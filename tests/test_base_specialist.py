"""Tests for src/specialists/base.py -- Specialist base class logic."""

import pytest
from typing import Dict, Any

from src.specialists.base import Specialist


class ConcreteSpecialist(Specialist):
    """Minimal concrete implementation for testing the ABC."""

    async def generate(
        self, file_path: str, specs: str, shared_context: Dict[str, Any], worker: Any
    ) -> str:
        return f"// generated {file_path}"


class TestCanHandle:
    def test_exact_match(self):
        spec = ConcreteSpecialist(name="Test", owned_patterns=["main.py", "app.py"])
        assert spec.can_handle("main.py") is True
        assert spec.can_handle("app.py") is True
        assert spec.can_handle("server.js") is False

    def test_prefix_wildcard(self):
        spec = ConcreteSpecialist(name="Test", owned_patterns=["routes/*", "models/*"])
        assert spec.can_handle("routes/users.py") is True
        assert spec.can_handle("models/patient.js") is True
        assert spec.can_handle("components/Header.tsx") is False

    def test_empty_patterns(self):
        spec = ConcreteSpecialist(name="Test", owned_patterns=[])
        assert spec.can_handle("anything.py") is False


class TestGetDependencyContext:
    def test_no_requires(self):
        spec = ConcreteSpecialist(name="Test", owned_patterns=[], requires=[])
        assert spec.get_dependency_context({}) == ""

    def test_with_upstream_output(self):
        spec = ConcreteSpecialist(
            name="Test", owned_patterns=[], requires=["Plumber"]
        )
        context = {
            "Plumber": {
                "main.py": "from fastapi import FastAPI\napp = FastAPI()"
            }
        }
        result = spec.get_dependency_context(context)
        assert "Plumber/main.py" in result
        assert "FastAPI" in result

    def test_missing_upstream_returns_empty(self):
        spec = ConcreteSpecialist(
            name="Test", owned_patterns=[], requires=["Missing"]
        )
        result = spec.get_dependency_context({})
        assert result == ""

    def test_context_truncation(self):
        spec = ConcreteSpecialist(
            name="Test", owned_patterns=[], requires=["Big"]
        )
        huge_code = "x" * 20000
        context = {"Big": {"huge.py": huge_code}}
        result = spec.get_dependency_context(context)
        assert len(result) <= 8000


class TestValidate:
    def test_default_always_valid(self):
        spec = ConcreteSpecialist(name="Test", owned_patterns=[])
        is_valid, error = spec.validate("any.py", "code", "specs")
        assert is_valid is True
        assert error == ""


class TestDeclareFiles:
    def test_default_no_files(self):
        spec = ConcreteSpecialist(name="Test", owned_patterns=[])
        assert spec.declare_files("specs", {}) == []


class TestTemperature:
    def test_default_temperature(self):
        spec = ConcreteSpecialist(name="Test", owned_patterns=[])
        assert spec.temperature == 0.2

    def test_custom_temperature(self):
        spec = ConcreteSpecialist(name="Test", owned_patterns=[], temperature=0.8)
        assert spec.temperature == 0.8
