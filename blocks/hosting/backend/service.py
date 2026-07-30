"""Hosting service — deployment config generation, health monitoring."""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("dark_factory")

_start_time = datetime.now(timezone.utc)


def get_domain() -> str:
    return os.environ.get("DOMAIN", "example.com")


def get_admin_email() -> str:
    return os.environ.get("ADMIN_EMAIL", "admin@example.com")


def get_platform() -> str:
    return os.environ.get("HOSTING_PLATFORM", "docker")


def get_status() -> dict:
    return {
        "domain": get_domain(),
        "platform": get_platform(),
        "uptime_seconds": int((datetime.now(timezone.utc) - _start_time).total_seconds()),
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def generate_docker_compose(domain: str, app_port: int = 8000) -> str:
    return f"""version: '3.8'
services:
  app:
    build: .
    restart: unless-stopped
    ports:
      - "{app_port}:{app_port}"
    environment:
      - DOMAIN={domain}
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:{app_port}/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./data/certbot/conf:/etc/letsencrypt
      - ./data/certbot/www:/var/www/certbot
    depends_on:
      - app

  certbot:
    image: certbot/certbot
    volumes:
      - ./data/certbot/conf:/etc/letsencrypt
      - ./data/certbot/www:/var/www/certbot
    entrypoint: "/bin/sh -c 'trap exit TERM; while :; do certbot renew; sleep 12h & wait; done'"
"""


def generate_nginx_config(domain: str, app_port: int = 8000) -> str:
    return f"""events {{}}

http {{
    upstream app {{
        server app:{app_port};
    }}

    server {{
        listen 80;
        server_name {domain} www.{domain};
        return 301 https://$server_name$request_uri;
    }}

    server {{
        listen 443 ssl;
        server_name {domain} www.{domain};

        ssl_certificate /etc/letsencrypt/live/{domain}/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/{domain}/privkey.pem;

        location / {{
            proxy_pass http://app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }}

        location /api/health {{
            proxy_pass http://app;
            proxy_set_header Host $host;
        }}
    }}
}}
"""


def generate_dockerfile(app_port: int = 8000) -> str:
    return f"""FROM python:3.13-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

EXPOSE {app_port}
CMD ["uvicorn", "web.server:app", "--host", "0.0.0.0", "--port", str(app_port)]
"""


def generate_systemd_service(domain: str, app_dir: str, user: str = "www-data") -> str:
    return f"""[Unit]
Description={domain} web app
After=network.target

[Service]
Type=simple
User={user}
WorkingDirectory={app_dir}
ExecStart=/usr/local/bin/uv run uvicorn web.server:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=5
Environment=DOMAIN={domain}

[Install]
WantedBy=multi-user.target
"""
