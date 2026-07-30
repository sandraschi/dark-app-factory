from fastapi import APIRouter
from . import service
router = APIRouter(prefix="/api/i18n", tags=["i18n"])

@router.get("/locales")
async def get_locales():
    return {"supported": service.get_supported(), "default": service.get_default()}

@router.get("/translations")
async def get_translations(locale: str):
    return {"locale": locale, "translations": service.get_translations(locale)}

@router.post("/translations")
async def set_translation(body: dict):
    return service.set_translation(body.get("locale", ""), body.get("key", ""), body.get("value", ""))

@router.post("/translate")
async def translate(body: dict):
    return {"translation": service.translate(body.get("key", ""), body.get("locale", ""), body.get("fallback", ""))}

@router.post("/import")
async def bulk_import(body: dict):
    count = service.bulk_import(body.get("locale", ""), body.get("pairs", {}))
    return {"imported": count}
