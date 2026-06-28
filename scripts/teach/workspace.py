"""Workspace management — creates and reads the .teach/ directory in the user's CWD."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from slugify import slugify


TEACH_DIR = ".teach"
BOOKS_DIR = "books"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_workspace_root(cwd: str | None = None) -> Path:
    return Path(cwd or os.getcwd()) / TEACH_DIR


def get_book_path(slug: str, cwd: str | None = None) -> Path:
    return get_workspace_root(cwd) / BOOKS_DIR / slug


def book_slug(pdf_path: str) -> str:
    name = Path(pdf_path).stem
    return slugify(name, separator="-")


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False))


def _read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return default


def init_book(pdf_path: str, toc: list[dict], metadata: dict, cwd: str | None = None) -> str:
    """
    Initialize workspace for a PDF. Creates directory structure and all empty state files.
    Returns the book slug.
    """
    slug = book_slug(pdf_path)
    book_path = get_book_path(slug, cwd)

    book_path.mkdir(parents=True, exist_ok=True)
    (book_path / "quizzes").mkdir(exist_ok=True)
    (book_path / "notes").mkdir(exist_ok=True)
    (book_path / "diagrams").mkdir(exist_ok=True)
    (book_path / "exports").mkdir(exist_ok=True)

    abs_pdf = str(Path(pdf_path).resolve())

    _write_json(book_path / "metadata.json", {
        "book_id": slug,
        "title": metadata.get("title") or Path(pdf_path).stem,
        "author": metadata.get("author", ""),
        "pdf_path": abs_pdf,
        "total_pages": metadata.get("total_pages", 0),
        "initialized_at": _now(),
        "last_accessed": _now(),
        "chapters": toc,
    })

    if not (book_path / "concepts.json").exists():
        _write_json(book_path / "concepts.json", {"concepts": {}})

    if not (book_path / "dependency_graph.json").exists():
        _write_json(book_path / "dependency_graph.json", {"nodes": {}, "edges": []})

    if not (book_path / "progress.json").exists():
        total_chapters = len(toc)
        _write_json(book_path / "progress.json", {
            "current_chapter": 1,
            "current_concept_id": None,
            "completed_chapters": [],
            "taught_concepts": [],
            "book_completion_pct": 0.0,
            "chapter_completion": {str(i + 1): 0.0 for i in range(total_chapters)},
            "total_chapters": total_chapters,
            "started_at": _now(),
            "last_updated": _now(),
        })

    if not (book_path / "mastery.json").exists():
        _write_json(book_path / "mastery.json", {"concept_mastery": {}})

    if not (book_path / "misconceptions.json").exists():
        _write_json(book_path / "misconceptions.json", {"misconceptions": []})

    if not (book_path / "sessions.json").exists():
        _write_json(book_path / "sessions.json", {"sessions": []})

    if not (book_path / "review_schedule.json").exists():
        _write_json(book_path / "review_schedule.json", {"schedule": {}})

    if not (book_path / "preferences.json").exists():
        _write_json(book_path / "preferences.json", {
            "learning_mode": "normal",
            "preferred_analogy_types": [],
            "preferred_explanation_style": "intuition-first",
            "known_topics": [],
            "background_notes": "",
            "session_pace": "medium",
        })

    # Touch last_accessed
    meta = _read_json(book_path / "metadata.json", {})
    meta["last_accessed"] = _now()
    _write_json(book_path / "metadata.json", meta)

    return slug


def list_books(cwd: str | None = None) -> list[dict]:
    """Return all books in the workspace with high-level progress."""
    ws = get_workspace_root(cwd) / BOOKS_DIR
    if not ws.exists():
        return []

    books = []
    for book_dir in sorted(ws.iterdir()):
        if not book_dir.is_dir():
            continue
        meta = _read_json(book_dir / "metadata.json", {})
        progress = _read_json(book_dir / "progress.json", {})
        if not meta:
            continue
        books.append({
            "slug": book_dir.name,
            "title": meta.get("title", book_dir.name),
            "author": meta.get("author", ""),
            "pdf_path": meta.get("pdf_path", ""),
            "completion_pct": progress.get("book_completion_pct", 0.0),
            "current_chapter": progress.get("current_chapter", 1),
            "total_chapters": progress.get("total_chapters", 0),
            "last_accessed": meta.get("last_accessed", ""),
        })
    return books


def touch_last_accessed(slug: str, cwd: str | None = None) -> None:
    book_path = get_book_path(slug, cwd)
    meta = _read_json(book_path / "metadata.json", {})
    if meta:
        meta["last_accessed"] = _now()
        _write_json(book_path / "metadata.json", meta)
