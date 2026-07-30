from fastapi import APIRouter, HTTPException
from . import service
router = APIRouter(prefix="/api/subscriptions", tags=["subscriptions"])

@router.post("/plans")
async def create_plan(body: dict):
    return {"plan": service.create_plan(body["name"], body.get("price_monthly", 0), body.get("price_yearly", 0), body.get("features", []), body.get("tier", 1), body.get("popular", False))}

@router.get("/plans")
async def list_plans():
    return {"plans": service.list_plans()}

@router.get("/plans/{plan_id}")
async def get_plan(plan_id: int):
    p = service.get_plan(plan_id)
    if not p: raise HTTPException(404)
    return {"plan": p}

@router.post("/user/{user_id}/assign")
async def assign_plan(user_id: int, body: dict):
    return service.assign_plan(user_id, body["plan_id"])

@router.get("/user/{user_id}")
async def get_subscription(user_id: int):
    sub = service.get_user_subscription(user_id)
    if not sub: raise HTTPException(404, "No subscription")
    return {"subscription": sub}

@router.post("/user/{user_id}/cancel")
async def cancel(user_id: int):
    if not service.cancel(user_id): raise HTTPException(404)
    return {"success": True}

@router.post("/user/{user_id}/change")
async def change_plan(user_id: int, body: dict):
    return service.change_plan(user_id, body["plan_id"])
