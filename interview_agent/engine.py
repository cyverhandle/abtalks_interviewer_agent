"""The Interviewer engine: a session state machine that runs a realistic,
adaptive technical interview and maintains full conversation context.

Flow:  opening -> question -> (followup)* -> question -> ... -> closing -> done

After every candidate answer the Assessor scores it against the day's core
concepts; shallow answers get a probing follow-up, strong answers get a
deep-dive follow-up, and everything in between moves on. The optional LLM
brain enriches phrasing and follow-up choice; the deterministic logic always
guarantees the interview progresses and completes.
"""
from __future__ import annotations

import re
import time
from typing import Any, Dict, List, Optional, Tuple

from .candidate_profile import build_profile
from .feedback import build_feedback
from .planner import build_plan
from .prompts import interviewer_system, transcript_messages

WEAK_SCORE = 0.30      # below this -> clarifying follow-up
STRONG_SCORE = 0.60    # above this -> deep-dive follow-up
MAX_FOLLOW_UPS = 1     # one follow-up per topic keeps the interview tight
ANSWER_DEPTH_WORDS = 160  # words considered "full enough" for depth scoring

_TRANSITIONS = [
    "Good. Next question — ",
    "Nice. Let's keep going — ",
    "Understood. Moving on — ",
    "That's helpful. Next up — ",
    "Okay, let's shift gears — ",
]

_UNSURE_PATTERNS = [
    "don't know", "do not know", "dont know", "not sure", "no idea",
    "i'm unsure", "im unsure", "not really sure", "i'd rather not",
    "never got", "didn't get", "didnt get", "wasn't able", "wasnt able",
    "skipped that", "pass on", "i'll pass", "ill pass", "draw a blank",
]


