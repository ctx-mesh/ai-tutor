"""Mastery tracking and SM-2 spaced repetition algorithm."""

from __future__ import annotations

import json
import math
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any


# Composite mastery weights
WEIGHTS = {"understanding": 0.30, "recall": 0.30, "application": 0.25, "confidence": 0.15}

# SM-2 defaults
SM2_DEFAULT_EF = 2.5
SM2_MIN_EF = 1.3


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _today() -> str:
    return date.today().isoformat()


def _read(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return default


def _write(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False))


def composite_score(u: float, r: float, a: float, c: float) -> float:
    """Compute weighted composite mastery 0–1."""
    return round(
        WEIGHTS["understanding"] * u
        + WEIGHTS["recall"] * r
        + WEIGHTS["application"] * a
        + WEIGHTS["confidence"] * c,
        3,
    )


def _sm2_quality(composite: float) -> int:
    """Map 0–1 composite to SM-2 quality 0–5."""
    return min(5, max(0, math.floor(composite * 6)))


def _next_interval(n: int, prev_interval: float, ef: float, q: int) -> tuple[int, float, float]:
    """
    SM-2 step.
    Returns (new_n, new_interval, new_ef).
    n: repetition count before this review
    prev_interval: previous interval in days
    ef: ease factor
    q: quality 0-5
    """
    if q >= 3:
        if n == 0:
            interval = 1
        elif n == 1:
            interval = 6
        else:
            interval = round(prev_interval * ef)
        new_n = n + 1
        new_ef = max(SM2_MIN_EF, ef + 0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
    else:
        interval = 1
        new_n = 0
        new_ef = ef  # EF does not decrease on failure in SM-2

    return new_n, float(interval), round(new_ef, 3)


def get_mastery(book_path: Path | str) -> dict:
    return _read(Path(book_path) / "mastery.json", {"concept_mastery": {}})


def update_mastery(
    book_path: Path | str,
    concept_id: str,
    understanding: float,
    recall: float,
    application: float,
    confidence: float,
) -> dict:
    """Update mastery scores for a concept and recalculate SM-2 schedule."""
    book_path = Path(book_path)
    store = _read(book_path / "mastery.json", {"concept_mastery": {}})
    existing = store["concept_mastery"].get(concept_id, {})

    comp = composite_score(understanding, recall, application, confidence)
    q = _sm2_quality(comp)

    n = existing.get("sm2_n", 0)
    prev_interval = existing.get("sm2_interval", 1.0)
    ef = existing.get("sm2_ef", SM2_DEFAULT_EF)

    new_n, new_interval, new_ef = _next_interval(n, prev_interval, ef, q)
    next_review = (date.today() + timedelta(days=int(new_interval))).isoformat()

    record = {
        "concept_id": concept_id,
        "understanding": round(understanding, 3),
        "recall": round(recall, 3),
        "application": round(application, 3),
        "confidence": round(confidence, 3),
        "composite": comp,
        "sm2_n": new_n,
        "sm2_interval": new_interval,
        "sm2_ef": new_ef,
        "sm2_quality": q,
        "next_review_date": next_review,
        "last_reviewed": _today(),
        "review_count": existing.get("review_count", 0) + 1,
        "first_taught": existing.get("first_taught", _today()),
    }

    store["concept_mastery"][concept_id] = record
    _write(book_path / "mastery.json", store)
    return record


def get_concept_mastery(book_path: Path | str, concept_id: str) -> dict | None:
    store = get_mastery(book_path)
    return store["concept_mastery"].get(concept_id)


def get_weak_topics(book_path: Path | str, threshold: float = 0.6) -> list[dict]:
    store = get_mastery(book_path)
    return [
        {"concept_id": cid, **m}
        for cid, m in store["concept_mastery"].items()
        if m.get("composite", 1.0) < threshold
    ]


def get_strong_topics(book_path: Path | str, threshold: float = 0.8) -> list[dict]:
    store = get_mastery(book_path)
    return [
        {"concept_id": cid, **m}
        for cid, m in store["concept_mastery"].items()
        if m.get("composite", 0.0) >= threshold
    ]


def reset_concept_mastery(book_path: Path | str, concept_id: str) -> None:
    book_path = Path(book_path)
    store = _read(book_path / "mastery.json", {"concept_mastery": {}})
    store["concept_mastery"].pop(concept_id, None)
    _write(book_path / "mastery.json", store)


def reset_all_mastery(book_path: Path | str) -> None:
    _write(Path(book_path) / "mastery.json", {"concept_mastery": {}})
