"""Subscription plans service — tiers, feature flags, usage tracking."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("dark_factory")

_plans: list[dict] = []
_subscriptions: dict[int, dict] = {}  # user_id -> {plan_id, start, status}
_next_plan = 1


def create_plan(name: str, price_monthly: float, price_yearly: float, features: list[str], tier: int = 1, popular: bool = False) -> dict:
    global _next_plan
    p = {"id": _next_plan, "name": name, "price_monthly": price_monthly, "price_yearly": price_yearly, "features": features, "tier": tier, "popular": popular}
    _plans.append(p)
    _next_plan += 1
    return p


def list_plans() -> list[dict]:
    return sorted(_plans, key=lambda x: x["tier"])


def get_plan(plan_id: int) -> dict | None:
    return next((p for p in _plans if p["id"] == plan_id), None)


def assign_plan(user_id: int, plan_id: int) -> dict:
    plan = get_plan(plan_id)
    if not plan:
        return {"error": "Plan not found"}
    _subscriptions[user_id] = {"plan_id": plan_id, "plan_name": plan["name"], "tier": plan["tier"], "started": datetime.now(timezone.utc).isoformat(), "status": "active"}
    return {"subscription": _subscriptions[user_id]}


def get_user_subscription(user_id: int) -> dict | None:
    return _subscriptions.get(user_id)


def has_feature(user_id: int, feature: str) -> bool:
    sub = _subscriptions.get(user_id)
    if not sub:
        return False
    plan = get_plan(sub["plan_id"])
    if not plan:
        return False
    return feature in plan.get("features", [])


def cancel(user_id: int) -> bool:
    sub = _subscriptions.get(user_id)
    if sub:
        sub["status"] = "cancelled"
        return True
    return False


def change_plan(user_id: int, new_plan_id: int) -> dict:
    sub = _subscriptions.get(user_id)
    if not sub:
        return assign_plan(user_id, new_plan_id)
    plan = get_plan(new_plan_id)
    if not plan:
        return {"error": "Plan not found"}
    sub.update({"plan_id": new_plan_id, "plan_name": plan["name"], "tier": plan["tier"]})
    return {"subscription": sub}
