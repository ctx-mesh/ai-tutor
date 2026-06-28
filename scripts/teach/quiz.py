"""Quiz state management — manages quizzes/ directory."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return default


def _write(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False))


def log_quiz(book_path: Path | str, quiz_data: dict) -> dict:
    """Save a completed quiz attempt."""
    book_path = Path(book_path)
    quiz_id = quiz_data.get("id") or str(uuid.uuid4())
    quiz_data["id"] = quiz_id
    quiz_data.setdefault("logged_at", _now())

    quiz_path = book_path / "quizzes" / f"{quiz_id}.json"
    _write(quiz_path, quiz_data)
    return quiz_data


def get_quiz_history(book_path: Path | str, concept_id: str | None = None) -> list[dict]:
    book_path = Path(book_path)
    quizzes_dir = book_path / "quizzes"
    if not quizzes_dir.exists():
        return []

    quizzes = []
    for f in sorted(quizzes_dir.glob("*.json")):
        q = _read(f, {})
        if q:
            quizzes.append(q)

    if concept_id:
        quizzes = [q for q in quizzes if q.get("concept_id") == concept_id]

    return sorted(quizzes, key=lambda q: q.get("logged_at", ""), reverse=True)


def get_quiz_stats(book_path: Path | str) -> dict:
    """Aggregate statistics across all quiz attempts."""
    quizzes = get_quiz_history(book_path)
    if not quizzes:
        return {
            "total_quizzes": 0,
            "total_questions": 0,
            "correct_answers": 0,
            "accuracy_pct": 0.0,
            "by_type": {},
        }

    total_q = sum(q.get("total_questions", 0) for q in quizzes)
    total_correct = sum(q.get("correct_answers", 0) for q in quizzes)

    by_type: dict[str, dict] = {}
    for q in quizzes:
        qtype = q.get("quiz_type", "unknown")
        if qtype not in by_type:
            by_type[qtype] = {"total": 0, "correct": 0}
        by_type[qtype]["total"] += q.get("total_questions", 0)
        by_type[qtype]["correct"] += q.get("correct_answers", 0)

    return {
        "total_quizzes": len(quizzes),
        "total_questions": total_q,
        "correct_answers": total_correct,
        "accuracy_pct": round(total_correct / max(1, total_q) * 100, 1),
        "by_type": by_type,
    }


def get_concept_performance(book_path: Path | str, concept_id: str) -> dict:
    """Get quiz performance for a specific concept."""
    quizzes = get_quiz_history(book_path, concept_id)
    total_q = sum(q.get("total_questions", 0) for q in quizzes)
    total_correct = sum(q.get("correct_answers", 0) for q in quizzes)
    return {
        "concept_id": concept_id,
        "quiz_attempts": len(quizzes),
        "total_questions": total_q,
        "correct_answers": total_correct,
        "accuracy_pct": round(total_correct / max(1, total_q) * 100, 1),
    }
