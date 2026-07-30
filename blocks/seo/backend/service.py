"""SEO service — sitemap, robots.txt, JSON-LD, redirects."""

from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import Any

logger = logging.getLogger("dark_factory")

_redirects: list[dict] = []
_routes: list[str] = []


def add_route(path: str):
    if path not in _routes:
        _routes.append(path)


def set_routes(routes: list[str]):
    global _routes
    _routes = routes


def generate_sitemap(site_url: str) -> str:
    urls = "\n".join(f"  <url><loc>{site_url.rstrip('/')}{r}</loc></url>" for r in _routes)
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls}\n</urlset>'


def generate_robots(site_url: str) -> str:
    return f"User-agent: *\nAllow: /\nSitemap: {site_url.rstrip('/')}/api/seo/sitemap.xml\n"


def generate_json_ld(org_name: str, url: str, description: str = "", logo: str = "") -> dict:
    ld = {"@context": "https://schema.org", "@type": "Organization", "name": org_name, "url": url}
    if description: ld["description"] = description
    if logo: ld["logo"] = logo
    return ld


def add_redirect(source: str, target: str, code: int = 301) -> dict:
    r = {"source": source, "target": target, "code": code}
    _redirects.append(r)
    return r


def resolve_redirect(path: str) -> dict | None:
    for r in _redirects:
        if r["source"] == path:
            return r
    return None


def get_settings() -> dict:
    return {"title": os.environ.get("SEO_TITLE", ""), "description": os.environ.get("SEO_DESCRIPTION", ""), "image": os.environ.get("SEO_IMAGE", ""), "site_url": os.environ.get("SITE_URL", "http://localhost:3000")}
