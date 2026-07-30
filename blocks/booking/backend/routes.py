"""Booking FastAPI routes — slots, appointments."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from . import service

router = APIRouter(prefix="/api/booking", tags=["booking"])


@router.get("/slots")
async def get_slots(duration_min: int = 60, days_ahead: int = 14):
    return {"slots": service.get_available_slots(duration_min, days_ahead)}


@router.post("/appointments")
async def create_appointment(body: dict):
    appt = service.create_appointment(
        body.get("start", ""), body.get("customer_name", ""), body.get("customer_email", ""), body.get("notes", ""),
    )
    return {"appointment": appt}


@router.get("/appointments")
async def list_appointments(status: str | None = None):
    return {"appointments": service.list_appointments(status)}


@router.get("/appointments/{appt_id}")
async def get_appointment(appt_id: int):
    a = service.get_appointment(appt_id)
    if not a:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return {"appointment": a}


@router.put("/appointments/{appt_id}")
async def update_appointment(appt_id: int, body: dict):
    a = service.update_appointment(appt_id, body)
    if not a:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return {"appointment": a}
