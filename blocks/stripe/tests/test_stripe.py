"""Tests for Stripe block."""

from __future__ import annotations

import os
from unittest.mock import MagicMock

import pytest


# Mock stripe module before any test imports it
import sys

_mock_stripe = MagicMock()
_mock_stripe.checkout.Session.create.return_value = MagicMock(url="https://checkout.stripe.com/test", id="cs_test_123")
_mock_stripe.Subscription.create.return_value = MagicMock(
    id="sub_123", latest_invoice=MagicMock(payment_intent=MagicMock(client_secret="pi_secret_123")),
)
_mock_stripe.error.StripeError = Exception
_mock_stripe.Webhook.construct_event.return_value = MagicMock(type="checkout.session.completed", data=MagicMock(object={}))
_mock_stripe.billing_portal.Session.create.return_value = MagicMock(url="https://billing.stripe.com/test")
sys.modules["stripe"] = _mock_stripe
sys.modules["stripe.error"] = _mock_stripe.error


@pytest.mark.asyncio
async def test_create_checkout_session():
    os.environ["STRIPE_SECRET_KEY"] = "sk_test_mock"
    os.environ["STRIPE_PUBLISHABLE_KEY"] = "pk_test_mock"
    from blocks.stripe.backend.service import configure, create_checkout_session

    configure()
    result = await create_checkout_session("price_123")
    assert result["url"] == "https://checkout.stripe.com/test"
    assert result["session_id"] == "cs_test_123"


@pytest.mark.asyncio
async def test_create_checkout_not_configured():
    os.environ.pop("STRIPE_SECRET_KEY", None)
    # Force re-import with clean state
    from blocks.stripe.backend import service as svc

    svc._SECRET_KEY = None
    result = await svc.create_checkout_session("price_123")
    assert "error" in result


@pytest.mark.asyncio
async def test_create_subscription():
    os.environ["STRIPE_SECRET_KEY"] = "sk_test_mock"
    from blocks.stripe.backend.service import configure, create_subscription

    configure()
    result = await create_subscription("price_monthly", "test@example.com")
    assert result["subscription_id"] == "sub_123"
    assert result["client_secret"] == "pi_secret_123"
