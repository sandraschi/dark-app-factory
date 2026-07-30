"""Stripe FastAPI routes — checkout, webhook, portal."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Request

from . import service

logger = logging.getLogger("dark_factory")

router = APIRouter(prefix="/api/stripe", tags=["stripe"])


@router.on_event("startup")
async def _startup():
    service.configure()


@router.post("/create-checkout")
async def create_checkout(body: dict):
    """Create a Stripe Checkout Session."""
    result = await service.create_checkout_session(
        price_id=body.get("price_id", ""),
        success_url=body.get("success_url", "http://localhost:3000/success"),
        cancel_url=body.get("cancel_url", "http://localhost:3000/cancel"),
        customer_email=body.get("email"),
        mode=body.get("mode", "payment"),
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return {"success": True, **result}


@router.post("/create-subscription")
async def create_subscription(body: dict):
    """Create a Stripe subscription."""
    result = await service.create_subscription(
        price_id=body.get("price_id", ""),
        customer_email=body.get("email"),
        trial_days=body.get("trial_days", 0),
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return {"success": True, **result}


@router.post("/webhook")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events."""
    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")
    event = await service.construct_webhook_event(payload, sig)
    if event is None:
        raise HTTPException(status_code=400, detail="Invalid signature")
    logger.info("Stripe webhook: %s", event["type"])
    return {"received": True, "type": event["type"]}


@router.post("/customer-portal")
async def customer_portal(body: dict):
    """Create a Customer Portal session for managing subscriptions."""
    result = await service.create_customer_portal(
        customer_id=body.get("customer_id", ""),
        return_url=body.get("return_url", "http://localhost:3000"),
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return {"success": True, **result}


@router.get("/status")
async def stripe_status():
    """Check if Stripe is configured."""
    return {"configured": service.is_configured()}
