"""CSV tools — import, export, schema detection, templates."""

from __future__ import annotations

import csv
import io
import logging
from datetime import datetime
from typing import Any

logger = logging.getLogger("dark_factory")


def export_csv(data: list[dict], fields: list[str] | None = None) -> str:
    if not data:
        return ""
    if fields is None:
        fields = list(data[0].keys())
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(data)
    return output.getvalue()


def import_csv(content: str, fields: list[str] | None = None) -> dict:
    reader = csv.DictReader(io.StringIO(content))
    rows = list(reader)
    if not rows:
        return {"error": "Empty CSV", "rows": 0}
    headers = list(rows[0].keys())
    if fields:
        missing = [f for f in fields if f not in headers]
        if missing:
            return {"error": f"Missing columns: {', '.join(missing)}", "rows": 0}
    return {"rows": len(rows), "headers": headers, "data": rows, "imported_at": datetime.now().isoformat()}


def detect_schema(data: list[dict]) -> list[dict]:
    schema: list[dict] = []
    for row in data:
        for key, val in row.items():
            existing = next((s for s in schema if s["field"] == key), None)
            if not existing:
                typ = "number" if isinstance(val, (int, float)) else "boolean" if isinstance(val, bool) else "text"
                schema.append({"field": key, "type": typ, "required": False})
    return schema


def generate_template(fields: list[str]) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(fields)
    writer.writerow([f"example_{f}" for f in fields])
    return output.getvalue()
