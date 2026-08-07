"""The Feedback agent: turns interview evidence into actionable, structured
feedback matching the Technical Specification schema:

    {summary: str, strengths: str[], gaps: str[], next: str[]}

Uses the LLM when available; otherwise a transparent heuristic synthesizer that
draws on per-topic scores, struggled/failed/skipped missions and the candidate's
own words.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List, Optional

from .prompts import feedback_system

SCORE_STRONG = 0.62
SCORE_WEAK = 0.38


def build_feedback(profile: Dict[str, Any],
                   answers: List[Dict[str, Any]],
                   transcript: Optional[List[Dict[str, str]]] = None,
                   llm: Any = None) -> Dict[str, List[Any]]:
    """Compute the final structured feedback."""
    scores_by_day: Dict[int, List[float]] = defaultdict(list)
    topic_by_day: Dict[int, str] = {}
    evidence_by_day: Dict[int, str] = {}
    for a in answers:
        day = a["day"]
        scores_by_day[day].append(a["score"])
        topic_by_day[day] = a["topic"]
        # keep the longest answer as evidence of what they could articulate
        if day not in evidence_by_day or len(a.get("answer", "")) > len(evidence_by_day[day]):
            evidence_by_day[day] = a.get("answer", "")[:220]

    avg = {d: sum(s) / len(s) for d, s in scores_by_day.items()}

    # ---- LLM path (with strict fallback on any failure) ---------------------
    if llm is not None and llm.enabled:
        llm_feedback = _llm_feedback(profile, avg, topic_by_day, transcript, llm)
        if llm_feedback is not None:
            return llm_feedback

    return _heuristic_feedback(profile, avg, topic_by_day, evidence_by_day, len(answers))


def _llm_feedback(profile: Dict[str, Any], avg: Dict[int, float],
                  topic_by_day: Dict[int, str], transcript: Optional[List[Dict[str, str]]],
                  llm: Any) -> Optional[Dict[str, Any]]:
    scores = {
        f"Day {d} — {topic_by_day.get(d, '')}": round(avg[d], 2)
        for d in sorted(avg)
    }
    messages = [
        {"role": "system", "content": feedback_system(profile, scores)},
    ]
    if transcript:
        for m in transcript[-20:]:
            messages.append({"role": m["role"], "content": m["text"]})
    messages.append({"role": "user",
                     "content": "Produce the final feedback JSON now."})
    data = llm.chat_json(messages, temperature=0.4)
    if not data:
        return None
    return _normalize(data)


def _normalize(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Validate/normalize LLM feedback into the spec schema; None if unusable."""
    summary = str(data.get("summary", "")).strip()
    strengths = [str(s).strip() for s in data.get("strengths", []) if str(s).strip()]
    gaps = [str(g).strip() for g in data.get("gaps", []) if str(g).strip()]
    nxt = [str(n).strip() for n in data.get("next", []) if str(n).strip()]
    if not summary or not strengths:
        return None
    return {
        "summary": summary,
        "strengths": strengths[:5],
        "gaps": gaps[:5],
        "next": nxt[:5],
    }


def _heuristic_feedback(profile: Dict[str, Any], avg: Dict[int, float],
                        topic_by_day: Dict[int, str],
                        evidence_by_day: Dict[int, str],
                        answer_count: int) -> Dict[str, List[Any]]:
    name = profile["member"].get("name", "You")

    strong = [d for d in avg if avg[d] >= SCORE_STRONG]
    weak = [d for d in avg if avg[d] < SCORE_WEAK]
    weak = [d for d in weak if d not in profile["failed_days"]]  # failed handled below

    strengths: List[str] = []
    for d in sorted(strong, key=lambda x: avg[x], reverse=True)[:3]:
        evidence = evidence_by_day.get(d, "").strip()
        quote = f" You explained '{evidence[:110].strip()}…'" if len(evidence) > 40 else ""
        strengths.append(f"Strong grasp of {topic_by_day.get(d, f'Day {d}')} — you spoke fluently about the core ideas.{quote}")

    gaps: List[str] = []
    for d in sorted(weak, key=lambda x: avg[x])[:3]:
        gaps.append(
            f"{topic_by_day.get(d, f'Day {d}')} came up and your answers stayed surface-level — "
            "revisit the core concepts and be ready to go two levels deeper."
        )
    for d in profile["failed_days"]:
        meta = profile["missions_by_day"][d]
        gaps.append(f"You attempted but did not pass Day {d} ({meta['title']}) — a focused review is worth your time.")
    for d in profile["skipped_days"][:1]:
        meta = profile["missions_by_day"][d]
        gaps.append(f"Day {d} ({meta['title']}) was skipped in the cohort — interviewers may still ask about it.")

    # Ensure we always have at least one gap insight
    if not gaps:
        weakest = min(avg, key=avg.get) if avg else None
        if weakest is not None:
            gaps.append(
                f"{topic_by_day.get(weakest, f'Day {weakest}')} was your least fluent topic — "
                "practice explaining it end-to-end out loud."
            )

    nxt: List[str] = []
    nxt.append(
        f"Re-explain your capstone architecture end-to-end out loud (or to a friend) and record it — "
        "fluency under pressure is what interviewers reward."
    )
    if weak or profile["failed_days"] or profile["skipped_days"]:
        target = profile["failed_days"] or weak or profile["skipped_days"]
        d = target[0]
        meta = profile["missions_by_day"].get(d, {"title": f"Day {d}"})
        nxt.append(
            f"Revisit Day {d}: {meta['title']} — redo the mission or study its objectives until you "
            "can teach it without notes."
        )
    nxt.append("Run a mock interview focused on RAG and agents — the two topics interviewers probe deepest on.")

    topic_count = len(avg)
    total_answers = answer_count
    strong_count = len(strong)
    gap_count = len(weak) + len(profile["failed_days"]) + len(profile["skipped_days"][:1])

    signals = profile.get("signals", {})
    commitment = ""
    if signals.get("commitDays"):
        commitment = f" Your consistency ({signals.get('commitDays')} active days) shows real commitment."
    summary = (
        f"Across {total_answers} answers covering {topic_count} curriculum topics, {name} showed "
        f"{'solid command in ' + str(strong_count) + ' areas' if strong_count else 'a developing foundation'}"
        f" and {gap_count} area{'s' if gap_count != 1 else ''} that need{'s' if gap_count == 1 else ''} reinforcement.{commitment} "
        "The strongest answers came when discussing systems you built yourself; the weakest "
        "when topics were rushed or skipped. With targeted review of the gaps below, you'll be interview-ready."
    )

    return {
        "summary": summary,
        "strengths": strengths or ["Good energy and a genuine, hands-on project you clearly cared about building."],
        "gaps": gaps,
        "next": nxt,
    }
