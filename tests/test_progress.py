"""Tests for progress.py — progress tracking."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.teach.progress import (
    get_progress,
    update_current_position,
    mark_concept_taught,
    mark_chapter_complete,
    reset_chapter,
    reset_all,
)


@pytest.fixture
def book_path(tmp_path):
    p = tmp_path / "test_book"
    p.mkdir()
    initial = {
        "current_chapter": 1,
        "current_concept_id": None,
        "completed_chapters": [],
        "taught_concepts": [],
        "book_completion_pct": 0.0,
        "chapter_completion": {"1": 0.0, "2": 0.0, "3": 0.0},
        "total_chapters": 3,
        "started_at": "2026-01-01T00:00:00Z",
        "last_updated": "2026-01-01T00:00:00Z",
    }
    (p / "progress.json").write_text(json.dumps(initial))
    return p


class TestUpdateCurrentPosition:
    def test_updates_chapter(self, book_path):
        prog = update_current_position(book_path, 2, "replication")
        assert prog["current_chapter"] == 2
        assert prog["current_concept_id"] == "replication"

    def test_persisted(self, book_path):
        update_current_position(book_path, 3, "consensus")
        prog = get_progress(book_path)
        assert prog["current_chapter"] == 3


class TestMarkConceptTaught:
    def test_adds_to_taught_list(self, book_path):
        prog = mark_concept_taught(book_path, 1, "reliability")
        assert "reliability" in prog["taught_concepts"]

    def test_idempotent(self, book_path):
        mark_concept_taught(book_path, 1, "reliability")
        mark_concept_taught(book_path, 1, "reliability")
        prog = get_progress(book_path)
        assert prog["taught_concepts"].count("reliability") == 1


class TestMarkChapterComplete:
    def test_adds_to_completed(self, book_path):
        prog = mark_chapter_complete(book_path, 1)
        assert 1 in prog["completed_chapters"]

    def test_advances_to_next_chapter(self, book_path):
        prog = mark_chapter_complete(book_path, 1)
        assert prog["current_chapter"] == 2

    def test_completion_pct_updates(self, book_path):
        mark_chapter_complete(book_path, 1)
        prog = mark_chapter_complete(book_path, 2)
        assert prog["book_completion_pct"] == pytest.approx(2 / 3 * 100, rel=0.01)

    def test_chapter_completion_set_to_100(self, book_path):
        prog = mark_chapter_complete(book_path, 1)
        assert prog["chapter_completion"]["1"] == 100.0


class TestResetChapter:
    def test_removes_from_completed(self, book_path):
        mark_chapter_complete(book_path, 1)
        mark_chapter_complete(book_path, 2)
        prog = reset_chapter(book_path, 1, ["concept_a", "concept_b"])
        assert 1 not in prog["completed_chapters"]
        assert 2 in prog["completed_chapters"]

    def test_removes_chapter_concepts_from_taught(self, book_path):
        mark_concept_taught(book_path, 1, "concept_a")
        mark_concept_taught(book_path, 1, "concept_b")
        mark_concept_taught(book_path, 2, "concept_c")
        prog = reset_chapter(book_path, 1, ["concept_a", "concept_b"])
        assert "concept_a" not in prog["taught_concepts"]
        assert "concept_b" not in prog["taught_concepts"]
        assert "concept_c" in prog["taught_concepts"]


class TestResetAll:
    def test_clears_all_state(self, book_path):
        mark_chapter_complete(book_path, 1)
        mark_concept_taught(book_path, 1, "something")
        prog = reset_all(book_path, total_chapters=3)
        assert prog["completed_chapters"] == []
        assert prog["taught_concepts"] == []
        assert prog["book_completion_pct"] == 0.0
        assert prog["current_chapter"] == 1
