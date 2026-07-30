# Hosting Block

Website hosting and deployment — Dockerfile, nginx config, SSL setup, systemd service, health monitoring, and domain DNS guide.

**Triggers**: hosting, deploy, docker, nginx, ssl, domain, dns, cloud, server, production, cpanel, vps

**Env vars**:
| Variable | Default | Description |
|----------|---------|-------------|
| `DOMAIN` | `example.com` | Deployment domain |
| `ADMIN_EMAIL` | `admin@example.com` | Admin contact for SSL |
| `HOSTING_PLATFORM` | `docker` | Platform: `docker` or `vps` |

**API endpoints**: `/api/hosting/status`, `/api/hosting/config`, `/api/health`

**Dependencies**: (none)
