"""PDF generation service — HTML to PDF, invoices, reports."""

from __future__ import annotations

import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("dark_factory")

PDF_DIR = Path(os.environ.get("PDF_STORAGE", "data/pdfs"))
PDF_DIR.mkdir(parents=True, exist_ok=True)

TEMPLATES: dict[str, str] = {}


def register_template(name: str, html: str):
    TEMPLATES[name] = html


def _default_invoice_html(items: list[dict], number: str, date: str, company: str, customer: str) -> str:
    rows = "\n".join(f"<tr><td>{i['description']}</td><td>{i['qty']}</td><td>${i['price']:.2f}</td><td>${i['total']:.2f}</td></tr>" for i in items)
    total = sum(i["total"] for i in items)
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
body {{ font-family: 'Helvetica', sans-serif; padding: 2cm; color: #333; }}
h1 {{ color: #111; font-size: 24px; }}
table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
th, td {{ padding: 8px 12px; text-align: left; border-bottom: 1px solid #ddd; }}
th {{ background: #f5f5f5; }}
.total {{ font-size: 18px; font-weight: bold; text-align: right; margin-top: 20px; }}
.footer {{ margin-top: 40px; font-size: 12px; color: #999; }}
</style></head><body>
<h1>Invoice #{number}</h1>
<p><strong>From:</strong> {company}<br><strong>To:</strong> {customer}<br><strong>Date:</strong> {date}</p>
<table><thead><tr><th>Description</th><th>Qty</th><th>Price</th><th>Total</th></tr></thead><tbody>{rows}</tbody></table>
<div class="total">Total: ${total:.2f}</div>
<div class="footer">Thank you for your business.</div>
</body></html>"""


async def generate_invoice(items: list[dict], company: str = "", customer: str = "", number: str = "") -> dict:
    try:
        from weasyprint import HTML as WeasyPrint

        number = number or f"INV-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        html = _default_invoice_html(items, number, datetime.now().strftime("%Y-%m-%d"), company, customer)
        file_id = str(uuid.uuid4())
        path = PDF_DIR / f"{file_id}.pdf"
        WeasyPrint(string=html).write_pdf(path)
        return {"id": file_id, "filename": f"invoice-{number}.pdf", "path": str(path), "pages": 1, "number": number}
    except ImportError:
        return {"error": "weasyprint not installed — install with: pip install weasyprint"}


async def generate_from_html(html: str, filename: str = "document.pdf") -> dict:
    try:
        from weasyprint import HTML as WeasyPrint

        file_id = str(uuid.uuid4())
        path = PDF_DIR / f"{file_id}.pdf"
        WeasyPrint(string=html).write_pdf(path)
        return {"id": file_id, "filename": filename, "path": str(path)}
    except ImportError:
        return {"error": "weasyprint not installed"}
