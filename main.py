"""AI Interview Agent — HTTP service.

Required endpoint (per Technical Specification):
    POST /api/interview
        {"sessionId": "...", "candidate": {...}}   -> start interview
        {"sessionId": "...", "message": "..."}      -> continue interview
    Response: {"reply": str, "done": bool, "feedback": {...} | None}

Extras (not required, but handy):
    GET  /api/candidates                 — candidate list for the demo UI
    GET  /api/interview/{sid}/state      — machine-readable progress/compliance
    GET  /                               — the chat UI

Run:  uvicorn main:app --port 8000
Optional LLM brain: set AI_INTERVIEW_LLM_BASE_URL / _API_KEY / _MODEL.
"""
from __future__ import annotations

import os
import time
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from interview_agent.data_loader import load_candidates, load_curriculum
from interview_agent.engine import InterviewSession
from interview_agent.llm import llm_from_env

app = FastAPI(
    title="AI Interview Agent",
    description="Personalized, multi-turn technical interviews grounded in each "
                "candidate's journey through the 31-day AI Cohort.",
    version="1.0.0",
)

CURRICULUM = load_curriculum()
CANDIDATES = load_candidates()
LLM = llm_from_env()

SESSIONS: Dict[str, InterviewSession] = {}
SESSION_TTL_SECONDS = 12 * 60 * 60  # sessions expire after 12h of inactivity


# ---------------------------------------------------------------- schemas

class InterviewRequest(BaseModel):
    sessionId: str = Field(..., min_length=1, description="Client-supplied session id")
    candidate: Optional[Dict[str, Any]] = Field(
        None, description="Candidate profile — present on the first request only")
    message: Optional[str] = Field(None, description="Candidate's latest reply")


class FeedbackOut(BaseModel):
    summary: str
    strengths: List[str]
    gaps: List[str]
    next: List[str]


class InterviewResponse(BaseModel):
    reply: str
    done: bool = False
    feedback: Optional[FeedbackOut] = None
    # Optional extras so clients can render progress without extra calls:
    topic: Optional[str] = None
    questionNumber: Optional[int] = None
    totalQuestions: Optional[int] = None


# ---------------------------------------------------------------- helpers

def _cleanup_sessions() -> None:
    now = time.time()
    stale = [sid for sid, s in SESSIONS.items() if now - s.last_access > SESSION_TTL_SECONDS]
    for sid in stale:
        SESSIONS.pop(sid, None)


# ---------------------------------------------------------------- endpoints

@app.post("/api/interview", response_model=InterviewResponse,
         response_model_exclude_none=True)
def interview(req: InterviewRequest) -> InterviewResponse:
    """The single required endpoint: start an interview or continue one.

    Responses always carry the documented contract fields ({reply, done}, plus
    {feedback} on completion). While the interview is in progress we also add
    light extras ({topic, questionNumber, totalQuestions}) so clients can render
    progress without extra calls; on the final turn the body matches the spec
    example exactly.
    """
    _cleanup_sessions()
    sid = req.sessionId

    # --- start a new interview -------------------------------------------
    if req.candidate is not None:
        if sid in SESSIONS:
            raise HTTPException(
                status_code=409,
                detail=f"Session '{sid}' already exists — send {{sessionId, message}} to continue it.",
            )
        session = InterviewSession(sid, req.candidate, CURRICULUM, LLM)
        SESSIONS[sid] = session
        reply = session.start()
        return InterviewResponse(
            reply=reply, done=False, topic=session.plan[0]["topic"] if session.plan else None,
            questionNumber=1, totalQuestions=len(session.plan),
        )

    # --- continue an interview -------------------------------------------
    if req.message is None:
        raise HTTPException(
            status_code=422,
            detail="Provide 'candidate' to start an interview, or 'message' to continue one.",
        )
    session = SESSIONS.get(sid)
    if session is None:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown sessionId '{sid}'. Start a new interview by POSTing a candidate.",
        )

    session.last_access = time.time()
    reply, done, feedback = session.handle(req.message)
    if done:
        return InterviewResponse(
            reply=reply, done=True, feedback=FeedbackOut(**feedback) if feedback else None
        )
    state = session.state()
    return InterviewResponse(
        reply=reply,
        done=False,
        topic=state.get("currentTopic"),
        questionNumber=state.get("questionNumber"),
        totalQuestions=state.get("totalQuestions"),
    )


@app.get("/api/candidates")
def list_candidates() -> List[Dict[str, Any]]:
    """Lightweight candidate roster for the demo UI."""
    return [
        {
            "id": c["member"]["id"],
            "name": c["member"]["name"],
            "jobRole": c["member"]["jobRole"],
            "yearsExperience": c["member"]["yearsExperience"],
            "status": c["member"]["status"],
            "missionsCompleted": c["signals"].get("missionsCompleted"),
        }
        for c in CANDIDATES
    ]


@app.get("/api/candidates-full")
def full_candidates() -> List[Dict[str, Any]]:
    """The complete candidate objects (members, missions, signals) — used by the
    demo UI to start a real interview for the selected profile."""
    return CANDIDATES


@app.get("/api/interview/{session_id}/state")
def interview_state(session_id: str) -> Dict[str, Any]:
    """Progress + compliance snapshot for a live session."""
    session = SESSIONS.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail=f"Unknown sessionId '{session_id}'")
    return session.state()


# ---------------------------------------------------------------- static UI

_STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
app.mount("/static", StaticFiles(directory=_STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(os.path.join(_STATIC_DIR, "index.html"))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
