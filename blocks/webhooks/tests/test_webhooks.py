"""Tests for webhooks block."""
from __future__ import annotations
import pytest
@pytest.fixture(autouse=True)
def reset():
    from blocks.webhooks.backend import service as s
    s._received.clear(); s._next_id = 1

class TestWebhooks:
    def test_receive(self):
        from blocks.webhooks.backend import service as s
        event = s.receive("stripe", {"type": "payment_intent.succeeded"})
        assert event["source"] == "stripe"
        assert event["verified"] is False

    def test_get_log(self):
        from blocks.webhooks.backend import service as s
        s.receive("discord", {"content": "hello"})
        s.receive("email", {"to": "test@test.com"})
        log = s.get_log()
        assert len(log) == 2
        discord = s.get_log("discord")
        assert len(discord) == 1

    def test_replay(self):
        from blocks.webhooks.backend import service as s
        s.receive("test", {"msg": "hello"})
        replayed = s.replay(1)
        assert replayed is not None
        assert replayed["replay_count"] == 1
