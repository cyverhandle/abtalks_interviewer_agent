# AI Interview Agent

A personalized, multi-turn technical interviewer for graduates of the 31-day AI
Cohort. It reads each candidate's **actual journey** — completed missions, how
many attempts each took, what was skipped, and their learning signals — and runs
a realistic interview that digs into the systems they built, adapts as they
answer, keeps full conversation context, and ends with structured, actionable
feedback.

```
Planner ──▶ Interviewer ──▶ Assessor ──▶ (follow-ups / advance) ──▶ Feedback
  │            │               │                                      │
  │   candidate profile +     scores every answer                {summary,
  │   curriculum signals      against core concepts              strengths,
  └──────────▶ 10+ questions across 4+ days                      gaps, next}
```

## Why it feels like a real interview (not a questionnaire)

* **Personalized plan.** The planner weights curriculum importance *and* the
  candidate's own signals: topics they struggled through (3+ attempts) get
  probed harder, failed missions surface as gaps, and the interview opens with
  their capstone story.
* **Adaptive follow-ups.** Every answer is scored against the day's core
  concepts. Shallow answers get a targeted probe about the missing concept;
  strong answers get a one-level-deeper "tradeoffs" question. "I'm not sure"
  is handled gracefully and the interview keeps moving.
* **Full context.** The entire transcript lives in the session and is fed back
  into every decision — no question is asked twice, and follow-ups reference
  what the candidate actually said.
* **Structured feedback.** At the end you get `summary`, `strengths`, `gaps`
  and `next` — each a concise, actionable list tied to real interview evidence.

## Quick start

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt   # Windows
# .venv/bin/python -m pip install -r requirements.txt      # macOS / Linux

.venv/Scripts/python -m uvicorn main:app --port 8000
```

Open http://127.0.0.1:8000 for the chat UI (pick a candidate, interview them,
get feedback). Or drive the API directly:

```bash
# 1. start an interview
curl -X POST http://127.0.0.1:8000/api/interview \
  -H "Content-Type: application/json" \
  -d '{"sessionId":"abc-123","candidate":{...candidate.json}}'

# 2. keep talking
curl -X POST http://127.0.0.1:8000/api/interview \
  -H "Content-Type: application/json" \
  -d '{"sessionId":"abc-123","message":"We used sentence transformers and Chroma..."}'

# 3. when done: true comes back, the response includes feedback
```

## API contract (per Technical Specification)

| Request body | Meaning | Response |
|---|---|---|
| `{"sessionId", "candidate"}` | Start a new interview | `{"reply", "done": false}` |
| `{"sessionId", "message"}` | Candidate's latest answer | `{"reply", "done": false}` |
| final turn | Interview complete | `{"reply": "Interview completed.", "done": true, "feedback": {...}}` |

`feedback` always matches:

```json
{ "summary": "string", "strengths": ["string"], "gaps": ["string"], "next": ["string"] }
```

Helpful extras (not required, but verified by the included tests):
`topic`, `questionNumber`, `totalQuestions` on every response;
`GET /api/interview/{sid}/state` exposes machine-readable progress and
compliance; `GET /api/candidates` lists the roster.

**Guaranteed minimums for every candidate:** ≥ 8 questions across ≥ 4 distinct
curriculum days (the default plan is 10 questions; the round-robin planner
spreads coverage, so even a candidate with 5 completed days gets 10 questions
across all of them). The test suite asserts this for all 20 profiles.

## Optional LLM brain (recommended for the live demo)

The deterministic engine fully satisfies the spec and works offline. To make
the interview *conversational*, point the agent at any OpenAI-compatible
endpoint:

```bash
export AI_INTERVIEW_LLM_BASE_URL="http://localhost:11434/v1"   # Ollama (as used in the cohort)
export AI_INTERVIEW_LLM_MODEL="qwen2.5-coder:7b"               # or gpt-4o-mini / llama-3.3-70b-versatile
# export AI_INTERVIEW_LLM_API_KEY="sk-..."                     # needed for OpenAI/Groq
```

With the LLM enabled, the interviewer decides phrasing, follow-up choice and
assessments itself (JSON-constrained, schema-validated); the engine still
enforces the plan, the one-follow-up-per-topic cap, and the completion flow.
If the endpoint is unreachable or returns garbage, every call falls back to the
deterministic engine — the interview never breaks. A mock-server test in
`test_api.py` proves both paths.

## Project layout

```
main.py                    FastAPI service — the /api/interview endpoint
interview_agent/
  data_loader.py           curriculum + candidates loading
  candidate_profile.py     learning-signal analysis (strong/struggled/failed/skipped)
  questions.py             curated question bank for all 31 days (+ scoring concepts)
  planner.py               personalized plan: >= 8 questions, >= 4 days, narrative arc
  engine.py                session state machine: follow-ups, context, closing
  feedback.py              structured feedback (LLM or heuristic synthesizer)
  llm.py                   OpenAI-compatible client (Ollama/OpenAI/Groq) + fallback
  prompts.py               system prompts for LLM mode
static/index.html          the chat UI
test_api.py                59 checks: planner compliance, full API contract, LLM path
```

## Tests

```bash
.venv/Scripts/python -m pip install -r requirements.txt
.venv/Scripts/python test_api.py
```

Covers: planner minimums for all 20 candidates, a complete simulated interview
over HTTP (start → 10+ turns → done → feedback schema), error handling
(unknown session 404 / bad body 422 / duplicate start 409), the LLM path via a
mock OpenAI-compatible server, and graceful fallback when the LLM is dead.

## Possible extensions

* **Vector-memory recall** — embed past interview answers (ChromaDB) so
  feedback and follow-ups draw on every previous session.
* **LangGraph orchestration** — swap the state machine for an explicit graph
  (planner → interviewer → assessor → feedback) for richer control flow.
* **Difficulty routing** — tune question depth from the candidate's
  `yearsExperience` and role.
* **Streaming** — stream interviewer tokens with SSE for a more natural feel.
