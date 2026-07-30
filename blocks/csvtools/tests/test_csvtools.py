"""Tests for csvtools block."""
from __future__ import annotations

class TestCsvTools:
    def test_export(self):
        from blocks.csvtools.backend import service as s
        data = [{"name": "Alice", "email": "a@b.com"}, {"name": "Bob", "email": "b@b.com"}]
        csv_str = s.export_csv(data)
        assert "Alice" in csv_str
        assert "Bob" in csv_str

    def test_import(self):
        from blocks.csvtools.backend import service as s
        result = s.import_csv("name,email\nAlice,a@b.com\nBob,b@b.com\n")
        assert result["rows"] == 2
        assert result["headers"] == ["name", "email"]

    def test_detect_schema(self):
        from blocks.csvtools.backend import service as s
        schema = s.detect_schema([{"name": "Alice", "age": 30}])
        assert len(schema) == 2

    def test_generate_template(self):
        from blocks.csvtools.backend import service as s
        tmpl = s.generate_template(["name", "email", "phone"])
        assert "name,email,phone" in tmpl
