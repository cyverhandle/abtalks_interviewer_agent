"""AI Interview Agent — a personalized, multi-turn technical interviewer.

Components (agent roles):
  * Planner   — turns a candidate profile + curriculum into a personalized
                question plan (>= 8 questions, >= 4 curriculum days).
  * Interviewer — a state machine that runs the live conversation, adapts with
                follow-up questions and keeps full transcript context.
  * Assessor  — scores every answer against the day's core concepts.
  * Feedback  — produces structured {summary, strengths, gaps, next} output.
  * LLM       — optional OpenAI-compatible brain (Ollama / OpenAI / Groq) that
                enriches the interview; the deterministic engine is the fallback
                so the agent always works, even fully offline.
"""

from .engine import InterviewSession
from .data_loader import load_curriculum, load_candidates
from .llm import llm_from_env

__all__ = ["InterviewSession", "load_curriculum", "load_candidates", "llm_from_env"]
__version__ = "1.0.0"
