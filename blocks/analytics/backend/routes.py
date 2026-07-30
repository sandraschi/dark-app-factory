"""Analytics FastAPI routes."""

from fastapi import APIRouter

from . import service

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.post("/pageview")
async def track_pageview(body: dict):
    pv = service.track_pageview(body.get("path", "/"), body.get("referrer", ""), body.get("user_agent", ""), body.get("ip", ""), body.get("session_id", ""))
    return {"success": True, "pageview": pv}


@router.post("/events")
async def track_event(body: dict):
    ev = service.track_event(body.get("name", ""), body.get("category", "general"), body.get("label", ""), body.get("value", 0), body.get("session_id", ""))
    return {"success": True, "event": ev}


@router.get("/dashboard")
async def get_dashboard(hours: int = 24):
    return service.get_dashboard(hours)


@router.get("/visitors")
async def get_visitors(hours: int = 24):
    data = service.get_dashboard(hours)
    return {"visitors": data["unique_sessions"], "pageviews": data["total_pageviews"], "top_pages": data["top_pages"], "top_referrers": data["top_referrers"]}
