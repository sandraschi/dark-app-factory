"""Tests for email block."""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_send_dry_run():
    from blocks.email.backend import service as s

    result = await s.send_email("test@test.com", "Subject", "<p>Body</p>")
    assert result["success"] is True
    assert result.get("dry_run") is True


@pytest.mark.asyncio
async def test_render_template():
    from blocks.email.backend import service as s

    s.TEMPLATES["test"] = "<p>Hello {{name}}!</p>"
    html = s.render("test", name="Alice")
    assert html == "<p>Hello Alice!</p>"


@pytest.mark.asyncio
async def test_send_verification():
    from blocks.email.backend import service as s

    result = await s.send_verification("a@b.com", "tok123", "http://x.com/verify")
    assert result["success"] is True


@pytest.mark.asyncio
async def test_send_welcome():
    from blocks.email.backend import service as s

    result = await s.send_welcome("a@b.com", "Alice")
    assert result["success"] is True
