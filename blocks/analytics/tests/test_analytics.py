"""Tests for analytics block."""
from __future__ import annotations
import pytest
@pytest.fixture(autouse=True)
def reset():
    from blocks.analytics.backend import service as s
    s._pageviews.clear(); s._events.clear()

class TestAnalytics:
    def test_track_pageview(self):
        from blocks.analytics.backend import service as s
        s.track_pageview("/home", "https://google.com", "test-agent", "1.2.3.4", "sess1")
        d = s.get_dashboard(24)
        assert d["total_pageviews"] == 1
        assert d["unique_sessions"] == 1

    def test_track_event(self):
        from blocks.analytics.backend import service as s
        s.track_event("purchase", "commerce", "item-1", 29.99, "sess1")
        d = s.get_dashboard(24)
        assert d["total_events"] == 1
