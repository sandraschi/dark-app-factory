"""Business website service — info, services, team, contact, FAQ."""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("dark_factory")

_info: dict = {
    "name": "",
    "tagline": "",
    "address": "",
    "phone": "",
    "email": "",
    "hours": "",
    "service_area": "",
    "hero_image": "",
    "about": "",
}

_services: list[dict] = []
_team: list[dict] = []
_faq: list[dict] = []
_contacts: list[dict] = []
_next_service = 1
_next_faq = 1
_next_contact = 1


def configure(vibe_data: dict | None = None):
    if vibe_data:
        _info.update({k: v for k, v in vibe_data.items() if k in _info})
    _info["name"] = _info["name"] or os.environ.get("BUSINESS_NAME", "Our Business")
    _info["address"] = _info["address"] or os.environ.get("BUSINESS_ADDRESS", "")
    _info["phone"] = _info["phone"] or os.environ.get("BUSINESS_PHONE", "")
    _info["email"] = _info["email"] or os.environ.get("BUSINESS_EMAIL", "")
    _info["hours"] = _info["hours"] or os.environ.get("BUSINESS_HOURS", "Mon-Fri 9am-5pm")
    _info["service_area"] = _info["service_area"] or os.environ.get("SERVICE_AREA", "")


def get_info() -> dict:
    return dict(_info)


def update_info(updates: dict) -> dict:
    safe = {"name", "tagline", "address", "phone", "email", "hours", "service_area", "hero_image", "about"}
    for k, v in updates.items():
        if k in safe:
            _info[k] = v
    return dict(_info)


def add_service(name: str, description: str, price: str = "", duration: str = "", category: str = "", featured: bool = False) -> dict:
    global _next_service
    s = {"id": _next_service, "name": name, "description": description, "price": price, "duration": duration, "category": category, "featured": featured}
    _services.append(s)
    _next_service += 1
    return s


def list_services(category: str | None = None) -> list[dict]:
    if category:
        return [s for s in _services if s.get("category", "").lower() == category.lower()]
    return list(_services)


def add_faq(question: str, answer: str, category: str = "") -> dict:
    global _next_faq
    f = {"id": _next_faq, "question": question, "answer": answer, "category": category}
    _faq.append(f)
    _next_faq += 1
    return f


def list_faq(category: str | None = None) -> list[dict]:
    if category:
        return [f for f in _faq if f.get("category", "").lower() == category.lower()]
    return list(_faq)


def add_team_member(name: str, role: str, bio: str = "", photo_url: str = "") -> dict:
    m = {"id": len(_team) + 1, "name": name, "role": role, "bio": bio, "photo_url": photo_url}
    _team.append(m)
    return m


def list_team() -> list[dict]:
    return list(_team)


def submit_contact(name: str, email: str, phone: str = "", message: str = "") -> dict:
    global _next_contact
    c = {"id": _next_contact, "name": name, "email": email, "phone": phone, "message": message, "created_at": datetime.now(timezone.utc).isoformat(), "read": False}
    _contacts.append(c)
    _next_contact += 1
    logger.info("Contact form submission from %s (%s)", name, email)
    return c


def list_contacts() -> list[dict]:
    return list(reversed(_contacts))
