"""Webshop FastAPI routes — products, cart, orders."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from . import service

router = APIRouter(prefix="/api", tags=["webshop"])


@router.on_event("startup")
async def _startup():
    service.configure()


# ── Products ──────────────────────────────────────────────────────────────

@router.get("/products")
async def list_products(category: str | None = None):
    return {"products": service.list_products(category), "count": len(service._products)}


@router.get("/products/{product_id}")
async def get_product(product_id: int):
    p = service.get_product(product_id)
    if not p:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"product": p}


@router.post("/products")
async def create_product(body: dict):
    p = service.create_product(
        name=body.get("name", ""),
        price=body.get("price", 0),
        category=body.get("category", ""),
        description=body.get("description", ""),
        stock=body.get("stock", 0),
        image_url=body.get("image_url", ""),
    )
    return {"product": p}


# ── Cart ──────────────────────────────────────────────────────────────────

@router.get("/cart")
async def get_cart(session_id: str):
    return {"items": service.get_cart(session_id), "session_id": session_id}


@router.post("/cart/add")
async def add_to_cart(body: dict):
    result = service.add_to_cart(body.get("session_id", ""), body.get("product_id", 0), body.get("quantity", 1))
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/cart/remove")
async def remove_from_cart(body: dict):
    service.remove_from_cart(body.get("session_id", ""), body.get("product_id", 0))
    return {"success": True}


@router.post("/cart/clear")
async def clear_cart(body: dict):
    service.clear_cart(body.get("session_id", ""))
    return {"success": True}


# ── Checkout → Stripe ────────────────────────────────────────────────────

@router.post("/checkout")
async def checkout(body: dict):
    """Create order + Stripe checkout session."""
    session_id = body.get("session_id", "")
    cart = service.get_cart(session_id)
    if not cart:
        raise HTTPException(status_code=400, detail="Cart is empty")

    # Try to use Stripe if configured
    try:
        from blocks.stripe.backend import service as stripe_service

        stripe_service.configure()
        if stripe_service.is_configured():
            total_cents = int(sum(i["price"] * i["quantity"] for i in cart) * 100)
            result = await stripe_service.create_checkout_session(
                price_id=None,
                success_url=body.get("success_url", "http://localhost:3000/orders"),
                cancel_url=body.get("cancel_url", "http://localhost:3000/cart"),
                customer_email=body.get("email"),
                mode="payment",
            )
            if "url" in result:
                service.create_order(session_id, {"email": body.get("email", "")}, stripe_session_id=result["session_id"])
                return {"checkout_url": result["url"], "stripe": True}
    except ImportError:
        pass

    # Fallback: direct order without payment
    order = service.create_order(session_id, {"email": body.get("email", "")})
    return {"order": order, "stripe": False, "message": "Order placed (payment not configured)"}


# ── Orders ────────────────────────────────────────────────────────────────

@router.get("/orders")
async def list_orders():
    return {"orders": service.list_orders()}


@router.get("/orders/{order_id}")
async def get_order(order_id: int):
    o = service.get_order(order_id)
    if not o:
        raise HTTPException(status_code=404, detail="Order not found")
    return {"order": o}
