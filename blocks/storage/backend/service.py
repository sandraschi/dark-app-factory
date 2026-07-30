"""Storage service — local FS and S3 backends, image resizing."""

from __future__ import annotations

import logging
import os
import uuid
from io import BytesIO
from pathlib import Path
from typing import Any

logger = logging.getLogger("dark_factory")

UPLOAD_DIR = Path("data/uploads")
THUMB_DIR = Path("data/thumbs")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
THUMB_DIR.mkdir(parents=True, exist_ok=True)


def _backend() -> str:
    return os.environ.get("STORAGE_BACKEND", "local")


async def _save_local(filename: str, data: bytes) -> dict:
    file_id = str(uuid.uuid4())
    ext = Path(filename).suffix
    dest = UPLOAD_DIR / f"{file_id}{ext}"
    dest.write_bytes(data)
    return {"id": file_id, "filename": filename, "size": len(data), "path": str(dest), "url": f"/api/storage/files/{file_id}"}


async def _save_s3(filename: str, data: bytes, bucket: str) -> dict:
    import boto3

    file_id = str(uuid.uuid4())
    ext = Path(filename).suffix
    key = f"uploads/{file_id}{ext}"
    s3 = boto3.client("s3", region_name=os.environ.get("AWS_REGION", "us-east-1"))
    s3.put_object(Bucket=bucket, Key=key, Body=data)
    return {"id": file_id, "filename": filename, "size": len(data), "key": key, "bucket": bucket}


async def upload(filename: str, data: bytes) -> dict:
    backend = _backend()
    if backend == "s3":
        bucket = os.environ.get("S3_BUCKET", "")
        if bucket:
            return await _save_s3(filename, data, bucket)
    return await _save_local(filename, data)


async def upload_image(filename: str, data: bytes, max_width: int = 1200, max_height: int = 1200) -> dict:
    from PIL import Image

    img = Image.open(BytesIO(data))
    img.thumbnail((max_width, max_height), Image.LANCZOS)
    buf = BytesIO()
    ext = Path(filename).suffix.lower()
    fmt = "JPEG" if ext in (".jpg", ".jpeg") else "PNG"
    img.save(buf, format=fmt)
    buf.seek(0)
    result = await upload(filename, buf.getvalue())
    result["resized"] = True
    result["dimensions"] = {"width": img.width, "height": img.height}
    return result


def get_file_path(file_id: str) -> Path | None:
    for f in UPLOAD_DIR.iterdir():
        if f.stem == file_id:
            return f
    return None


def list_files() -> list[dict]:
    files = []
    for f in sorted(UPLOAD_DIR.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
        files.append({"id": f.stem, "filename": f.name, "size": f.stat().st_size, "url": f"/api/storage/files/{f.stem}"})
    return files
