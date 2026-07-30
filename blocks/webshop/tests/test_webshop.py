"""Tests for webshop block."""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def reset_state():
    from blocks.webshop.backend import service as s

    s._products.clear()
    s._carts.clear()
    s._orders.clear()
    s._next_id = 1


@pytest.mark.asyncio
async def test_create_and_list_products():
    from blocks.webshop.backend import service as s

    s.create_product("Test Product", 19.99, category="widgets", stock=10)
    s.create_product("Another", 9.99, category="gadgets", stock=5)
    assert len(s.list_products()) == 2
    assert len(s.list_products("widgets")) == 1


@pytest.mark.asyncio
async def test_cart_add_and_total():
    from blocks.webshop.backend import service as s

    s.create_product("Widget", 10.0, stock=5)
    result = s.add_to_cart("sess_1", 1, 2)
    assert "error" not in result
    assert result["cart_total"] == 20.0
    cart = s.get_cart("sess_1")
    assert len(cart) == 1
    assert cart[0]["quantity"] == 2


@pytest.mark.asyncio
async def test_cart_insufficient_stock():
    from blocks.webshop.backend import service as s

    s.create_product("Widget", 10.0, stock=1)
    result = s.add_to_cart("sess_1", 1, 5)
    assert "error" in result


@pytest.mark.asyncio
async def test_create_order():
    from blocks.webshop.backend import service as s

    s.create_product("Widget", 10.0, stock=5)
    s.add_to_cart("sess_1", 1, 2)
    order = s.create_order("sess_1", {"email": "test@test.com"})
    assert "error" not in order
    assert order["total"] == 20.0
    assert order["status"] == "pending"
    # Stock should be reduced
    assert s.get_product(1)["stock"] == 3


@pytest.mark.asyncio
async def test_order_empty_cart():
    from blocks.webshop.backend import service as s

    order = s.create_order("sess_empty", {"email": "test@test.com"})
    assert "error" in order
