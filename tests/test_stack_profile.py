"""Tests for src/utils/stack_profile.py -- pure logic, no LLM needed."""

import json

from src.utils.stack_profile import (
    DEFAULT_STACK,
    parse_stack_from_vibe,
    embed_in_specs,
    extract_from_specs,
    is_python_backend,
    is_node_backend,
    has_frontend,
    is_react_frontend,
    describe_stack,
)


class TestParseStackFromVibe:
    def test_default_stack_when_empty(self):
        result = parse_stack_from_vibe("")
        assert result == DEFAULT_STACK

    def test_explicit_python_fastapi(self):
        vibe = """## Tech Stack
- **Backend**: python/fastapi
- **Frontend**: react
- **Database**: postgresql
"""
        result = parse_stack_from_vibe(vibe)
        assert result["backend"] == "python/fastapi"
        assert result["frontend"] == "react"
        assert result["database"] == "postgresql"

    def test_invalid_backend_falls_back(self):
        vibe = "- **Backend**: ruby/rails"
        result = parse_stack_from_vibe(vibe)
        assert result["backend"] == DEFAULT_STACK["backend"]

    def test_partial_vibe_uses_defaults(self):
        vibe = "- **Backend**: python/flask"
        result = parse_stack_from_vibe(vibe)
        assert result["backend"] == "python/flask"
        assert result["frontend"] == DEFAULT_STACK["frontend"]
        assert result["database"] == DEFAULT_STACK["database"]

    def test_no_frontend(self):
        vibe = "- **Frontend**: none"
        result = parse_stack_from_vibe(vibe)
        assert result["frontend"] == "none"


class TestEmbedAndExtract:
    def test_roundtrip(self):
        profile = {
            "backend": "python/fastapi",
            "frontend": "htmx",
            "database": "sqlite",
        }
        specs = "# My App\nSome specs here."
        embedded = embed_in_specs(specs, profile)
        extracted = extract_from_specs(embedded)
        assert extracted == profile

    def test_extract_missing_returns_default(self):
        specs = "# My App\nNo stack profile here."
        result = extract_from_specs(specs)
        assert result == DEFAULT_STACK

    def test_embed_format(self):
        profile = {"backend": "node/express", "frontend": "react", "database": "sqlite"}
        embedded = embed_in_specs("specs", profile)
        assert "<!-- STACK_PROFILE:" in embedded
        assert json.dumps(profile) in embedded


class TestHelperFunctions:
    def test_is_python_backend(self):
        assert is_python_backend({"backend": "python/fastapi"}) is True
        assert is_python_backend({"backend": "python/flask"}) is True
        assert is_python_backend({"backend": "node/express"}) is False

    def test_is_node_backend(self):
        assert is_node_backend({"backend": "node/express"}) is True
        assert is_node_backend({"backend": "python/fastapi"}) is False

    def test_has_frontend(self):
        assert has_frontend({"frontend": "react"}) is True
        assert has_frontend({"frontend": "none"}) is False

    def test_is_react_frontend(self):
        assert is_react_frontend({"frontend": "react"}) is True
        assert is_react_frontend({"frontend": "svelte"}) is False


class TestDescribeStack:
    def test_python_fastapi_react(self):
        desc = describe_stack(
            {"backend": "python/fastapi", "frontend": "react", "database": "postgresql"}
        )
        assert "FastAPI" in desc
        assert "React" in desc
        assert "PostgreSQL" in desc

    def test_node_express_none(self):
        desc = describe_stack(
            {"backend": "node/express", "frontend": "none", "database": "sqlite"}
        )
        assert "Express" in desc
        assert "API-only" in desc
        assert "SQLite" in desc
