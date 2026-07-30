"""Membership FastAPI routes — auth, members, customers, employees."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Header

from . import auth, models

router = APIRouter(prefix="/api", tags=["membership"])


@router.on_event("startup")
async def _startup():
    models.configure()


# ── Auth helpers ───────────────────────────────────────────────────────────

def _get_current_user(authorization: str = Header("")) -> dict:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    payload = auth.decode_token(authorization[7:])
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user = models.get_member_by_id(int(payload["sub"]))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def _require_role(required: str):
    async def _check(user: dict = Depends(_get_current_user)):
        if user["role"] != required and user["role"] != "admin":
            raise HTTPException(status_code=403, detail=f"Requires role: {required}")
        return user
    return _check


# ── Auth endpoints ────────────────────────────────────────────────────────

@router.post("/auth/register")
async def register(body: dict):
    """Register a new member."""
    email = body.get("email", "")
    password = body.get("password", "")
    name = body.get("name", "")
    if not email or not password or not name:
        raise HTTPException(status_code=400, detail="email, password, name required")
    if models.get_member_by_email(email):
        raise HTTPException(status_code=409, detail="Email already registered")
    member = models.create_member(email, auth.hash_password(password), name, role=body.get("role", "member"))
    token = auth.create_token(member["id"], member["role"])
    return {"member": member, "token": token}


@router.post("/auth/login")
async def login(body: dict):
    """Login with email and password."""
    member = models.get_member_by_email(body.get("email", ""))
    if not member or not auth.verify_password(body.get("password", ""), member["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if member["status"] != "active":
        raise HTTPException(status_code=403, detail="Account is not active")
    safe = {k: v for k, v in member.items() if k != "password_hash"}
    token = auth.create_token(member["id"], member["role"])
    return {"member": safe, "token": token}


@router.get("/auth/me")
async def get_me(user: dict = Depends(_get_current_user)):
    """Get the current user's profile."""
    return {"member": user}


# ── Members (club/org directory) ──────────────────────────────────────────

@router.get("/members")
async def list_members(role: str | None = None, status: str | None = None):
    """List all members. Optionally filter by role or status."""
    return {"members": models.list_members(role, status), "count": len(models._memory_db["members"])}


@router.get("/members/{member_id}")
async def get_member(member_id: int):
    m = models.get_member_by_id(member_id)
    if not m:
        raise HTTPException(status_code=404, detail="Member not found")
    return {"member": m}


@router.put("/members/{member_id}")
async def update_member(member_id: int, body: dict, user: dict = Depends(_require_role("admin"))):
    m = models.update_member(member_id, body)
    if not m:
        raise HTTPException(status_code=404, detail="Member not found")
    return {"member": m}


# ── Customers (business) ──────────────────────────────────────────────────

@router.get("/customers")
async def list_customers(search: str = ""):
    return {"customers": models.list_customers(search), "count": len(models._memory_db["customers"])}


@router.post("/customers")
async def create_customer(body: dict, user: dict = Depends(_get_current_user)):
    c = models.create_customer(
        email=body.get("email", ""),
        name=body.get("name", ""),
        phone=body.get("phone", ""),
        company=body.get("company", ""),
        notes=body.get("notes", ""),
        created_by=user["id"],
    )
    return {"customer": c}


@router.get("/customers/{customer_id}")
async def get_customer(customer_id: int):
    c = models.get_customer(customer_id)
    if not c:
        raise HTTPException(status_code=404, detail="Customer not found")
    return {"customer": c}


# ── Employees (business) ──────────────────────────────────────────────────

@router.get("/employees")
async def list_employees(department: str | None = None):
    return {"employees": models.list_employees(department), "count": len(models._memory_db["employees"])}


@router.post("/employees")
async def create_employee(body: dict, user: dict = Depends(_require_role("admin"))):
    e = models.create_employee(
        email=body.get("email", ""),
        name=body.get("name", ""),
        department=body.get("department", ""),
        position=body.get("position", ""),
        phone=body.get("phone", ""),
        role=body.get("role", "employee"),
        notes=body.get("notes", ""),
    )
    return {"employee": e}


@router.get("/employees/{employee_id}")
async def get_employee(employee_id: int):
    e = models.get_employee(employee_id)
    if not e:
        raise HTTPException(status_code=404, detail="Employee not found")
    return {"employee": e}
