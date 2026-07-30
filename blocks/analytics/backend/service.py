"""Analytics service — page views, events, visitor stats."""

from __future__ import annotations

import logging
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from typing import Any

logger = logging.getLogger("dark_factory")

_pageviews: list[dict] = []
_events: list[dict] = []


def track_pageview(path: str, referrer: str = "", user_agent: str = "", ip: str = "", session_id: str = "") -> dict:
    pv = {"path": path, "referrer": referrer, "user_agent": user_agent, "ip": ip, "session_id": session_id, "timestamp": datetime.now(timezone.utc).isoformat()}
    _pageviews.append(pv)
    return pv


def track_event(name: str, category: str = "general", label: str = "", value: float = 0, session_id: str = "") -> dict:
    ev = {"name": name, "category": category, "label": label, "value": value, "session_id": session_id, "timestamp": datetime.now(timezone.utc).isoformat()}
    _events.append(ev)
    return ev


def get_dashboard(hours: int = 24) -> dict:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    recent_pv = [p for p in _pageviews if datetime.fromisoformat(p["timestamp"]) > cutoff]
    recent_ev = [e for e in _events if datetime.fromisoformat(e["timestamp"]) > cutoff]

    page_counts: dict[str, int] = defaultdict(int)
    hourly: dict[str, int] = defaultdict(int)
    referrers: dict[str, int] = defaultdict(int)

    for pv in recent_pv:
        page_counts[pv["path"]] += 1
        hour_key = pv["timestamp"][:13]
        hourly[hour_key] += 1
        if pv.get("referrer"):
            ref = pv["referrer"].split("/")[2] if "://" in pv["referrer"] else pv["referrer"]
            referrers[ref] += 1

    return {
        "total_pageviews": len(recent_pv),
        "total_events": len(recent_ev),
        "unique_sessions": len({p["session_id"] for p in recent_pv if p.get("session_id")}),
        "top_pages": sorted(page_counts.items(), key=lambda x: -x[1])[:10],
        "hourly_traffic": dict(sorted(hourly.items())),
        "top_referrers": sorted(referrers.items(), key=lambda x: -x[1])[:10],
        "recent_events": recent_ev[-20:],
    }
