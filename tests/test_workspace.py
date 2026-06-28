"""Tests for workspace.py — initialization and listing."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.teach.workspace import init_book, list_books, get_book_path, book_slug


SAMPLE_TOC = [
    {"chapter_num": 1, "title": "Introduction", "start_page": 1, "end_page": 30, "page_count": 30, "sections": [], "has_figures": False},
    {"chapter_num": 2, "title": "Replication", "start_page": 31, "end_page": 80, "page_count": 50, "sections": [], "has_figures": True},
]

SAMPLE_META = {
    "title": "Test Book",
    "author": "Test Author",
    "total_pages": 80,
    "pdf_path": "/tmp/test_book.pdf",
}


@pytest.fixture
def workspace(tmp_path):
    """Use tmp_path as the CWD for workspace operations."""
    return tmp_path


class TestBookSlug:
    def test_simple(self):
        assert book_slug("MyBook.pdf") == "mybook"

    def test_spaces(self):
        assert "designing-data-intensive-applications" == book_slug("Designing Data-Intensive Applications.pdf")

    def test_special_chars(self):
        slug = book_slug("TCP/IP Illustrated: Vol. 1.pdf")
        assert "/" not in slug
        assert ":" not in slug


class TestInitBook:
    def test_creates_directory_structure(self, workspace):
        slug = init_book("/tmp/test.pdf", SAMPLE_TOC, SAMPLE_META, cwd=str(workspace))
        book_dir = workspace / ".teach" / "books" / slug
        assert book_dir.exists()
        assert (book_dir / "quizzes").exists()
        assert (book_dir / "notes").exists()
        assert (book_dir / "diagrams").exists()

    def test_creates_all_state_files(self, workspace):
        slug = init_book("/tmp/test.pdf", SAMPLE_TOC, SAMPLE_META, cwd=str(workspace))
        book_dir = workspace / ".teach" / "books" / slug
        required_files = [
            "metadata.json", "concepts.json", "dependency_graph.json",
            "progress.json", "mastery.json", "misconceptions.json",
            "sessions.json", "review_schedule.json", "preferences.json",
        ]
        for fname in required_files:
            assert (book_dir / fname).exists(), f"Missing: {fname}"

    def test_metadata_content(self, workspace):
        slug = init_book("/tmp/test.pdf", SAMPLE_TOC, SAMPLE_META, cwd=str(workspace))
        book_dir = workspace / ".teach" / "books" / slug
        meta = json.loads((book_dir / "metadata.json").read_text())
        assert meta["title"] == "Test Book"
        assert meta["author"] == "Test Author"
        assert meta["total_pages"] == 80
        assert len(meta["chapters"]) == 2

    def test_progress_initial_values(self, workspace):
        slug = init_book("/tmp/test.pdf", SAMPLE_TOC, SAMPLE_META, cwd=str(workspace))
        book_dir = workspace / ".teach" / "books" / slug
        prog = json.loads((book_dir / "progress.json").read_text())
        assert prog["current_chapter"] == 1
        assert prog["completed_chapters"] == []
        assert prog["book_completion_pct"] == 0.0
        assert prog["total_chapters"] == 2

    def test_idempotent(self, workspace):
        """Re-initializing should not overwrite existing state files."""
        slug = init_book("/tmp/test.pdf", SAMPLE_TOC, SAMPLE_META, cwd=str(workspace))
        book_dir = workspace / ".teach" / "books" / slug

        # Modify progress
        prog_path = book_dir / "progress.json"
        prog = json.loads(prog_path.read_text())
        prog["current_chapter"] = 3
        prog_path.write_text(json.dumps(prog))

        # Re-init
        init_book("/tmp/test.pdf", SAMPLE_TOC, SAMPLE_META, cwd=str(workspace))
        prog_after = json.loads(prog_path.read_text())
        # Progress should be preserved, not reset
        assert prog_after["current_chapter"] == 3


class TestListBooks:
    def test_empty_workspace(self, workspace):
        books = list_books(cwd=str(workspace))
        assert books == []

    def test_lists_initialized_books(self, workspace):
        init_book("/tmp/book1.pdf", SAMPLE_TOC, {**SAMPLE_META, "title": "Book One"}, cwd=str(workspace))
        init_book("/tmp/book2.pdf", SAMPLE_TOC, {**SAMPLE_META, "title": "Book Two"}, cwd=str(workspace))
        books = list_books(cwd=str(workspace))
        assert len(books) == 2
        titles = {b["title"] for b in books}
        assert "Book One" in titles
        assert "Book Two" in titles

    def test_book_has_progress_fields(self, workspace):
        init_book("/tmp/test.pdf", SAMPLE_TOC, SAMPLE_META, cwd=str(workspace))
        books = list_books(cwd=str(workspace))
        assert len(books) == 1
        book = books[0]
        assert "completion_pct" in book
        assert "current_chapter" in book
        assert "total_chapters" in book
        assert book["total_chapters"] == 2
