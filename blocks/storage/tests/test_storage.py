"""Tests for storage block."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest


@pytest.mark.asyncio
async def test_upload_local(monkeypatch):
    monkeypatch.setenv("STORAGE_BACKEND", "local")
    from blocks.storage.backend import service as s

    s.UPLOAD_DIR = Path(tempfile.mkdtemp())

    data = b"hello world"
    result = await s.upload("test.txt", data)
    assert result["filename"] == "test.txt"
    assert result["size"] == 11
    assert result["id"] is not None


@pytest.mark.skip(reason="requires Pillow")
@pytest.mark.asyncio
async def test_upload_image_resize(monkeypatch):
    pass


@pytest.mark.asyncio
async def test_list_files(monkeypatch):
    monkeypatch.setenv("STORAGE_BACKEND", "local")
    from blocks.storage.backend import service as s

    s.UPLOAD_DIR = Path(tempfile.mkdtemp())

    await s.upload("a.txt", b"aaa")
    await s.upload("b.txt", b"bbb")
    files = s.list_files()
    assert len(files) == 2
