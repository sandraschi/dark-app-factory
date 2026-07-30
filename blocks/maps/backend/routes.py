from fastapi import APIRouter
from . import service
router = APIRouter(prefix="/api/maps", tags=["maps"])

@router.get("/locations")
async def list_locations(category: str | None = None):
    return {"locations": service.list_locations(category)}

@router.post("/locations")
async def add_location(body: dict):
    return {"location": service.add_location(body.get("name", ""), body.get("lat", 0), body.get("lng", 0), body.get("address", ""), body.get("phone", ""), body.get("hours", ""), body.get("category", ""))}

@router.get("/nearby")
async def nearby(lat: float, lng: float, radius: float = 10):
    return {"locations": service.nearby(lat, lng, radius)}
