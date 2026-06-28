"""Concept CRUD — manages concepts.json and dependency_graph.json."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _read(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return default


def _write(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False))


def save_concept(book_path: Path | str, concept: dict) -> dict:
    """Insert or update a concept in concepts.json."""
    book_path = Path(book_path)
    path = book_path / "concepts.json"
    store = _read(path, {"concepts": {}})
    concept_id = concept["id"]
    store["concepts"][concept_id] = concept
    _write(path, store)
    return concept


def get_concept(book_path: Path | str, concept_id: str) -> dict | None:
    book_path = Path(book_path)
    store = _read(book_path / "concepts.json", {"concepts": {}})
    return store["concepts"].get(concept_id)


def get_all_concepts(book_path: Path | str) -> dict[str, dict]:
    book_path = Path(book_path)
    store = _read(book_path / "concepts.json", {"concepts": {}})
    return store["concepts"]


def get_chapter_concepts(book_path: Path | str, chapter_num: int) -> list[dict]:
    concepts = get_all_concepts(book_path)
    return [c for c in concepts.values() if c.get("chapter") == chapter_num]


def save_dependency_graph(book_path: Path | str, graph: dict) -> None:
    book_path = Path(book_path)
    _write(book_path / "dependency_graph.json", graph)


def get_dependency_graph(book_path: Path | str) -> dict:
    book_path = Path(book_path)
    return _read(book_path / "dependency_graph.json", {"nodes": {}, "edges": []})


def get_prerequisites(book_path: Path | str, concept_id: str) -> list[str]:
    """Return list of concept IDs that must be taught before this one."""
    concept = get_concept(book_path, concept_id)
    if not concept:
        return []
    return concept.get("prerequisites", [])


def get_untaught_prerequisites(book_path: Path | str, concept_id: str, taught_ids: list[str]) -> list[str]:
    prereqs = get_prerequisites(book_path, concept_id)
    return [p for p in prereqs if p not in taught_ids]
