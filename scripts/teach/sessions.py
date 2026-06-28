"""Session logging — manages sessions.json."""

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


def start_session(book_path: Path | str, chapter_num: int) -> dict:
    """Create a new session record and return it (including its id)."""
    book_path = Path(book_path)
    store = _read(book_path / "sessions.json", {"sessions": []})

    session = {
        "id": str(uuid.uuid4()),
        "started_at": _now(),
        "ended_at": None,
        "chapter_num": chapter_num,
        "concepts_taught": [],
        "quizzes_taken": 0,
        "correct_answers": 0,
        "duration_minutes": None,
        "notes": "",
    }
    store["sessions"].append(session)
    _write(book_path / "sessions.json", store)
    return session


def end_session(book_path: Path | str, session_id: str, summary: dict) -> dict | None:
    """Mark a session as complete and update its summary fields."""
    book_path = Path(book_path)
    store = _read(book_path / "sessions.json", {"sessions": []})

    for s in store["sessions"]:
        if s["id"] == session_id:
            s["ended_at"] = _now()
            if s.get("started_at"):
                try:
                    start = datetime.fromisoformat(s["started_at"])
                    end = datetime.fromisoformat(s["ended_at"])
                    s["duration_minutes"] = round((end - start).total_seconds() / 60, 1)
                except (ValueError, TypeError):
                    pass
            s.update(summary)
            _write(book_path / "sessions.json", store)
            return s

    return None


def log_session(book_path: Path | str, session_data: dict) -> dict:
    """Log a complete session record (used when session is supplied externally)."""
    book_path = Path(book_path)
    store = _read(book_path / "sessions.json", {"sessions": []})

    if "id" not in session_data:
        session_data["id"] = str(uuid.uuid4())
    if "logged_at" not in session_data:
        session_data["logged_at"] = _now()

    store["sessions"].append(session_data)
    _write(book_path / "sessions.json", store)
    return session_data


def get_recent_sessions(book_path: Path | str, limit: int = 5) -> list[dict]:
    store = _read(Path(book_path) / "sessions.json", {"sessions": []})
    sessions = store.get("sessions", [])
    return sessions[-limit:][::-1]  # most recent first


def get_total_study_time_minutes(book_path: Path | str) -> float:
    store = _read(Path(book_path) / "sessions.json", {"sessions": []})
    return sum(s.get("duration_minutes") or 0 for s in store.get("sessions", []))
