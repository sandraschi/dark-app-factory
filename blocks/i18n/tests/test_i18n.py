"""Tests for i18n block."""
from __future__ import annotations
import pytest

class TestI18n:
    def test_translation_roundtrip(self):
        from blocks.i18n.backend import service as s
        s.set_translation("de", "hello", "Hallo")
        s.set_translation("de", "goodbye", "Tschüss")
        t = s.get_translations("de")
        assert t["hello"] == "Hallo"

    def test_translate_fallback(self):
        from blocks.i18n.backend import service as s
        s.set_translation("en", "hello", "Hello")
        assert s.translate("hello", "fr") == "Hello"

    def test_bulk_import(self):
        from blocks.i18n.backend import service as s
        count = s.bulk_import("fr", {"yes": "oui", "no": "non"})
        assert count == 2
