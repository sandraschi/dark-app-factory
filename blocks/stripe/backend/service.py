"""Stripe service — checkout sessions, webhooks, subscriptions."""

from __future__ import annotations

import logging
import os

import stripe

logger = logging.getLogger("dark_factory")

_SECRET_KEY: str | None = None
_WEBHOOK_SECRET: str | None = None


def configure():
    global _SECRET_KEY, _WEBHOOK_SECRET
    _SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
    _WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
    if _SECRET_KEY:
        stripe.api_key = _SECRET_KEY


def is_configured() -> bool:
    return bool(_SECRET_KEY)


async def create_checkout_session(
    price_id: str,
    success_url: str = "http://localhost:3000/success",
    cancel_url: str = "http://localhost:3000/cancel",
    customer_email: str | None = None,
    mode: str = "payment",
    allow_promotion_codes: bool = True,
) -> dict:
    """Create a Stripe Checkout Session."""
    if not _SECRET_KEY:
        return {"error": "Stripe not configured — set STRIPE_SECRET_KEY"}
    try:
        session = stripe.checkout.Session.create(
            line_items=[{"price": price_id, "quantity": 1}],
            mode=mode,
            success_url=success_url,
            cancel_url=cancel_url,
            customer_email=customer_email,
            allow_promotion_codes=allow_promotion_codes,
        )
        return {"url": session.url, "session_id": session.id}
    except stripe.error.StripeError as e:
        logger.error("Stripe checkout failed: %s", e)
        return {"error": str(e)}


async def create_subscription(
    price_id: str,
    customer_email: str | None = None,
    trial_days: int = 0,
) -> dict:
    """Create a Stripe subscription."""
    if not _SECRET_KEY:
        return {"error": "Stripe not configured"}
    try:
        customer_data = {"email": customer_email} if customer_email else {}
        subscription = stripe.Subscription.create(
            customer=customer_data,
            items=[{"price": price_id}],
            trial_period_days=trial_days or None,
            payment_behavior="default_incomplete",
            expand=["latest_invoice.payment_intent"],
        )
        return {"subscription_id": subscription.id, "client_secret": subscription.latest_invoice.payment_intent.client_secret}
    except stripe.error.StripeError as e:
        logger.error("Stripe subscription failed: %s", e)
        return {"error": str(e)}


async def construct_webhook_event(payload: bytes, sig_header: str) -> dict | None:
    """Verify and construct a Stripe webhook event."""
    if not _WEBHOOK_SECRET:
        return None
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, _WEBHOOK_SECRET)
        return {"type": event.type, "data": event.data.object}
    except stripe.error.SignatureVerificationError as e:
        logger.warning("Stripe webhook signature invalid: %s", e)
        return None


async def create_customer_portal(customer_id: str, return_url: str = "http://localhost:3000") -> dict:
    """Create a Stripe Customer Portal session."""
    if not _SECRET_KEY:
        return {"error": "Stripe not configured"}
    try:
        session = stripe.billing_portal.Session.create(customer=customer_id, return_url=return_url)
        return {"url": session.url}
    except stripe.error.StripeError as e:
        logger.error("Stripe portal failed: %s", e)
        return {"error": str(e)}
