"""Tests for notes.py — LaTeX generation."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def book_path(tmp_path):
    p = tmp_path / "test_book"
    p.mkdir()
    (p / "notes").mkdir()
    return p


SAMPLE_NOTES = {
    "book_title": "Test Book",
    "chapter_title": "Introduction",
    "summary": "An overview of the main concepts.",
    "concepts": [
        {
            "name": "Reliability",
            "definition": "The system works correctly even when faults occur.",
            "intuition": "A reliable system keeps working when things go wrong.",
            "examples": ["Netflix chaos engineering", "Disk failure handling"],
            "analogies": ["A car with a spare tire"],
            "formulas": [],
            "warnings": ["Reliability != availability"],
            "common_mistakes": ["Confusing fault with failure"],
            "connections": ["Relates to fault tolerance"],
        }
    ],
    "key_takeaways": ["Always design for faults, not just failures"],
    "personal_notes": "Remember: fault → partial failure → system failure",
}


class TestGenerateChapterNotes:
    def test_creates_tex_file(self, book_path):
        try:
            from jinja2 import Environment  # noqa: F401
        except ImportError:
            pytest.skip("Jinja2 not installed")

        from scripts.teach.notes import generate_chapter_notes
        result = generate_chapter_notes(book_path, 1, SAMPLE_NOTES)

        assert "tex_path" in result
        tex_path = Path(result["tex_path"])
        assert tex_path.exists()
        assert tex_path.suffix == ".tex"

    def test_tex_contains_concept_name(self, book_path):
        try:
            from jinja2 import Environment  # noqa: F401
        except ImportError:
            pytest.skip("Jinja2 not installed")

        from scripts.teach.notes import generate_chapter_notes
        result = generate_chapter_notes(book_path, 1, SAMPLE_NOTES)
        tex_content = Path(result["tex_path"]).read_text()
        assert "Reliability" in tex_content

    def test_tex_contains_definition(self, book_path):
        try:
            from jinja2 import Environment  # noqa: F401
        except ImportError:
            pytest.skip("Jinja2 not installed")

        from scripts.teach.notes import generate_chapter_notes
        result = generate_chapter_notes(book_path, 1, SAMPLE_NOTES)
        tex_content = Path(result["tex_path"]).read_text()
        assert "works correctly" in tex_content

    def test_chapter_num_in_filename(self, book_path):
        try:
            from jinja2 import Environment  # noqa: F401
        except ImportError:
            pytest.skip("Jinja2 not installed")

        from scripts.teach.notes import generate_chapter_notes
        result = generate_chapter_notes(book_path, 3, SAMPLE_NOTES)
        assert "chapter03" in result["tex_path"]

    def test_special_chars_escaped(self, book_path):
        try:
            from jinja2 import Environment  # noqa: F401
        except ImportError:
            pytest.skip("Jinja2 not installed")

        from scripts.teach.notes import generate_chapter_notes
        notes = {
            **SAMPLE_NOTES,
            "concepts": [{
                **SAMPLE_NOTES["concepts"][0],
                "definition": "Cost is $O(n)$ — 100% efficient & fast",
            }]
        }
        result = generate_chapter_notes(book_path, 1, notes)
        tex = Path(result["tex_path"]).read_text()
        # Should be escaped
        assert "\\$" in tex or "\\%" in tex or "\\&" in tex
