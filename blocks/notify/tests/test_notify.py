"""Tests for notifications block."""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def reset():
    from blocks.notify.backend import service as s
    s._notifications.clear()
    s._next_id = 1


class TestNotifications:
    def test_send_and_list(self):
        from blocks.notify.backend import service as s
        s.send(1, "Test", "Hello world")
        s.send(1, "Test 2", "Second")
        assert len(s.list_for_user(1)) == 2
        assert len(s.list_for_user(2)) == 0

    def test_unread_count(self):
        from blocks.notify.backend import service as s
        s.send(1, "T", "M")
        s.send(1, "T2", "M2")
        assert s.get_unread_count(1) == 2

    def test_mark_read(self):
        from blocks.notify.backend import service as s
        s.send(1, "T", "M")
        assert s.mark_read(1, 1) is True
        assert s.get_unread_count(1) == 0

    def test_mark_all_read(self):
        from blocks.notify.backend import service as s
        s.send(1, "T", "M")
        s.send(1, "T2", "M2")
        assert s.mark_all_read(1) == 2
        assert s.get_unread_count(1) == 0

    def test_channels(self):
        from blocks.notify.backend import service as s
        n = s.send(1, "T", "M", channel="email")
        assert n["channel"] == "email"
        n2 = s.send(1, "T", "M", channel="invalid")
        assert n2["channel"] == "in_app"
