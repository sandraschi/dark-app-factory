"""Notification service — in-app notifications, channel routing."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("dark_factory")

_notifications: list[dict] = []
_next_id = 1

CHANNELS = ["in_app", "email", "push", "sms"]


def send(to_user_id: int, title: str, message: str, channel: str = "in_app", priority: str = "normal", link: str = "") -> dict:
    global _next_id
    n = {
        "id": _next_id, "to_user_id": to_user_id, "title": title, "message": message,
        "channel": channel if channel in CHANNELS else "in_app",
        "priority": priority, "link": link, "read": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    _notifications.append(n)
    _next_id += 1
    logger.info("Notification sent to user %d: %s (%s)", to_user_id, title, channel)
    return n


def list_for_user(user_id: int, unread_only: bool = False) -> list[dict]:
    results = [n for n in _notifications if n["to_user_id"] == user_id]
    if unread_only:
        results = [n for n in results if not n["read"]]
    return list(reversed(results))


def mark_read(notif_id: int, user_id: int) -> bool:
    n = next((n for n in _notifications if n["id"] == notif_id and n["to_user_id"] == user_id), None)
    if n:
        n["read"] = True
        return True
    return False


def mark_all_read(user_id: int) -> int:
    count = 0
    for n in _notifications:
        if n["to_user_id"] == user_id and not n["read"]:
            n["read"] = True
            count += 1
    return count


def get_unread_count(user_id: int) -> int:
    return sum(1 for n in _notifications if n["to_user_id"] == user_id and not n["read"])
