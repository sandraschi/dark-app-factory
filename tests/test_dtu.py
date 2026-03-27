"""Tests for dtu/main.py -- DTU mock server endpoints."""

import pytest
from httpx import AsyncClient, ASGITransport

from dtu.main import app


@pytest.fixture
def transport():
    return ASGITransport(app=app)


@pytest.fixture
async def client(transport):
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac


@pytest.mark.asyncio
async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "services" in data


@pytest.mark.asyncio
async def test_service_registry(client):
    resp = await client.get("/dtu/services")
    assert resp.status_code == 200
    data = resp.json()
    assert "stripe" in data["services"]
    assert "auth" in data["services"]
    assert "env_vars" in data


@pytest.mark.asyncio
async def test_stripe_payment_intent(client):
    resp = await client.post(
        "/stripe/v1/payment_intents",
        json={"amount": 5000, "currency": "eur"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "succeeded"
    assert data["amount"] == 5000


@pytest.mark.asyncio
async def test_auth_login(client):
    resp = await client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "pass123"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_auth_register(client):
    resp = await client.post(
        "/auth/register",
        json={"email": "new@example.com", "password": "secure", "name": "Tester"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["user"]["name"] == "Tester"


@pytest.mark.asyncio
async def test_email_send(client):
    resp = await client.post(
        "/email/send",
        json={"to": "user@example.com", "subject": "Test", "body": "Hello"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "sent"


@pytest.mark.asyncio
async def test_sms_send(client):
    resp = await client.post(
        "/sms/send",
        json={"to": "+431234567", "message": "Test SMS"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "delivered"


@pytest.mark.asyncio
async def test_weather_current(client):
    resp = await client.get("/weather/current", params={"city": "Vienna"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["city"] == "Vienna"
    assert "temperature" in data


@pytest.mark.asyncio
async def test_request_log(client):
    # Make a request first
    await client.get("/health")
    resp = await client.get("/dtu/log")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] > 0
