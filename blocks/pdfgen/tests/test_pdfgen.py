"""Tests for pdfgen block."""
from __future__ import annotations
import pytest

class TestPdfGen:
    def test_invoice_html(self):
        from blocks.pdfgen.backend import service as s
        result = s._default_invoice_html([{"description": "Widget", "qty": 2, "price": 10, "total": 20}], "INV-001", "2026-07-30", "ACME Inc", "Bob")
        assert "INV-001" in result
        assert "ACME Inc" in result
        assert "$20.00" in result

    @pytest.mark.asyncio
    async def test_generate_from_html_no_weasyprint(self):
        import os, tempfile
        os.environ.pop("PDF_STORAGE", None)
        from blocks.pdfgen.backend import service as s
        s.PDF_DIR = tempfile.mkdtemp()
        result = await s.generate_from_html("<p>Test</p>")
        assert result is not None
