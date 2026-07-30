"""Tests for subscriptions block."""
from __future__ import annotations
import pytest
@pytest.fixture(autouse=True)
def reset():
    from blocks.subscriptions.backend import service as s
    s._plans.clear(); s._subscriptions.clear(); s._next_plan = 1

class TestSubscriptions:
    def test_create_plan(self):
        from blocks.subscriptions.backend import service as s
        s.create_plan("Basic", 9, 90, ["feature1"], 1)
        s.create_plan("Pro", 29, 290, ["feature1", "feature2"], 2, popular=True)
        plans = s.list_plans()
        assert len(plans) == 2
        assert plans[1]["popular"] is True

    def test_assign_and_check(self):
        from blocks.subscriptions.backend import service as s
        s.create_plan("Basic", 9, 90, ["email", "storage"])
        s.assign_plan(1, 1)
        assert s.has_feature(1, "email") is True
        assert s.has_feature(1, "premium") is False

    def test_cancel(self):
        from blocks.subscriptions.backend import service as s
        s.create_plan("Basic", 9, 90, ["email"])
        s.assign_plan(1, 1)
        assert s.cancel(1) is True
        assert s.get_user_subscription(1)["status"] == "cancelled"

    def test_change_plan(self):
        from blocks.subscriptions.backend import service as s
        s.create_plan("Basic", 9, 90, ["email"])
        s.create_plan("Pro", 29, 290, ["email", "api"])
        s.assign_plan(1, 1)
        s.change_plan(1, 2)
        assert s.get_user_subscription(1)["plan_name"] == "Pro"
