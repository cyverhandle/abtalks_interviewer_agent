"""Builds a rich understanding of each candidate from their learning signals."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .data_loader import day_title

STATUS_STRONG = "solid"      # passed, few attempts
STATUS_STRUGGLED = "struggled"  # passed but needed 3+ attempts
STATUS_FAILED = "failed"     # attempted but not passed
STATUS_SKIPPED = "skipped"   # never attempted


def build_profile(candidate: Dict[str, Any], curriculum: Dict[str, Any]) -> Dict[str, Any]:
    """Classify every curriculum day touched by the candidate.

    Returns a profile with:
      * member        — identity / role / experience
      * signals       — commitDays, missionsCompleted, missionsFirstTry
      * missions_by_day — day -> {status, passed, attempts, title}
      * completed_days / struggled_days / failed_days / skipped_days
      * summary       — a one-paragraph human-readable digest for prompts
    """
    member = candidate.get("member", {})
    missions = candidate.get("missions", [])
    signals = candidate.get("signals", {})

    missions_by_day: Dict[int, Dict[str, Any]] = {}
    for m in missions:
        day = m.get("day")
        if not day:
            continue
        skipped = bool(m.get("skipped"))
        passed = m.get("passed")
        attempts = int(m.get("attempts") or 0)
        if skipped:
            status = STATUS_SKIPPED
        elif passed is False:
            status = STATUS_FAILED
        elif attempts >= 3:
            status = STATUS_STRUGGLED
        else:
            status = STATUS_STRONG
        missions_by_day[day] = {
            "status": status,
            "passed": passed,
            "attempts": attempts,
            "title": m.get("title") or day_title(curriculum, day),
        }

    completed = sorted(d for d, s in missions_by_day.items() if s["status"] in (STATUS_STRONG, STATUS_STRUGGLED))
    struggled = sorted(d for d, s in missions_by_day.items() if s["status"] == STATUS_STRUGGLED)
    failed = sorted(d for d, s in missions_by_day.items() if s["status"] == STATUS_FAILED)
    skipped = sorted(d for d, s in missions_by_day.items() if s["status"] == STATUS_SKIPPED)

    profile: Dict[str, Any] = {
        "member": member,
        "signals": signals,
        "missions_by_day": missions_by_day,
        "completed_days": completed,
        "struggled_days": struggled,
        "failed_days": failed,
        "skipped_days": skipped,
        "summary": _summarize(member, missions_by_day, signals, curriculum),
    }
    return profile


def _summarize(member: Dict[str, Any], missions_by_day: Dict[int, Dict[str, Any]],
               signals: Dict[str, Any], curriculum: Dict[str, Any]) -> str:
    name = member.get("name", "the candidate")
    role = member.get("jobRole", "unknown role")
    exp = member.get("yearsExperience", 0)

    bits = [f"{name} is a {role} with {exp} years of experience."]
    if signals:
        bits.append(
            f"Learning signals: {signals.get('missionsCompleted', '?')} missions completed, "
            f"{signals.get('missionsFirstTry', '?')} passed on the first try across "
            f"{signals.get('commitDays', '?')} active days."
        )

    def fmt(days: List[int], label: str) -> Optional[str]:
        if not days:
            return None
        titles = ", ".join(f"Day {d} ({missions_by_day[d]['title']})" for d in days[:4])
        more = "..." if len(days) > 4 else ""
        return f"{label}: {titles}{more}"

    for line in (
        fmt([d for d in missions_by_day if missions_by_day[d]['status'] == 'struggled'],
            "Completed but required repeated attempts"),
        fmt([d for d in missions_by_day if missions_by_day[d]['status'] == 'failed'],
            "Attempted but not passed"),
        fmt([d for d in missions_by_day if missions_by_day[d]['status'] == 'skipped'],
            "Skipped"),
    ):
        if line:
            bits.append(line)

    return " ".join(bits)
