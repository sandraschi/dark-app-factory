"""Tests for reviews block."""
from __future__ import annotations
import pytest
@pytest.fixture(autouse=True)
def reset():
    from blocks.reviews.backend import service as s
    s._reviews.clear(); s._next_id = 1

class TestReviews:
    def test_submit_and_list(self):
        from blocks.reviews.backend import service as s
        s.submit("Alice", "a@b.com", 5, "Great!", "Love it", True)
        s.submit("Bob", "b@b.com", 3, "OK", "Meh", False)
        assert len(s.list_approved()) == 1
        assert len(s.list_pending()) == 1

    def test_approve(self):
        from blocks.reviews.backend import service as s
        s.submit("A", "a@b.com", 4, "T", "C")
        assert s.approve(1) is True
        assert len(s.list_approved()) == 1

    def test_stats(self):
        from blocks.reviews.backend import service as s
        s.submit("A", "a@b.com", 5, "T", "C", True)
        s.submit("B", "b@b.com", 3, "T", "C", True)
        stats = s.get_stats()
        assert stats["total"] == 2
        assert stats["average"] == 4.0
