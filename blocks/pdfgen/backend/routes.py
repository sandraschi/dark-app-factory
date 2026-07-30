from fastapi import APIRouter, HTTPException
from . import service
router = APIRouter(prefix="/api/pdf", tags=["pdf"])

@router.post("/generate")
async def generate_pdf(body: dict):
    result = await service.generate_from_html(body.get("html", "<p>Empty</p>"), body.get("filename", "document.pdf"))
    if "error" in result: raise HTTPException(501, result["error"])
    return result

@router.post("/invoice")
async def generate_invoice(body: dict):
    result = await service.generate_invoice(body.get("items", []), body.get("company", ""), body.get("customer", ""), body.get("number", ""))
    if "error" in result: raise HTTPException(501, result["error"])
    return result

@router.get("/templates")
async def list_templates():
    return {"templates": list(service.TEMPLATES.keys())}
