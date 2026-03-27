"""Generate deploy artifacts (deploy.sh, deploy_config.example.yaml, etc.) into output_dir."""

import os
from src.utils.logger import logger


def _detect_stack(output_dir: str) -> dict:
    """Detect app stack from output directory."""
    has_requirements = os.path.exists(os.path.join(output_dir, "requirements.txt"))
    has_main_py = os.path.exists(os.path.join(output_dir, "main.py"))
    has_app_py = os.path.exists(os.path.join(output_dir, "app.py"))
    has_package_json = os.path.exists(os.path.join(output_dir, "package.json"))
    has_dockerfile = os.path.exists(os.path.join(output_dir, "Dockerfile"))

    is_python = has_requirements or has_main_py or has_app_py
    is_node = bool(has_package_json)
    is_hybrid = is_python and is_node

    return {
        "is_python": is_python,
        "is_node": is_node,
        "is_hybrid": is_hybrid,
        "has_dockerfile": has_dockerfile,
    }


DEPLOY_CONFIG_EXAMPLE = """# Deploy configuration -- copy to deploy_config.yaml and fill in.
# Used by deploy.sh for Hetzner + INWX + SSL automation.

# Domain (optional; omit for IP-only or free subdomain)
domain: ""
# domain: "myapp.at"

# INWX (registrar/DNS) -- https://www.inwx.com/en/help/apidoc/
inwx:
  enabled: false
  username: ""
  password: ""
  # Test system: ote.inwx.com

# Hetzner Cloud -- https://docs.hetzner.com/cloud/
hetzner:
  api_token: ""
  server_name: "dark-app-prod"
  server_type: "cx11"  # ~EUR 4/mo
  image: "ubuntu-24.04"
  location: "nbg1"  # Nuremberg

# SSH (for deploy.sh when run from your machine)
ssh:
  key_path: "~/.ssh/id_rsa"
  user: "root"

# SSL (Let's Encrypt via Certbot)
ssl:
  email: ""  # Required for Let's Encrypt
  use_staging: true  # Set false for production certs
"""


DEPLOY_SH = """#!/bin/bash
# Deploy script for Dark App Factory output.
# Run on the target server after copying this directory.
# Requires: Docker, docker-compose. Optionally: Certbot for SSL.

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Load config if present
CONFIG="$SCRIPT_DIR/deploy_config.yaml"
if [ -f "$CONFIG" ]; then
  echo "[INFO] Using $CONFIG"
else
  echo "[WARN] No deploy_config.yaml. Copy deploy_config.example.yaml and fill in."
fi

# Ensure Docker
if ! command -v docker &> /dev/null; then
  echo "[INFO] Installing Docker..."
  curl -fsSL https://get.docker.com | sh
  systemctl enable docker
  systemctl start docker
fi

# Build and run
if [ -f "docker-compose.prod.yml" ]; then
  docker compose -f docker-compose.prod.yml build --no-cache
  docker compose -f docker-compose.prod.yml up -d
  echo "[SUCCESS] App running via docker-compose.prod.yml"
elif [ -f "Dockerfile" ]; then
  docker build -t dark-app .
  docker run -d -p 80:8000 --name dark-app dark-app
  echo "[SUCCESS] App running on port 80"
else
  echo "[ERROR] No Dockerfile or docker-compose.prod.yml found."
  exit 1
fi

# SSL (optional, if domain and certbot available)
if [ -f "$CONFIG" ] && command -v certbot &> /dev/null; then
  DOMAIN=$(grep -E "^domain:" "$CONFIG" 2>/dev/null | sed 's/domain:\\s*"\\?\\([^"]*\\)"\\?/\\1/' | tr -d ' ')
  if [ -n "$DOMAIN" ]; then
    echo "[INFO] Consider: certbot certonly --standalone -d $DOMAIN"
  fi
fi
"""


DOCKER_COMPOSE_PROD = """# Production docker-compose for Dark App Factory output.
# Usage: docker compose -f docker-compose.prod.yml up -d

services:
  app:
    build: .
    ports:
      - "8000:8000"
    restart: unless-stopped
    environment:
      - PORT=8000
"""


NGINX_CONF = """# Nginx reverse proxy + SSL (place in /etc/nginx/sites-available/ or similar).
# Replace DOMAIN and CERT_PATH as needed.

server {
    listen 80;
    server_name DOMAIN;
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# SSL block (after certbot)
# server {
#     listen 443 ssl;
#     server_name DOMAIN;
#     ssl_certificate /etc/letsencrypt/live/DOMAIN/fullchain.pem;
#     ssl_certificate_key /etc/letsencrypt/live/DOMAIN/privkey.pem;
#     location / {
#         proxy_pass http://127.0.0.1:8000;
#         proxy_set_header Host $host;
#         proxy_set_header X-Real-IP $remote_addr;
#         proxy_set_header X-Forwarded-Proto https;
#     }
# }
"""


def generate_deploy_artifacts(output_dir: str) -> list[str]:
    """Generate deploy artifacts into output_dir.

    Writes:
    - deploy_config.example.yaml
    - deploy.sh
    - docker-compose.prod.yml (if not present)
    - nginx.conf (optional reverse-proxy template)

    Returns list of paths written.
    """
    written: list[str] = []
    stack = _detect_stack(output_dir)

    # deploy_config.example.yaml
    config_path = os.path.join(output_dir, "deploy_config.example.yaml")
    try:
        with open(config_path, "w", encoding="utf-8") as f:
            f.write(DEPLOY_CONFIG_EXAMPLE)
        written.append(config_path)
    except OSError as e:
        logger.warning("Could not write deploy_config.example.yaml: %s", e)

    # deploy.sh
    sh_path = os.path.join(output_dir, "deploy.sh")
    try:
        with open(sh_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(DEPLOY_SH)
        os.chmod(sh_path, 0o755)
        written.append(sh_path)
    except OSError as e:
        logger.warning("Could not write deploy.sh: %s", e)

    # docker-compose.prod.yml (only if missing)
    compose_path = os.path.join(output_dir, "docker-compose.prod.yml")
    if not os.path.exists(compose_path):
        try:
            with open(compose_path, "w", encoding="utf-8") as f:
                f.write(DOCKER_COMPOSE_PROD)
            written.append(compose_path)
        except OSError as e:
            logger.warning("Could not write docker-compose.prod.yml: %s", e)
    else:
        logger.debug("docker-compose.prod.yml exists, skipping")

    # nginx.conf (always write as template)
    nginx_path = os.path.join(output_dir, "nginx.conf")
    try:
        with open(nginx_path, "w", encoding="utf-8") as f:
            f.write(NGINX_CONF)
        written.append(nginx_path)
    except OSError as e:
        logger.warning("Could not write nginx.conf: %s", e)

    if written:
        logger.info("Deploy artifacts written: %s", ", ".join(os.path.basename(p) for p in written))

    return written
