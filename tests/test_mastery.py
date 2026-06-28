"""Tests for mastery.py — SM-2 algorithm and mastery scoring."""

import json
import tempfile
from pathlib import Path
from datetime import date, timedelta

import pytest
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.teach.mastery import (
    composite_score,
    update_mastery,
    get_mastery,
    get_weak_topics,
    get_strong_topics,
    reset_concept_mastery,
    reset_all_mastery,
    SM2_MIN_EF,
    _sm2_quality,
    _next_interval,
)


@pytest.fixture
def book_path(tmp_path):
    p = tmp_path / "test_book"
    p.mkdir()
    (p / "mastery.json").write_text(json.dumps({"concept_mastery": {}}))
    return p


class TestCompositeScore:
    def test_all_perfect(self):
        assert composite_score(1.0, 1.0, 1.0, 1.0) == 1.0

    def test_all_zero(self):
        assert composite_score(0.0, 0.0, 0.0, 0.0) == 0.0

    def test_weights_sum(self):
        # Weights: u=0.30, r=0.30, a=0.25, c=0.15 → sum = 1.0
        result = composite_score(1.0, 0.0, 0.0, 0.0)
        assert abs(result - 0.30) < 0.001

    def test_partial_scores(self):
        result = composite_score(0.8, 0.7, 0.6, 0.5)
        expected = 0.30 * 0.8 + 0.30 * 0.7 + 0.25 * 0.6 + 0.15 * 0.5
        assert abs(result - expected) < 0.001


class TestSM2Quality:
    def test_zero_composite_gives_zero_quality(self):
        assert _sm2_quality(0.0) == 0

    def test_perfect_composite_gives_five(self):
        assert _sm2_quality(1.0) == 5

    def test_threshold_for_correct(self):
        # q >= 3 means success. 0.5 composite → q=3
        assert _sm2_quality(0.5) == 3

    def test_below_threshold(self):
        # 0.4 → q=2 → failure
        assert _sm2_quality(0.4) == 2


class TestSM2NextInterval:
    def test_first_correct_review(self):
        new_n, interval, ef = _next_interval(n=0, prev_interval=1, ef=2.5, q=4)
        assert new_n == 1
        assert interval == 1
        assert ef >= 2.5  # EF stays or grows (q=5 increases it, q=4 is neutral)

    def test_perfect_review_increases_ef(self):
        _, _, ef = _next_interval(n=2, prev_interval=6, ef=2.5, q=5)
        assert ef > 2.5

    def test_second_correct_review(self):
        new_n, interval, ef = _next_interval(n=1, prev_interval=1, ef=2.5, q=5)
        assert new_n == 2
        assert interval == 6

    def test_third_correct_review(self):
        new_n, interval, ef = _next_interval(n=2, prev_interval=6, ef=2.5, q=4)
        assert new_n == 3
        assert interval == round(6 * 2.5)

    def test_failed_review_resets(self):
        new_n, interval, ef = _next_interval(n=5, prev_interval=30, ef=2.5, q=1)
        assert new_n == 0
        assert interval == 1
        # EF doesn't decrease on failure in SM-2
        assert ef == 2.5

    def test_ef_never_below_minimum(self):
        # Repeatedly fail should not drop EF below SM2_MIN_EF
        ef = 2.5
        n, interval = 3, 10
        for _ in range(20):
            n, interval, ef = _next_interval(n, interval, ef, q=0)
        assert ef >= SM2_MIN_EF


class TestUpdateMastery:
    def test_creates_record(self, book_path):
        record = update_mastery(book_path, "replication", 0.8, 0.7, 0.6, 0.9)
        assert record["concept_id"] == "replication"
        assert record["understanding"] == 0.8
        assert record["recall"] == 0.7
        assert record["application"] == 0.6
        assert record["confidence"] == 0.9
        assert "composite" in record
        assert "next_review_date" in record
        assert "sm2_interval" in record

    def test_persists_to_json(self, book_path):
        update_mastery(book_path, "replication", 0.8, 0.7, 0.6, 0.9)
        store = get_mastery(book_path)
        assert "replication" in store["concept_mastery"]

    def test_review_count_increments(self, book_path):
        update_mastery(book_path, "replication", 0.8, 0.7, 0.6, 0.9)
        update_mastery(book_path, "replication", 0.9, 0.8, 0.7, 0.9)
        record = get_mastery(book_path)["concept_mastery"]["replication"]
        assert record["review_count"] == 2

    def test_next_review_date_is_future(self, book_path):
        record = update_mastery(book_path, "concept", 0.9, 0.9, 0.9, 0.9)
        next_date = date.fromisoformat(record["next_review_date"])
        assert next_date >= date.today()

    def test_low_mastery_schedules_next_day(self, book_path):
        # Low performance → interval = 1 day
        record = update_mastery(book_path, "concept", 0.1, 0.1, 0.1, 0.1)
        next_date = date.fromisoformat(record["next_review_date"])
        expected = date.today() + timedelta(days=1)
        assert next_date == expected


class TestWeakAndStrongTopics:
    def test_weak_topics(self, book_path):
        update_mastery(book_path, "weak_concept", 0.3, 0.3, 0.3, 0.3)
        update_mastery(book_path, "strong_concept", 0.9, 0.9, 0.9, 0.9)
        weak = get_weak_topics(book_path, threshold=0.6)
        weak_ids = [w["concept_id"] for w in weak]
        assert "weak_concept" in weak_ids
        assert "strong_concept" not in weak_ids

    def test_strong_topics(self, book_path):
        update_mastery(book_path, "weak_concept", 0.3, 0.3, 0.3, 0.3)
        update_mastery(book_path, "strong_concept", 0.9, 0.9, 0.9, 0.9)
        strong = get_strong_topics(book_path, threshold=0.8)
        strong_ids = [s["concept_id"] for s in strong]
        assert "strong_concept" in strong_ids
        assert "weak_concept" not in strong_ids


class TestReset:
    def test_reset_concept(self, book_path):
        update_mastery(book_path, "concept_a", 0.8, 0.8, 0.8, 0.8)
        update_mastery(book_path, "concept_b", 0.7, 0.7, 0.7, 0.7)
        reset_concept_mastery(book_path, "concept_a")
        store = get_mastery(book_path)
        assert "concept_a" not in store["concept_mastery"]
        assert "concept_b" in store["concept_mastery"]

    def test_reset_all(self, book_path):
        update_mastery(book_path, "concept_a", 0.8, 0.8, 0.8, 0.8)
        update_mastery(book_path, "concept_b", 0.7, 0.7, 0.7, 0.7)
        reset_all_mastery(book_path)
        store = get_mastery(book_path)
        assert store["concept_mastery"] == {}
