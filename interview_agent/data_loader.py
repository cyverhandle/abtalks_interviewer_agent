"""Loads the curriculum and candidate data, with caching."""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PKG_DIR = os.path.dirname(os.path.abspath(__file__))

_curriculum_cache: Optional[Dict[str, Any]] = None
_candidates_cache: Optional[List[Dict[str, Any]]] = None


def _load_json(name: str) -> Any:
    """Find ``name`` next to the project root first, then next to this package."""
    for root in (_PROJECT_ROOT, _PKG_DIR):
        path = os.path.join(root, name)
        if os.path.exists(path):
            with open(path, encoding="utf-8") as fh:
                return json.load(fh)
    raise FileNotFoundError(
        f"Could not locate '{name}' — place it next to main.py or inside interview_agent/."
    )


def load_curriculum() -> Dict[str, Any]:
    """Curriculum document: modules, daily topics, objectives and tools."""
    global _curriculum_cache
    if _curriculum_cache is None:
        _curriculum_cache = _load_json("curriculum.json")
    return _curriculum_cache


def load_candidates() -> List[Dict[str, Any]]:
    """Candidate profiles: members, missions, attempts, skips and signals."""
    global _candidates_cache
    if _candidates_cache is None:
        _candidates_cache = _load_json("candidates.json")["candidates"]
    return _candidates_cache


def days_by_number(curriculum: Optional[Dict[str, Any]] = None) -> Dict[int, Dict[str, Any]]:
    """Map day number -> day object (title, type, tools, objectives)."""
    curriculum = curriculum or load_curriculum()
    return {d["day"]: d for d in curriculum.get("days", [])}


def day_title(curriculum: Dict[str, Any], day: int) -> str:
    """Human readable title for a curriculum day, or a fallback string."""
    day_obj = days_by_number(curriculum).get(day)
    return day_obj["title"] if day_obj else f"Day {day}"
