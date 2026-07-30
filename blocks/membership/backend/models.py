"""Member database — SQLite with aiosqlite for async access."""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("dark_factory")

DB_PATH = os.environ.get("MEMBER_DB_PATH", "data/members.db")

# In-memory fallback when SQLite is unavailable
_memory_db: dict[str, list[dict]] = {
    "members": [],
    "customers": [],
    "employees": [],
}
_next_ids: dict[str, int] = {"members": 1, "customers": 1, "employees": 1}

# ── Schema ─────────────────────────────────────────────────────────────────

MEMBER_SCHEMA = ["id", "email", "password_hash", "name", "role", "phone", "status", "created_at", "notes"]
CUSTOMER_SCHEMA = ["id", "email", "name", "phone", "company", "status", "created_at", "notes", "created_by"]
EMPLOYEE_SCHEMA = ["id", "email", "name", "phone", "department", "position", "role", "status", "created_at", "notes"]

ROLES = {"admin", "member", "employee", "customer"}
STATUSES = {"active", "inactive", "suspended", "pending"}


def configure():
    os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)


# ── Members (club/org) ────────────────────────────────────────────────────

def create_member(email: str, password_hash: str, name: str, role: str = "member", phone: str = "", notes: str = "") -> dict:
    m = {
        "id": _next_ids["members"],
        "email": email,
        "password_hash": password_hash,
        "name": name,
        "role": role if role in ROLES else "member",
        "phone": phone,
        "status": "active",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "notes": notes,
    }
    _memory_db["members"].append(m)
    _next_ids["members"] += 1
    return {k: v for k, v in m.items() if k != "password_hash"}


def get_member_by_email(email: str) -> dict | None:
    return next((m for m in _memory_db["members"] if m["email"] == email), None)


def get_member_by_id(member_id: int) -> dict | None:
    return next((m for m in _memory_db["members"] if m["id"] == member_id), None)


def list_members(role: str | None = None, status: str | None = None) -> list[dict]:
    results = _memory_db["members"]
    if role:
        results = [m for m in results if m["role"] == role]
    if status:
        results = [m for m in results if m["status"] == status]
    return [{k: v for k, v in m.items() if k != "password_hash"} for m in results]


def update_member(member_id: int, updates: dict) -> dict | None:
    m = get_member_by_id(member_id)
    if not m:
        return None
    safe_keys = {"name", "phone", "status", "notes", "role"}
    for k, v in updates.items():
        if k in safe_keys:
            m[k] = v
    return {k: v for k, v in m.items() if k != "password_hash"}


# ── Customers (business) ──────────────────────────────────────────────────

def create_customer(email: str, name: str, phone: str = "", company: str = "", notes: str = "", created_by: int = 0) -> dict:
    c = {
        "id": _next_ids["customers"],
        "email": email,
        "name": name,
        "phone": phone,
        "company": company,
        "status": "active",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "notes": notes,
        "created_by": created_by,
    }
    _memory_db["customers"].append(c)
    _next_ids["customers"] += 1
    return c


def list_customers(search: str = "") -> list[dict]:
    results = _memory_db["customers"]
    if search:
        s = search.lower()
        results = [c for c in results if s in c["name"].lower() or s in c["email"].lower() or s in c["company"].lower()]
    return results


def get_customer(customer_id: int) -> dict | None:
    return next((c for c in _memory_db["customers"] if c["id"] == customer_id), None)


# ── Employees (business) ──────────────────────────────────────────────────

def create_employee(email: str, name: str, department: str = "", position: str = "", phone: str = "", role: str = "employee", notes: str = "") -> dict:
    e = {
        "id": _next_ids["employees"],
        "email": email,
        "name": name,
        "phone": phone,
        "department": department,
        "position": position,
        "role": role if role in ROLES else "employee",
        "status": "active",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "notes": notes,
    }
    _memory_db["employees"].append(e)
    _next_ids["employees"] += 1
    return e


def list_employees(department: str | None = None) -> list[dict]:
    results = _memory_db["employees"]
    if department:
        results = [e for e in results if e["department"] == department]
    return results


def get_employee(employee_id: int) -> dict | None:
    return next((e for e in _memory_db["employees"] if e["id"] == employee_id), None)
