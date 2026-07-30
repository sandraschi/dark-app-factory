from fastapi import APIRouter, Response
from . import service
router = APIRouter(prefix="/api/csv", tags=["csv"])

@router.post("/export")
async def export_csv(body: dict):
    csv_str = service.export_csv(body.get("data", []), body.get("fields"))
    return Response(content=csv_str, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=export.csv"})

@router.post("/import")
async def import_csv(body: dict):
    return service.import_csv(body.get("content", ""), body.get("fields"))

@router.get("/template")
async def generate_template(fields: str = "name,email,phone"):
    csv_str = service.generate_template(fields.split(","))
    return Response(content=csv_str, media_type="text/csv")
