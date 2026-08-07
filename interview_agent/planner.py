"""The Planner agent: personalizes the interview plan for a candidate.

Guarantees (enforced for every candidate):
  * at least MIN_QUESTIONS primary questions (default 10, spec minimum is 8)
  * covering at least 4 distinct curriculum days
  * topics weighted by curriculum importance + the candidate's own signals
    (struggled days get probed harder, failed/skipped days surface as gaps)
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Set

from .candidate_profile import (
    STATUS_FAILED,
    STATUS_SKIPPED,
    STATUS_STRUGGLED,
    build_profile,
)
from .data_loader import days_by_number
from .questions import available_variants, get_day_meta

MIN_QUESTIONS = 10
MIN_DISTINCT_DAYS = 4

# Curriculum centrality — days that form the spine of the cohort get asked first.
IMPORTANCE = {
    31: 6,   # capstone / system design (opener)
    7: 5, 10: 5, 11: 5, 12: 5, 21: 5, 23: 5,
    8: 4, 13: 4, 16: 4, 22: 4, 28: 4,
    3: 3, 20: 3, 24: 3, 25: 3, 27: 3,
    1: 2, 2: 2, 4: 2, 5: 2, 6: 2, 9: 2, 14: 2, 15: 2,
    17: 2, 18: 2, 19: 2, 26: 2, 29: 2, 30: 2,
}

STATUS_BONUS = {
    STATUS_STRUGGLED: 3,   # passed but fought for it -> verify real understanding
    STATUS_FAILED: 4,      # attempted, didn't pass -> probe the fundamentals
    "solid": 1,
    STATUS_SKIPPED: -4,    # skipped topics are only asked when we need coverage
}


def _day_weight(profile: Dict[str, Any], day: int) -> int:
    base = IMPORTANCE.get(day, 2)
    mission = profile["missions_by_day"].get(day)
    if mission is None:
        return base - 3  # never touched in the cohort
    return base + STATUS_BONUS.get(mission["status"], 0)


def build_plan(profile: Dict[str, Any], min_questions: int = MIN_QUESTIONS) -> List[Dict[str, Any]]:
    """Return an ordered list of planned questions for the candidate.

    Each plan item: {day, topic, question, concepts, deep_dives, probes, objectives}
    """
    by_day: Dict[int, Dict[str, Any]] = profile["missions_by_day"]
    curriculum_days = days_by_number()

    # 1. Choose the pool of days to interview on: everything the candidate worked
    #    on (passed or failed). Skipped days join only if we need more coverage.
    main_days: List[int] = [d for d, m in by_day.items() if m["status"] != STATUS_SKIPPED]
    probe_days: List[int] = [d for d, m in by_day.items() if m["status"] == STATUS_SKIPPED]
    if not main_days and not probe_days:
        # Candidate has no mission record at all — fall back to the core spine
        # of the curriculum so the interview still runs.
        main_days = [d for d, _ in sorted(IMPORTANCE.items(), key=lambda kv: kv[1], reverse=True)][:10]
        probe_days = []
    elif len(main_days) < MIN_DISTINCT_DAYS:
        main_days = main_days + probe_days
        probe_days = []

    main_days.sort(key=lambda d: _day_weight(profile, d), reverse=True)

    # 2. Round-robin across the weighted list so coverage is spread over many
    #    days (a candidate with few completed days gets several questions each).
    used: Dict[int, int] = {d: 0 for d in main_days}
    pool: List[int] = list(main_days)
    slots: List[int] = []
    guard = 0
    idx = 0
    while len(slots) < min_questions and pool and guard < 10_000:
        guard += 1
        day = pool[idx % len(pool)]
        if used[day] < len(available_variants(day, curriculum_days.get(day))):
            slots.append(day)
            used[day] += 1
        idx += 1

    # 3. Build plan items, rotating through question variants per day.
    variant_idx: Dict[int, int] = {}
    plan: List[Dict[str, Any]] = []
    for day in slots:
        variants = available_variants(day, curriculum_days.get(day))
        vi = variant_idx.get(day, 0)
        if vi >= len(variants):
            continue
        question = variants[vi]
        variant_idx[day] = vi + 1
        meta = get_day_meta(day)
        plan.append({
            "day": day,
            "topic": meta["topic"],
            "question": question,
            "concepts": meta["concepts"],
            "deep_dives": meta["deep_dives"],
            "probes": meta.get("probes", {}),
            "objectives": (curriculum_days.get(day) or {}).get("objectives", []),
        })

    # 4. Narrative ordering: open with the capstone/project story if available,
    #    then walk the remaining topics in curriculum-day order (a real arc:
    #    embeddings -> retrieval -> RAG -> prompting -> agents/MCP -> production).
    opener = next((q for q in plan if q["day"] == 31), plan[0])
    opener_idx = plan.index(opener)
    rest = plan[:opener_idx] + plan[opener_idx + 1:]
    ordered = [opener] + sorted(rest, key=lambda q: q["day"])

    return ordered


def plan_stats(plan: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compliance stats for the plan (used by tests and the /state endpoint)."""
    days = sorted({q["day"] for q in plan})
    return {
        "total_questions": len(plan),
        "distinct_days": len(days),
        "days": days,
        "meets_min_questions": len(plan) >= MIN_QUESTIONS,
        "meets_min_days": len(days) >= MIN_DISTINCT_DAYS,
    }


def verify_plan_for_all_candidates(curriculum: Dict[str, Any],
                                   candidates: List[Dict[str, Any]]) -> List[str]:
    """Check the minimum requirements for every candidate; return violations."""
    violations: List[str] = []
    for candidate in candidates:
        profile = build_profile(candidate, curriculum)
        plan = build_plan(profile)
        stats = plan_stats(plan)
        cid = candidate["member"]["id"]
        if not stats["meets_min_questions"]:
            violations.append(f"{cid}: only {stats['total_questions']} questions")
        if not stats["meets_min_days"]:
            violations.append(f"{cid}: only {stats['distinct_days']} distinct days")
    return violations
