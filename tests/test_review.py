"""Tests for review.py — due review queries."""

import json
import sys
from datetime import date, timedelta
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.teach.mastery import update_mastery
from scripts.teach.review import get_due_reviews, get_upcoming_reviews


@pytest.fixture
def book_path(tmp_path):
    p = tmp_path / "test_book"
    p.mkdir()
    (p / "mastery.json").write_text(json.dumps({"concept_mastery": {}}))
    (p / "concepts.json").write_text(json.dumps({"concepts": {}}))
    return p


def _force_review_date(book_path: Path, concept_id: str, review_date: str) -> None:
    """Directly set next_review_date for testing."""
    path = book_path / "mastery.json"
    store = json.loads(path.read_text())
    if concept_id in store["concept_mastery"]:
        store["concept_mastery"][concept_id]["next_review_date"] = review_date
        path.write_text(json.dumps(store, indent=2))


class TestGetDueReviews:
    def test_no_reviews_when_empty(self, book_path):
        due = get_due_reviews(book_path)
        assert due == []

    def test_overdue_concept_appears(self, book_path):
        update_mastery(book_path, "concept_a", 0.7, 0.7, 0.7, 0.7)
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        _force_review_date(book_path, "concept_a", yesterday)

        due = get_due_reviews(book_path)
        assert len(due) == 1
        assert due[0]["concept_id"] == "concept_a"

    def test_future_concept_not_due(self, book_path):
        update_mastery(book_path, "concept_b", 0.9, 0.9, 0.9, 0.9)
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        _force_review_date(book_path, "concept_b", tomorrow)

        due = get_due_reviews(book_path)
        assert not any(d["concept_id"] == "concept_b" for d in due)

    def test_today_due_appears(self, book_path):
        update_mastery(book_path, "concept_c", 0.5, 0.5, 0.5, 0.5)
        today = date.today().isoformat()
        _force_review_date(book_path, "concept_c", today)

        due = get_due_reviews(book_path)
        assert any(d["concept_id"] == "concept_c" for d in due)

    def test_sorted_most_overdue_first(self, book_path):
        for cid in ["c1", "c2", "c3"]:
            update_mastery(book_path, cid, 0.5, 0.5, 0.5, 0.5)

        _force_review_date(book_path, "c1", (date.today() - timedelta(days=5)).isoformat())
        _force_review_date(book_path, "c2", (date.today() - timedelta(days=1)).isoformat())
        _force_review_date(book_path, "c3", (date.today() - timedelta(days=10)).isoformat())

        due = get_due_reviews(book_path)
        due_ids = [d["concept_id"] for d in due]
        assert due_ids.index("c3") < due_ids.index("c1") < due_ids.index("c2")


class TestGetUpcomingReviews:
    def test_returns_concepts_in_window(self, book_path):
        update_mastery(book_path, "soon", 0.8, 0.8, 0.8, 0.8)
        in_3_days = (date.today() + timedelta(days=3)).isoformat()
        _force_review_date(book_path, "soon", in_3_days)

        upcoming = get_upcoming_reviews(book_path, days_ahead=7)
        assert any(u["concept_id"] == "soon" for u in upcoming)

    def test_excludes_concepts_beyond_window(self, book_path):
        update_mastery(book_path, "far", 0.8, 0.8, 0.8, 0.8)
        in_30_days = (date.today() + timedelta(days=30)).isoformat()
        _force_review_date(book_path, "far", in_30_days)

        upcoming = get_upcoming_reviews(book_path, days_ahead=7)
        assert not any(u["concept_id"] == "far" for u in upcoming)
