"""Notification FastAPI routes — list, read, send."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from . import service

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.post("/send")
async def send_notification(body: dict):
    n = service.send(
        body.get("to_user_id", 0), body.get("title", ""), body.get("message", ""),
        body.get("channel", "in_app"), body.get("priority", "normal"), body.get("link", ""),
    )
    return {"notification": n}


@router.get("")
async def list_notifications(user_id: int, unread_only: bool = False):
    return {"notifications": service.list_for_user(user_id, unread_only)}


@router.get("/unread-count")
async def unread_count(user_id: int):
    return {"count": service.get_unread_count(user_id)}


@router.post("/{notif_id}/read")
async def mark_read(notif_id: int, body: dict):
    if not service.mark_read(notif_id, body.get("user_id", 0)):
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"success": True}


@router.post("/mark-all-read")
async def mark_all_read(body: dict):
    count = service.mark_all_read(body.get("user_id", 0))
    return {"success": True, "count": count}
