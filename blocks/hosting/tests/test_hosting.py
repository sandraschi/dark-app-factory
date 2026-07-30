"""Tests for hosting block."""

from __future__ import annotations

import pytest


class TestHosting:
    def test_status(self):
        from blocks.hosting.backend import service as s
        status = s.get_status()
        assert status["status"] == "ok"
        assert "uptime_seconds" in status

    def test_docker_compose(self):
        from blocks.hosting.backend import service as s
        compose = s.generate_docker_compose("example.com")
        assert "example.com" in compose
        assert "nginx:" in compose
        assert "certbot:" in compose

    def test_nginx_config(self):
        from blocks.hosting.backend import service as s
        conf = s.generate_nginx_config("example.com")
        assert "example.com" in conf
        assert "ssl_certificate" in conf

    def test_dockerfile(self):
        from blocks.hosting.backend import service as s
        df = s.generate_dockerfile(8000)
        assert "uvicorn" in df
        assert "8000" in df

    def test_systemd_service(self):
        from blocks.hosting.backend import service as s
        svc = s.generate_systemd_service("app.example.com", "/opt/app")
        assert "app.example.com" in svc
        assert "/opt/app" in svc
