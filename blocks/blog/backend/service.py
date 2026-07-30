"""Blog/CMS service — articles, categories, RSS, Markdown rendering."""

from __future__ import annotations

import logging
import os
import re
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("dark_factory")

_articles: list[dict] = []
_categories: set[str] = set()
_next_id = 1


def create_article(title: str, content_md: str, category: str = "", author: str = "", tags: str = "", published: bool = False) -> dict:
    global _next_id
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    article = {
        "id": _next_id, "title": title, "slug": slug, "content_md": content_md,
        "category": category, "author": author or "Admin", "tags": tags.split(",") if tags else [],
        "published": published, "views": 0,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    _articles.append(article)
    _next_id += 1
    if category:
        _categories.add(category)
    return article


def list_articles(category: str | None = None, published: bool | None = None) -> list[dict]:
    results = _articles
    if category:
        results = [a for a in results if a["category"] == category]
    if published is True:
        results = [a for a in results if a["published"]]
    return list(reversed(results))


def get_article(article_id: int) -> dict | None:
    a = next((a for a in _articles if a["id"] == article_id), None)
    if a:
        a["views"] = (a.get("views", 0) or 0) + 1
    return a


def get_article_by_slug(slug: str) -> dict | None:
    return next((a for a in _articles if a["slug"] == slug), None)


def update_article(article_id: int, updates: dict) -> dict | None:
    a = next((a for a in _articles if a["id"] == article_id), None)
    if not a:
        return None
    safe = {"title", "content_md", "category", "author", "tags", "published"}
    for k, v in updates.items():
        if k in safe:
            a[k] = v
    a["updated_at"] = datetime.now(timezone.utc).isoformat()
    if updates.get("category"):
        _categories.add(updates["category"])
    return a


def render_markdown(md: str) -> str:
    try:
        import markdown as md_lib
        return md_lib.markdown(md, extensions=["fenced_code", "codehilite", "tables"])
    except ImportError:
        return f"<pre>{md}</pre>"


def generate_rss(site_url: str, title: str, description: str) -> str:
    try:
        from feedgen.feed import FeedGenerator

        fg = FeedGenerator()
        fg.title(title)
        fg.description(description)
        fg.link(href=site_url, rel="self")
        for a in list_articles(published=True)[:20]:
            entry = fg.add_entry()
            entry.title(a["title"])
            entry.link(href=f"{site_url}/blog/{a['slug']}")
            entry.description(a["content_md"][:300])
            entry.pubDate(a["created_at"])
            entry.author(name=a["author"])
        return fg.rss_str(pretty=True).decode()
    except ImportError:
        return "<?xml version='1.0'?><rss version='2.0'><channel><title>Blog</title></channel></rss>"


def get_categories() -> list[str]:
    return sorted(_categories)
