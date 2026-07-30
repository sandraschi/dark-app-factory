"""Webhook receiver service — ingestion, verification, replay."""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("dark_factory")

_received: list[dict] = []
_next_id = 1


def _verify_signature(payload: bytes, signature: str, secret: str) -> bool:
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def receive(source: str, payload: dict, headers: dict | None = None, signature: str = "") -> dict:
    global _next_id
    secret = os.environ.get("WEBHOOK_SECRET", "")
    verified = False
    if secret and signature:
        raw = json.dumps(payload).encode()
        verified = _verify_signature(raw, signature, secret)
    event = {
        "id": _next_id,
        "source": source,
        "payload": payload,
        "headers": headers or {},
        "verified": verified,
        "status": "delivered",
        "received_at": datetime.now(timezone.utc).isoformat(),
    }
    _received.append(event)
    _next_id += 1
    logger.info("Webhook received from %s (id=%d, verified=%s)", source, event["id"], verified)
    return event


def get_log(source: str | None = None, limit: int = 50) -> list[dict]:
    results = _received
    if source:
        results = [r for r in results if r["source"] == source]
    return list(reversed(results))[:limit]


def replay(event_id: int) -> dict | None:
    event = next((r for r in _received if r["id"] == event_id), None)
    if not event:
        return None
    logger.info("Replaying webhook id=%d from %s", event_id, event["source"])
    event["replayed_at"] = datetime.now(timezone.utc).isoformat()
    event["replay_count"] = event.get("replay_count", 0) + 1
    return event
