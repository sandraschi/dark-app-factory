from fastapi import APIRouter, HTTPException
from . import service
router = APIRouter(prefix="/api/reviews", tags=["reviews"])

@router.post("")
async def submit_review(body: dict):
    return {"review": service.submit(body.get("name", ""), body.get("email", ""), body.get("rating", 5), body.get("title", ""), body.get("content", ""), body.get("auto_approve", False))}

@router.get("")
async def list_reviews(approved: bool = True):
    return {"reviews": service.list_approved() if approved else service.list_pending()}

@router.get("/stats")
async def review_stats():
    return service.get_stats()

@router.post("/{review_id}/approve")
async def approve_review(review_id: int):
    if not service.approve(review_id): raise HTTPException(404, "Not found")
    return {"success": True}

@router.delete("/{review_id}")
async def delete_review(review_id: int):
    if not service.delete(review_id): raise HTTPException(404, "Not found")
    return {"success": True}
