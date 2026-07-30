"""Tests for blog block."""
from __future__ import annotations
import pytest
@pytest.fixture(autouse=True)
def reset():
    from blocks.blog.backend import service as s
    s._articles.clear(); s._categories.clear(); s._next_id = 1

class TestBlog:
    def test_create_article(self):
        from blocks.blog.backend import service as s
        a = s.create_article("Hello", "World", "tech", "Alice", "news", True)
        assert a["title"] == "Hello"
        assert a["slug"] == "hello"
        assert len(s.list_articles(published=True)) == 1

    def test_list_by_category(self):
        from blocks.blog.backend import service as s
        s.create_article("A", "a", "tech")
        s.create_article("B", "b", "design")
        assert len(s.list_articles("tech")) == 1

    def test_get_article(self):
        from blocks.blog.backend import service as s
        s.create_article("Test", "Content")
        a = s.get_article(1)
        assert a is not None
        assert a["title"] == "Test"

    def test_markdown_rendering(self):
        from blocks.blog.backend import service as s
        html = s.render_markdown("# Hello\n**bold**")
        assert html is not None

    def test_rss_generation(self):
        from blocks.blog.backend import service as s
        s.create_article("Post 1", "Content 1", published=True)
        xml = s.generate_rss("http://x.com", "Test Blog", "Desc")
        assert "<rss" in xml or "rss" in xml

    def test_categories(self):
        from blocks.blog.backend import service as s
        s.create_article("A", "a", "tech")
        assert "tech" in s.get_categories()
