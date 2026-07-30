"""Hosting FastAPI routes — status, config."""

from __future__ import annotations

from fastapi import APIRouter

from . import service

router = APIRouter(prefix="/api/hosting", tags=["hosting"])


@router.get("/status")
async def get_status():
    return service.get_status()


@router.get("/config")
async def get_config():
    domain = service.get_domain()
    return {
        "domain": domain,
        "platform": service.get_platform(),
        "docker_compose": service.generate_docker_compose(domain),
        "nginx": service.generate_nginx_config(domain),
        "systemd": service.generate_systemd_service(domain, "/opt/app"),
    }


@router.get("/health")
async def health():
    return service.get_status()
