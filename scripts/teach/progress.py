"""Progress tracking — manages progress.json."""

from __future__ import annotations

import json
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


def get_progress(book_path: Path | str) -> dict:
    return _read(Path(book_path) / "progress.json", {})


def update_current_position(book_path: Path | str, chapter_num: int, concept_id: str | None = None) -> dict:
    book_path = Path(book_path)
    p = _read(book_path / "progress.json", {})
    p["current_chapter"] = chapter_num
    p["current_concept_id"] = concept_id
    p["last_updated"] = _now()
    _write(book_path / "progress.json", p)
    return p


def mark_concept_taught(book_path: Path | str, chapter_num: int, concept_id: str) -> dict:
    book_path = Path(book_path)
    p = _read(book_path / "progress.json", {})

    taught = p.get("taught_concepts", [])
    if concept_id not in taught:
        taught.append(concept_id)
    p["taught_concepts"] = taught
    p["current_concept_id"] = concept_id
    p["last_updated"] = _now()

    # Update chapter completion (rough estimate: concepts taught / total)
    _recalculate_completion(p, chapter_num)

    _write(book_path / "progress.json", p)
    return p


def mark_chapter_complete(book_path: Path | str, chapter_num: int) -> dict:
    book_path = Path(book_path)
    p = _read(book_path / "progress.json", {})

    completed = p.get("completed_chapters", [])
    if chapter_num not in completed:
        completed.append(chapter_num)
    p["completed_chapters"] = sorted(completed)

    ch_completion = p.get("chapter_completion", {})
    ch_completion[str(chapter_num)] = 100.0
    p["chapter_completion"] = ch_completion

    total = p.get("total_chapters", 1)
    p["book_completion_pct"] = round(len(completed) / max(1, total) * 100, 1)
    p["last_updated"] = _now()

    # Advance to next chapter
    p["current_chapter"] = chapter_num + 1
    p["current_concept_id"] = None

    _write(book_path / "progress.json", p)
    return p


def _recalculate_completion(p: dict, chapter_num: int) -> None:
    """Approximate chapter completion by ratio of taught concepts in chapter.
    Full accuracy requires concept count from concepts.json; this is an estimate."""
    completed_chapters = p.get("completed_chapters", [])
    total = max(1, p.get("total_chapters", 1))
    base_pct = len(completed_chapters) / total * 100
    p["book_completion_pct"] = round(base_pct, 1)


def reset_chapter(book_path: Path | str, chapter_num: int, chapter_concept_ids: list[str]) -> dict:
    book_path = Path(book_path)
    p = _read(book_path / "progress.json", {})

    p["completed_chapters"] = [c for c in p.get("completed_chapters", []) if c != chapter_num]
    p["taught_concepts"] = [c for c in p.get("taught_concepts", []) if c not in chapter_concept_ids]
    p["chapter_completion"][str(chapter_num)] = 0.0

    total = max(1, p.get("total_chapters", 1))
    p["book_completion_pct"] = round(len(p["completed_chapters"]) / total * 100, 1)
    p["current_chapter"] = chapter_num
    p["current_concept_id"] = None
    p["last_updated"] = _now()

    _write(book_path / "progress.json", p)
    return p


def reset_all(book_path: Path | str, total_chapters: int) -> dict:
    book_path = Path(book_path)
    p = {
        "current_chapter": 1,
        "current_concept_id": None,
        "completed_chapters": [],
        "taught_concepts": [],
        "book_completion_pct": 0.0,
        "chapter_completion": {str(i + 1): 0.0 for i in range(total_chapters)},
        "total_chapters": total_chapters,
        "started_at": _now(),
        "last_updated": _now(),
    }
    _write(book_path / "progress.json", p)
    return p
