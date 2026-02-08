import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict

app = FastAPI(title="Dark App Factory - Digital Twin Universe")


# Mock Stripe Output
class PaymentIntent(BaseModel):
    amount: int
    currency: str
    payment_method_types: list[str] = ["card"]


@app.post("/stripe/v1/payment_intents")
async def create_payment_intent(intent: PaymentIntent):
    return {
        "id": "pi_mock_123456789",
        "object": "payment_intent",
        "amount": intent.amount,
        "currency": intent.currency,
        "status": "succeeded",  # Always succeed in DTU-Lite
        "client_secret": "pi_mock_secret_123",
    }


# Mock Auth (Generic)
class User(BaseModel):
    email: str
    password: str


@app.post("/auth/login")
async def login(user: User):
    if user.email == "test@example.com" and user.password == "password":
        return {"token": "mock_jwt_token_valid"}
    return HTTPException(status_code=401, detail="Invalid credentials")


@app.get("/health")
async def health():
    return {"status": "ok", "version": "dtu-lite-0.1"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
