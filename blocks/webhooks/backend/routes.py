from fastapi import APIRouter, HTTPException, Request
from . import service
router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])

@router.post("/receive/{source}")
async def receive_webhook(source: str, request: Request):
    body = await request.json()
    sig = request.headers.get("x-webhook-signature", "")
    event = service.receive(source, body, dict(request.headers), sig)
    return {"received": True, "id": event["id"], "verified": event["verified"]}

@router.get("/log")
async def get_log(source: str | None = None, limit: int = 50):
    return {"events": service.get_log(source, limit)}

@router.post("/replay/{event_id}")
async def replay(event_id: int):
    event = service.replay(event_id)
    if not event: raise HTTPException(404, "Event not found")
    return {"replayed": True, "event": event}

@router.get("/stats")
async def get_stats():
    total = len(service._received)
    verified = sum(1 for r in service._received if r["verified"])
    sources = {}
    for r in service._received:
        sources[r["source"]] = sources.get(r["source"], 0) + 1
    return {"total": total, "verified": verified, "sources": sources}
