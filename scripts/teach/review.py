"""Review scheduling — wraps mastery SM-2 data for due-review queries."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

from scripts.teach.mastery import get_mastery
from scripts.teach.concepts import get_concept


def _read(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return default


def get_due_reviews(book_path: Path | str) -> list[dict]:
    """Return concepts whose SM-2 next_review_date is today or earlier."""
    book_path = Path(book_path)
    store = get_mastery(book_path)
    today = date.today().isoformat()

    due = []
    for cid, m in store["concept_mastery"].items():
        next_review = m.get("next_review_date")
        if next_review and next_review <= today:
            concept = get_concept(book_path, cid) or {}
            due.append({
                "concept_id": cid,
                "concept_name": concept.get("name", cid),
                "chapter": concept.get("chapter"),
                "next_review_date": next_review,
                "composite": m.get("composite", 0.0),
                "sm2_interval": m.get("sm2_interval", 1),
                "review_count": m.get("review_count", 0),
            })

    # Sort: most overdue first, then lowest mastery
    due.sort(key=lambda x: (x["next_review_date"], x["composite"]))
    return due


def get_upcoming_reviews(book_path: Path | str, days_ahead: int = 7) -> list[dict]:
    """Return concepts due in the next N days (useful for planning)."""
    book_path = Path(book_path)
    store = get_mastery(book_path)
    today = date.today()

    upcoming = []
    for cid, m in store["concept_mastery"].items():
        next_review = m.get("next_review_date")
        if not next_review:
            continue
        try:
            review_date = date.fromisoformat(next_review)
        except ValueError:
            continue
        delta = (review_date - today).days
        if 0 <= delta <= days_ahead:
            concept = get_concept(book_path, cid) or {}
            upcoming.append({
                "concept_id": cid,
                "concept_name": concept.get("name", cid),
                "chapter": concept.get("chapter"),
                "next_review_date": next_review,
                "days_until_due": delta,
                "composite": m.get("composite", 0.0),
            })

    upcoming.sort(key=lambda x: x["days_until_due"])
    return upcoming
