"""Webshop backend — products, cart, orders, inventory."""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("dark_factory")

# In-memory store (replace with DB in production)
_products: list[dict] = []
_carts: dict[str, list[dict]] = {}
_orders: list[dict] = []
_next_id = 1
_DATA_FILE = "data/webshop.json"


def _load():
    global _products, _next_id
    if os.path.exists(_DATA_FILE):
        try:
            with open(_DATA_FILE, encoding="utf-8") as f:
                data = json.load(f)
                _products = data.get("products", [])
                _next_id = max((p["id"] for p in _products), default=0) + 1
        except (json.JSONDecodeError, OSError):
            pass


def configure():
    _load()


# ── Products ──────────────────────────────────────────────────────────────

def list_products(category: str | None = None) -> list[dict]:
    if category:
        return [p for p in _products if p.get("category", "").lower() == category.lower()]
    return list(_products)


def get_product(product_id: int) -> dict | None:
    return next((p for p in _products if p["id"] == product_id), None)


def create_product(name: str, price: float, category: str = "", description: str = "", stock: int = 0, image_url: str = "") -> dict:
    global _next_id
    product = {"id": _next_id, "name": name, "price": price, "category": category, "description": description, "stock": stock, "image_url": image_url}
    _products.append(product)
    _next_id += 1
    return product


def update_stock(product_id: int, quantity: int) -> bool:
    p = get_product(product_id)
    if not p or p["stock"] < quantity:
        return False
    p["stock"] -= quantity
    return True


# ── Cart ──────────────────────────────────────────────────────────────────

def get_cart(session_id: str) -> list[dict]:
    return _carts.get(session_id, [])


def add_to_cart(session_id: str, product_id: int, quantity: int = 1) -> dict:
    product = get_product(product_id)
    if not product:
        return {"error": "Product not found"}
    if product["stock"] < quantity:
        return {"error": "Insufficient stock"}
    cart = _carts.setdefault(session_id, [])
    existing = next((i for i in cart if i["product_id"] == product_id), None)
    if existing:
        existing["quantity"] += quantity
    else:
        cart.append({"product_id": product_id, "name": product["name"], "price": product["price"], "quantity": quantity})
    return {"item": cart[-1], "cart_total": sum(i["price"] * i["quantity"] for i in cart)}


def remove_from_cart(session_id: str, product_id: int):
    cart = _carts.get(session_id, [])
    _carts[session_id] = [i for i in cart if i["product_id"] != product_id]


def clear_cart(session_id: str):
    _carts.pop(session_id, None)


# ── Orders ────────────────────────────────────────────────────────────────

def create_order(session_id: str, customer: dict, stripe_session_id: str = "") -> dict:
    cart = _carts.get(session_id, [])
    if not cart:
        return {"error": "Cart is empty"}
    # Check stock and reserve
    for item in cart:
        if not update_stock(item["product_id"], item["quantity"]):
            return {"error": f"Insufficient stock for {item['name']}"}
    total = sum(i["price"] * i["quantity"] for i in cart)
    order = {
        "id": len(_orders) + 1,
        "session_id": session_id,
        "items": list(cart),
        "total": total,
        "customer": customer,
        "stripe_session_id": stripe_session_id,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    _orders.append(order)
    clear_cart(session_id)
    return order


def list_orders() -> list[dict]:
    return list(_orders)


def get_order(order_id: int) -> dict | None:
    return next((o for o in _orders if o["id"] == order_id), None)
