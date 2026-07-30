"""Tests for seo block."""
from __future__ import annotations

class TestSeo:
    def test_sitemap(self):
        from blocks.seo.backend import service as s
        s.set_routes(["/", "/services", "/contact"])
        xml = s.generate_sitemap("http://example.com")
        assert "/services" in xml
        assert "sitemap" in xml

    def test_robots(self):
        from blocks.seo.backend import service as s
        txt = s.generate_robots("http://example.com")
        assert "Sitemap" in txt

    def test_json_ld(self):
        from blocks.seo.backend import service as s
        ld = s.generate_json_ld("Test Org", "http://test.com", "A test", "http://test.com/logo.png")
        assert ld["@type"] == "Organization"
        assert ld["name"] == "Test Org"

    def test_redirects(self):
        from blocks.seo.backend import service as s
        s.add_redirect("/old", "/new", 301)
        r = s.resolve_redirect("/old")
        assert r is not None
        assert r["target"] == "/new"
