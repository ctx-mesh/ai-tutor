"""Misconception tracking — manages misconceptions.json."""

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


def log_misconception(book_path: Path | str, concept_id: str, text: str) -> dict:
    book_path = Path(book_path)
    store = _read(book_path / "misconceptions.json", {"misconceptions": []})

    record = {
        "id": str(uuid.uuid4()),
        "concept_id": concept_id,
        "text": text,
        "logged_at": _now(),
        "resolved": False,
        "resolved_at": None,
    }
    store["misconceptions"].append(record)
    _write(book_path / "misconceptions.json", store)
    return record


def get_misconceptions(book_path: Path | str, concept_id: str | None = None) -> list[dict]:
    store = _read(Path(book_path) / "misconceptions.json", {"misconceptions": []})
    items = store.get("misconceptions", [])
    if concept_id:
        items = [m for m in items if m["concept_id"] == concept_id]
    return items


def get_unresolved_misconceptions(book_path: Path | str) -> list[dict]:
    return [m for m in get_misconceptions(book_path) if not m.get("resolved")]


def resolve_misconception(book_path: Path | str, misconception_id: str) -> dict | None:
    book_path = Path(book_path)
    store = _read(book_path / "misconceptions.json", {"misconceptions": []})
    for m in store["misconceptions"]:
        if m["id"] == misconception_id:
            m["resolved"] = True
            m["resolved_at"] = _now()
            _write(book_path / "misconceptions.json", store)
            return m
    return None
