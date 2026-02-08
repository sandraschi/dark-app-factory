"""
Digital Twin Universe (DTU) - Local mock server for external APIs.

Provides deterministic, always-succeeding mock endpoints for:
- Stripe payments
- Auth (JWT login/register)
- Email/SMS sending
- S3/file storage
- Discord/Slack webhooks
- Weather API
- Generic webhook receiver

The DTU runs on a configurable port (default 8001) and exposes a
service registry at /dtu/services so generated apps can discover
which mocks are available.
"""

import logging
import os
import time
import uuid
from typing import Dict, List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel

logger = logging.getLogger("dtu")
logging.basicConfig(level=logging.INFO, format="%(name)s %(levelname)s %(message)s")

DTU_PORT = int(os.environ.get("DTU_PORT", "8001"))

app = FastAPI(
    title="Dark App Factory - Digital Twin Universe",
    description="Local mock server for external API dependencies.",
    version="0.2.0",
)

# =====================================================================
# Request log -- record all incoming requests for audit
# =====================================================================
request_log: List[Dict] = []


@app.middleware("http")
async def log_requests(request: Request, call_next):
    entry = {
        "timestamp": time.time(),
        "method": request.method,
        "path": request.url.path,
        "query": str(request.query_params),
    }
    request_log.append(entry)
    if len(request_log) > 500:
        request_log.pop(0)
    response = await call_next(request)
    return response


# =====================================================================
# Service Registry
# =====================================================================
SERVICE_REGISTRY = {
    "stripe": {
        "base_url": f"http://localhost:{DTU_PORT}/stripe",
        "env_var": "STRIPE_API_URL",
        "description": "Stripe payment mock (always succeeds)",
    },
    "auth": {
        "base_url": f"http://localhost:{DTU_PORT}/auth",
        "env_var": "AUTH_API_URL",
        "description": "JWT auth mock (login, register, verify)",
    },
    "email": {
        "base_url": f"http://localhost:{DTU_PORT}/email",
        "env_var": "EMAIL_API_URL",
        "description": "Email sending mock (always succeeds)",
    },
    "sms": {
        "base_url": f"http://localhost:{DTU_PORT}/sms",
        "env_var": "SMS_API_URL",
        "description": "SMS sending mock (always succeeds)",
    },
    "storage": {
        "base_url": f"http://localhost:{DTU_PORT}/storage",
        "env_var": "STORAGE_API_URL",
        "description": "S3-compatible file storage mock",
    },
    "discord": {
        "base_url": f"http://localhost:{DTU_PORT}/discord",
        "env_var": "DISCORD_WEBHOOK_URL",
        "description": "Discord webhook mock",
    },
    "slack": {
        "base_url": f"http://localhost:{DTU_PORT}/slack",
        "env_var": "SLACK_WEBHOOK_URL",
        "description": "Slack webhook mock",
    },
    "weather": {
        "base_url": f"http://localhost:{DTU_PORT}/weather",
        "env_var": "WEATHER_API_URL",
        "description": "Weather API mock",
    },
    "webhook": {
        "base_url": f"http://localhost:{DTU_PORT}/webhook",
        "env_var": "WEBHOOK_URL",
        "description": "Generic webhook receiver (logs all calls)",
    },
}


@app.get("/dtu/services")
async def get_service_registry():
    """Returns the full service registry so generated apps can discover mock URLs."""
    return {
        "dtu_version": "0.2.0",
        "port": DTU_PORT,
        "services": SERVICE_REGISTRY,
        "env_vars": {v["env_var"]: v["base_url"] for v in SERVICE_REGISTRY.values()},
    }


@app.get("/dtu/log")
async def get_request_log(limit: int = 50):
    """Returns the last N requests received by DTU for debugging."""
    return {"count": len(request_log), "entries": request_log[-limit:]}


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "version": "dtu-0.2.0",
        "services": list(SERVICE_REGISTRY.keys()),
        "port": DTU_PORT,
    }


# =====================================================================
# Stripe Mock
# =====================================================================
class PaymentIntent(BaseModel):
    amount: int
    currency: str = "usd"
    payment_method_types: List[str] = ["card"]


@app.post("/stripe/v1/payment_intents")
async def create_payment_intent(intent: PaymentIntent):
    return {
        "id": f"pi_mock_{uuid.uuid4().hex[:12]}",
        "object": "payment_intent",
        "amount": intent.amount,
        "currency": intent.currency,
        "status": "succeeded",
        "client_secret": f"pi_mock_secret_{uuid.uuid4().hex[:8]}",
    }


@app.post("/stripe/v1/charges")
async def create_charge(request: Request):
    body = await request.json()
    return {
        "id": f"ch_mock_{uuid.uuid4().hex[:12]}",
        "object": "charge",
        "amount": body.get("amount", 0),
        "currency": body.get("currency", "usd"),
        "status": "succeeded",
        "paid": True,
    }


