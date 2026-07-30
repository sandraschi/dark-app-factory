"""Blog FastAPI routes — articles, RSS, categories."""

from __future__ import annotations

import os

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from . import service

router = APIRouter(prefix="/api/blog", tags=["blog"])


@router.post("/articles")
async def create_article(body: dict):
    article = service.create_article(
        body.get("title", "Untitled"), body.get("content_md", ""),
        body.get("category", ""), body.get("author", ""), body.get("tags", ""), body.get("published", False),
    )
    return {"article": article}


@router.get("/articles")
async def list_articles(category: str | None = None, published: bool | None = None):
    return {"articles": service.list_articles(category, published)}


@router.get("/articles/{article_id}")
async def get_article(article_id: int):
    a = service.get_article(article_id)
    if not a:
        raise HTTPException(status_code=404, detail="Article not found")
    a["content_html"] = service.render_markdown(a["content_md"])
    return {"article": a}


@router.put("/articles/{article_id}")
async def update_article(article_id: int, body: dict):
    a = service.update_article(article_id, body)
    if not a:
        raise HTTPException(status_code=404, detail="Article not found")
    return {"article": a}


@router.get("/rss")
async def rss_feed():
    site_url = os.environ.get("SITE_URL", "http://localhost:3000")
    title = os.environ.get("BLOG_TITLE", "Blog")
    desc = os.environ.get("BLOG_DESCRIPTION", "")
    xml = service.generate_rss(site_url, title, desc)
    return Response(content=xml, media_type="application/rss+xml")


@router.get("/categories")
async def list_categories():
    return {"categories": service.get_categories()}