class InterviewSession:
    """Stateful interview for one candidate, keyed by sessionId."""

    def __init__(self, session_id: str, candidate: Dict[str, Any],
                 curriculum: Dict[str, Any], llm: Any = None):
        self.session_id = session_id
        self.candidate = candidate
        self.profile = build_profile(candidate, curriculum)
        self.plan = build_plan(self.profile)
        self.index = 0                 # current primary question index
        self.follow_ups = 0            # follow-ups asked on the current topic
        self.phase = "opening"         # opening | question | followup | closing | done
        self.transcript: List[Dict[str, str]] = []
        self.answers: List[Dict[str, Any]] = []  # per-topic assessment evidence
        self.feedback: Optional[Dict[str, Any]] = None
        self.llm = llm
        self.last_access = time.time()
        self._used_deep_dives: Dict[int, int] = {}
        self._llm_failures = 0        # circuit breaker: 2 failures -> go deterministic
        self._turn = 0

    # ------------------------------------------------------------- lifecycle

    def start(self) -> str:
        """Open the interview: welcome + first planned question."""
        self.phase = "question"
        if not self.plan:  # defensive: candidate with no record at all
            return ("Welcome! It looks like we don't have a record of your cohort "
                    "missions yet. Let's start simply: tell me about the AI project you "
                    "built most recently — what problem did it solve?")
        q = self.plan[0]
        reply = (
            f"Welcome{', ' + self.profile['member'].get('name', '') if self.profile['member'].get('name') else ''}! "
            "I'm your AI interviewer, and I've been following your work through the cohort. "
            "I'll ask about the systems you built — where you show real understanding we'll go deeper, "
            "and where things are fuzzy, that's exactly what we want to find and fix. "
            "There are no wrong answers here, so just explain things in your own words. Let's begin."
        )
        reply += f"\n\n{q['question']}"
        self._record("assistant", reply)
        self._turn += 1
        return reply

    def handle(self, message: str) -> Tuple[str, bool, Optional[Dict[str, Any]]]:
        """Process a candidate reply -> (interviewer reply, done, feedback)."""
        self.last_access = time.time()
        text = (message or "").strip()
        if not text:
            text = "(no response)"
        self._record("candidate", text)
        self._turn += 1

        if self.phase == "done":
            return "Interview completed.", True, self.feedback

        if self.phase == "closing":
            return self._finalize()

        # question | followup
        if self.llm is not None and self.llm.enabled and self._llm_failures < 2:
            result = self._llm_turn(text)
            if result is not None:
                self._llm_failures = 0
                return result
            self._llm_failures += 1  # circuit breaker -> deterministic from here on
        return self._deterministic_turn(text)

    def state(self) -> Dict[str, Any]:
        """Machine-readable progress (used by /state and the UI)."""
        asked = [
            {
                "n": i + 1,
                "day": a["day"],
                "topic": a["topic"],
                "score": round(a["score"], 2),
                "followUp": bool(a.get("follow_up")),
                "unsure": bool(a.get("unsure")),
            }
            for i, a in enumerate(self.answers)
        ]
        current = self.plan[self.index] if self.index < len(self.plan) else None
        return {
            "sessionId": self.session_id,
            "phase": self.phase,
            "questionNumber": min(self.index + 1, len(self.plan)),
            "totalQuestions": len(self.plan),
            "currentTopic": current["topic"] if current else None,
            "currentDay": current["day"] if current else None,
            "distinctDaysAsked": len({a["day"] for a in self.answers}),
            "topicsAsked": asked,
            "done": self.phase == "done",
        }

    # -------------------------------------------------------- deterministic

    def _deterministic_turn(self, text: str) -> Tuple[str, bool, Optional[Dict[str, Any]]]:
        q = self.plan[self.index]
        score = self._assess(text, q)
        self._record_answer(q, text, score)

        if self._is_unsure(text):
            self.answers[-1]["unsure"] = True
            # Be encouraging, take the miss, and move on — real interviewers do.
            self.follow_ups = 0
            self.index += 1
            return self._next_reply(
                "No problem — that's a tricky one, and honesty is a good sign. "
                "We'll flag it as something to revisit. "
            )

        if self.follow_ups < MAX_FOLLOW_UPS:
            if score < WEAK_SCORE:
                self.follow_ups += 1
                self.phase = "followup"
                return self._probe(q, text), False, None
            if score >= STRONG_SCORE:
                self.follow_ups += 1
                self.phase = "followup"
                return self._deep_dive(q), False, None

        self.follow_ups = 0
        self.index += 1
        return self._next_reply()

    def _next_reply(self, prelude: str = "") -> Tuple[str, bool, Optional[Dict[str, Any]]]:
        if self.index >= len(self.plan):
            self.phase = "closing"
            closing = (
                "That wraps up the technical portion — great work getting through it. "
                "Before we finish: is there anything you'd like to add about your capstone project, "
                "or any question you'd like to ask me?"
            )
            reply = prelude + closing
            self._record("assistant", reply)
            return reply, False, None

        self.phase = "question"
        q = self.plan[self.index]
        transition = _TRANSITIONS[self.index % len(_TRANSITIONS)]
        reply = prelude + transition + q["question"]
        self._record("assistant", reply)
        return reply, False, None

    def _probe(self, q: Dict[str, Any], text: str) -> str:
        """Ask a targeted follow-up about a concept the answer missed."""
        low = text.lower()
        missing = [c for c in q["concepts"] if c not in low]
        concept = missing[0] if missing else q["concepts"][0]
        probe = q.get("probes", {}).get(concept)
        if not probe:
            templates = [
                f"You didn't mention {concept} — how did that play into what you actually built?",
                f"Could you expand on the role of {concept} in your implementation? A rough mental model is fine.",
                f"Walk me through how you handled {concept} in your project — even a rough sketch helps.",
            ]
            probe = templates[len(self.answers) % len(templates)]
        reply = "That's a start — let me push on one point. " + probe
        self._record("assistant", reply)
        return reply

    def _deep_dive(self, q: Dict[str, Any]) -> str:
        """Ask a harder follow-up after a strong answer."""
        used = self._used_deep_dives.get(self.index, 0)
        dives = q.get("deep_dives") or []
        if used < len(dives):
            dive = dives[used]
        else:
            dive = (
                "Impressive — now tell me the tradeoff. What did you give up with that "
                "approach, and what would make you switch to something else?"
            )
        self._used_deep_dives[self.index] = used + 1
        reply = "Solid answer. One level deeper: " + dive
        self._record("assistant", reply)
        return reply

    def _finalize(self) -> Tuple[str, bool, Optional[Dict[str, Any]]]:
        self.phase = "done"
        self.feedback = build_feedback(self.profile, self.answers, self.transcript, self.llm)
        self._record("assistant", "Interview completed.")
        return "Interview completed.", True, self.feedback

    # ------------------------------------------------------------ assessment

    def _assess(self, text: str, q: Dict[str, Any]) -> float:
        """Score 0..1: concept coverage (60%) + answer depth (40%)."""
        low = text.lower()
        concepts = q.get("concepts") or []
        if not concepts:
            return 0.5  # unknown topic: flat neutral score
        hits = sum(1 for c in concepts if c in low)
        coverage = hits / len(concepts)
        words = len(re.findall(r"\b[\w-]+\b", text))
        depth = min(words / ANSWER_DEPTH_WORDS, 1.0)
        return 0.6 * coverage + 0.4 * depth

    def _is_unsure(self, text: str) -> bool:
        low = text.lower()
        return any(p in low for p in _UNSURE_PATTERNS)

    def _record_answer(self, q: Dict[str, Any], text: str, score: float) -> None:
        self.answers.append({
            "day": q["day"],
            "topic": q["topic"],
            "question": q["question"],
            "answer": text,
            "score": score,
            "follow_up": self.phase == "followup",
        })

    # ------------------------------------------------------------------- llm

    def _llm_turn(self, text: str) -> Optional[Tuple[str, bool, Optional[Dict[str, Any]]]]:
        """One LLM-powered turn; None -> caller falls back to deterministic."""
        q = self.plan[self.index]
        system = interviewer_system(self.profile, self.plan)
        messages = [{"role": "system", "content": system}]
        messages += transcript_messages(self.transcript)
        messages.append({
            "role": "user",
            "content": (
                f"The candidate just answered question {self.index + 1} of {len(self.plan)} "
                f"(Day {q['day']} — {q['topic']}). You may ask at most {MAX_FOLLOW_UPS} "
                f"follow-up{'s' if MAX_FOLLOW_UPS != 1 else ''} on this topic "
                f"(already asked: {self.follow_ups}). Respond with your JSON."
            ),
        })
        data = self.llm.chat_json(messages, temperature=0.7)
        if not data:
            return None

        reply = str(data.get("text", "")).strip()
        if not reply:
            return None
        action = data.get("action", "advance")
        assessment = data.get("assessment", "solid")
        score_map = {"weak": 0.25, "solid": 0.55, "strong": 0.85}
        score = score_map.get(assessment, 0.55)

        # Engine guardrails still apply: cap follow-ups, advance on unsure.
        if self.follow_ups >= MAX_FOLLOW_UPS:
            action = "advance"

        self._record_answer(q, text, score)
        if self._is_unsure(text):
            self.answers[-1]["unsure"] = True

        if self._is_unsure(text) or action == "advance":
            self.follow_ups = 0
            self.index += 1
            self._record("assistant", reply)
            return self._next_reply(reply + " " if reply else "")
        self.follow_ups += 1
        self.phase = "followup"
        self._record("assistant", reply)
        return reply, False, None

    # -------------------------------------------------------------- helpers

    def _record(self, role: str, text: str) -> None:
        self.transcript.append({"role": role, "text": text})
        # keep a bounded transcript in memory
        if len(self.transcript) > 120:
            self.transcript = self.transcript[-120:]
