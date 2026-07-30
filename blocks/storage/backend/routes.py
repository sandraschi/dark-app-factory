"""Storage FastAPI routes — upload, list, serve files."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import FileResponse

from . import service

router = APIRouter(prefix="/api/storage", tags=["storage"])


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    data = await file.read()
    result = await service.upload(file.filename or "file", data)
    return {"success": True, **result}


@router.post("/upload/image")
async def upload_image(file: UploadFile = File(...), max_width: int = 1200, max_height: int = 1200):
    data = await file.read()
    result = await service.upload_image(file.filename or "image.png", data, max_width, max_height)
    return {"success": True, **result}


@router.get("/files")
async def list_files():
    return {"files": service.list_files()}


@router.get("/files/{file_id}")
async def get_file(file_id: str):
    path = service.get_file_path(file_id)
    if not path:
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(str(path))
