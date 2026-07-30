from fastapi import APIRouter, Response
from . import service
router = APIRouter(prefix="/api/seo", tags=["seo"])

@router.get("/sitemap.xml")
async def sitemap():
    settings = service.get_settings()
    xml = service.generate_sitemap(settings["site_url"])
    return Response(content=xml, media_type="application/xml")

@router.get("/robots.txt")
async def robots():
    settings = service.get_settings()
    txt = service.generate_robots(settings["site_url"])
    return Response(content=txt, media_type="text/plain")

@router.get("/json-ld")
async def json_ld():
    s = service.get_settings()
    name = s["title"] or "Organization"
    return service.generate_json_ld(name, s["site_url"], s["description"], s["image"])

@router.get("/settings")
async def get_settings():
    return service.get_settings()

@router.post("/redirects")
async def add_redirect(body: dict):
    return {"redirect": service.add_redirect(body["source"], body["target"], body.get("code", 301))}

@router.get("/redirects")
async def list_redirects():
    return {"redirects": service._redirects}
