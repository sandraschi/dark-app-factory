"""Business website FastAPI routes."""

from __future__ import annotations

from fastapi import APIRouter

from . import service

router = APIRouter(prefix="/api/business", tags=["business"])


@router.on_event("startup")
async def _startup():
    service.configure()


@router.get("/info")
async def get_info():
    return {"info": service.get_info()}


@router.put("/info")
async def update_info(body: dict):
    return {"info": service.update_info(body)}


@router.get("/services")
async def list_services(category: str | None = None):
    return {"services": service.list_services(category)}


@router.post("/services")
async def add_service(body: dict):
    s = service.add_service(body.get("name", ""), body.get("description", ""), body.get("price", ""), body.get("duration", ""), body.get("category", ""), body.get("featured", False))
    return {"service": s}


@router.get("/team")
async def list_team():
    return {"team": service.list_team()}


@router.get("/faq")
async def list_faq(category: str | None = None):
    return {"faq": service.list_faq(category)}


@router.post("/contact")
async def submit_contact(body: dict):
    c = service.submit_contact(body.get("name", ""), body.get("email", ""), body.get("phone", ""), body.get("message", ""))
    return {"contact": c}


@router.get("/contacts")
async def list_contacts():
    return {"contacts": service.list_contacts()}
