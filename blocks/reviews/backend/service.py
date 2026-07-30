"""Reviews service — submission, moderation, stats."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("dark_factory")

_reviews: list[dict] = []
_next_id = 1


def submit(name: str, email: str, rating: int, title: str, content: str, auto_approve: bool = False) -> dict:
    global _next_id
    r = {"id": _next_id, "name": name, "email": email, "rating": max(1, min(5, rating)), "title": title, "content": content,
         "approved": auto_approve, "created_at": datetime.now(timezone.utc).isoformat()}
    _reviews.append(r)
    _next_id += 1
    return r


def list_approved() -> list[dict]:
    return [r for r in reversed(_reviews) if r["approved"]]


def list_pending() -> list[dict]:
    return [r for r in reversed(_reviews) if not r["approved"]]


def approve(review_id: int) -> bool:
    r = next((x for x in _reviews if x["id"] == review_id), None)
    if r: r["approved"] = True; return True
    return False


def delete(review_id: int) -> bool:
    global _reviews
    before = len(_reviews)
    _reviews = [r for r in _reviews if r["id"] != review_id]
    return len(_reviews) < before


def get_stats() -> dict:
    approved = [r for r in _reviews if r["approved"]]
    count = len(approved)
    avg = sum(r["rating"] for r in approved) / count if count else 0
    dist = {i: sum(1 for r in approved if r["rating"] == i) for i in range(1, 6)}
    return {"total": count, "average": round(avg, 1), "distribution": dist, "pending": sum(1 for r in _reviews if not r["approved"])}
