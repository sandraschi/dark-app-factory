"""Booking service — availability slots, appointment management."""

from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta, date, time
from typing import Any

logger = logging.getLogger("dark_factory")

_slots: list[dict] = []
_appointments: list[dict] = []
_next_id = 1


def _today() -> date:
    return datetime.now(timezone.utc).date()


def generate_slots(duration_min: int = 60, days_ahead: int = 14, start_hour: int = 9, end_hour: int = 17, interval_min: int = 30) -> list[dict]:
    """Generate time slots for the next N days."""
    slots = []
    for d in range(days_ahead):
        day = _today() + timedelta(days=d)
        for h in range(start_hour, end_hour):
            for m in range(0, 60, interval_min):
                start = datetime.combine(day, time(h, m))
                end = start + timedelta(minutes=duration_min)
                slot_id = len(_slots) + len(slots) + 1
                slots.append({"id": slot_id, "start": start.isoformat(), "end": end.isoformat(), "available": True})
    return slots


def get_available_slots(duration_min: int = 60, days_ahead: int = 14) -> list[dict]:
    all_slots = generate_slots(duration_min, days_ahead)
    booked = {(a["start"], a["end"]) for a in _appointments if a["status"] != "cancelled"}
    return [s for s in all_slots if (s["start"], s["end"]) not in booked]


def create_appointment(slot_start: str, customer_name: str, customer_email: str, notes: str = "") -> dict:
    global _next_id
    appt = {
        "id": _next_id,
        "start": slot_start,
        "customer_name": customer_name,
        "customer_email": customer_email,
        "notes": notes,
        "status": "confirmed",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    _appointments.append(appt)
    _next_id += 1
    return appt


def list_appointments(status: str | None = None) -> list[dict]:
    results = _appointments
    if status:
        results = [a for a in results if a["status"] == status]
    return list(reversed(results))


def get_appointment(appt_id: int) -> dict | None:
    return next((a for a in _appointments if a["id"] == appt_id), None)


def update_appointment(appt_id: int, updates: dict) -> dict | None:
    a = get_appointment(appt_id)
    if not a:
        return None
    safe = {"status", "notes", "customer_name", "customer_email"}
    for k, v in updates.items():
        if k in safe:
            a[k] = v
    return a
