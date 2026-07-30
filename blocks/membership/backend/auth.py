"""Auth service — JWT tokens, password hashing, role-based access."""

from __future__ import annotations

import hashlib
import logging
import os
import secrets
from datetime import datetime, timezone, timedelta
from typing import Any

from jose import JWTError, jwt

logger = logging.getLogger("dark_factory")

_SECRET = os.environ.get("JWT_SECRET", "change-me")
_ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")
_ACCESS_EXPIRE = 86400  # 24h


def hash_password(password: str) -> str:
    """SHA-256 hash with random salt. Returns salt$hash."""
    salt = secrets.token_hex(16)
    h = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"{salt}${h}"


def verify_password(plain: str, hashed: str) -> bool:
    try:
        salt, h = hashed.split("$", 1)
        return hashlib.sha256((salt + plain).encode()).hexdigest() == h
    except (ValueError, AttributeError):
        return False


def create_token(user_id: int, role: str = "member") -> str:
    expire = datetime.now(timezone.utc) + timedelta(seconds=_ACCESS_EXPIRE)
    return jwt.encode({"sub": str(user_id), "role": role, "exp": expire}, _SECRET, algorithm=_ALGORITHM)


def decode_token(token: str) -> dict[str, Any] | None:
    try:
        payload = jwt.decode(token, _SECRET, algorithms=[_ALGORITHM])
        return payload
    except JWTError:
        return None