@app.get("/stripe/v1/balance")
async def get_balance():
    return {
        "object": "balance",
        "available": [{"amount": 100000, "currency": "usd"}],
        "pending": [{"amount": 5000, "currency": "usd"}],
    }


# =====================================================================
# Auth Mock
# =====================================================================
class UserCredentials(BaseModel):
    email: str
    password: str
    name: Optional[str] = None


MOCK_JWT = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJtb2NrX3VzZXIiLCJleHAiOjk5OTk5OTk5OTl9.mock_signature"


@app.post("/auth/login")
async def login(user: UserCredentials):
    return {
        "token": MOCK_JWT,
        "token_type": "bearer",
        "user": {"email": user.email, "id": f"usr_{uuid.uuid4().hex[:8]}"},
    }


@app.post("/auth/register")
async def register(user: UserCredentials):
    return {
        "token": MOCK_JWT,
        "token_type": "bearer",
        "user": {
            "email": user.email,
            "name": user.name or "Mock User",
            "id": f"usr_{uuid.uuid4().hex[:8]}",
        },
    }


@app.get("/auth/verify")
async def verify_token():
    return {"valid": True, "user": {"email": "mock@example.com", "id": "usr_mock123"}}


@app.get("/auth/me")
async def get_current_user():
    return {"email": "mock@example.com", "id": "usr_mock123", "name": "Mock User"}


# =====================================================================
# Email Mock
# =====================================================================
class EmailRequest(BaseModel):
    to: str
    subject: str
    body: str
    from_email: Optional[str] = "noreply@dtu.local"


@app.post("/email/send")
async def send_email(email: EmailRequest):
    logger.info("DTU Email -> %s: %s", email.to, email.subject)
    return {
        "id": f"msg_{uuid.uuid4().hex[:12]}",
        "status": "sent",
        "to": email.to,
        "subject": email.subject,
    }


# =====================================================================
# SMS Mock
# =====================================================================
class SMSRequest(BaseModel):
    to: str
    message: str


@app.post("/sms/send")
async def send_sms(sms: SMSRequest):
    logger.info("DTU SMS -> %s: %s", sms.to, sms.message[:50])
    return {
        "id": f"sms_{uuid.uuid4().hex[:12]}",
        "status": "delivered",
        "to": sms.to,
    }


# =====================================================================
# Storage Mock (S3-compatible)
# =====================================================================
@app.post("/storage/upload")
async def upload_file(request: Request):
    return {
        "key": f"uploads/{uuid.uuid4().hex[:16]}.bin",
        "bucket": "dtu-mock-bucket",
        "url": f"http://localhost:{DTU_PORT}/storage/files/{uuid.uuid4().hex[:16]}",
        "status": "uploaded",
    }


@app.get("/storage/files/{key}")
async def get_file(key: str):
    return {"key": key, "content": "mock_file_content_base64", "size": 1024}


@app.delete("/storage/files/{key}")
async def delete_file(key: str):
    return {"key": key, "status": "deleted"}


# =====================================================================
# Discord / Slack Webhook Mocks
# =====================================================================
@app.post("/discord/webhooks/{webhook_id}/{webhook_token}")
async def discord_webhook(webhook_id: str, webhook_token: str, request: Request):
    body = await request.json()
    logger.info("DTU Discord webhook: %s", str(body)[:100])
    return {"id": f"msg_{uuid.uuid4().hex[:12]}"}


@app.post("/slack/hooks/{hook_id}")
async def slack_webhook(hook_id: str, request: Request):
    body = await request.json()
    logger.info("DTU Slack webhook: %s", str(body)[:100])
    return {"ok": True, "message": "posted"}


# =====================================================================
# Weather Mock
# =====================================================================
@app.get("/weather/current")
async def get_weather(city: str = "Vienna", units: str = "metric"):
    return {
        "city": city,
        "temperature": 18.5,
        "humidity": 65,
        "description": "Partly cloudy",
        "wind_speed": 12.3,
        "units": units,
    }


@app.get("/weather/forecast")
async def get_forecast(city: str = "Vienna", days: int = 5):
    return {
        "city": city,
        "forecast": [
            {"day": i + 1, "high": 20 + i, "low": 10 + i, "condition": "Cloudy"}
            for i in range(days)
        ],
    }


# =====================================================================
# Generic Webhook Receiver
# =====================================================================
@app.post("/webhook/{path:path}")
async def generic_webhook(path: str, request: Request):
    try:
        body = await request.json()
    except Exception:
        body = {"raw": (await request.body()).decode("utf-8", errors="replace")[:500]}
    logger.info("DTU webhook /%s: %s", path, str(body)[:100])
    return {"received": True, "path": path}


# =====================================================================
# Entry point
# =====================================================================
if __name__ == "__main__":
    logger.info("Starting Digital Twin Universe on port %d", DTU_PORT)
    uvicorn.run(app, host="0.0.0.0", port=DTU_PORT)
