"""Email FastAPI routes — send, templates, verify."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from . import service

router = APIRouter(prefix="/api/email", tags=["email"])


@router.on_event("startup")
async def _startup():
    service.configure()


@router.post("/send")
async def send_email(body: dict):
    result = await service.send_email(body.get("to", ""), body.get("subject", ""), body.get("html", ""))
    if not result.get("success"):
        raise HTTPException(status_code=502, detail=result.get("error", "Send failed"))
    return result


@router.post("/send-verification")
async def send_verification(body: dict):
    result = await service.send_verification(body.get("email", ""), body.get("token", ""), body.get("verify_url", "http://localhost:3000/verify"))
    if not result.get("success"):
        raise HTTPException(status_code=502, detail=result.get("error", "Send failed"))
    return result


@router.post("/send-welcome")
async def send_welcome(body: dict):
    result = await service.send_welcome(body.get("email", ""), body.get("name", ""))
    return result


@router.get("/templates")
async def list_templates():
    return {"templates": list(service.TEMPLATES.keys())}


@router.get("/status")
async def email_status():
    has_sg = bool(os.environ.get("SENDGRID_API_KEY", ""))
    has_smtp = bool(os.environ.get("SMTP_HOST", ""))
    return {"configured": has_sg or has_smtp, "mode": "sendgrid" if has_sg else "smtp" if has_smtp else "dry_run"}
