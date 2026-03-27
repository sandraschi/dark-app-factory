# Full Auto Deployment: Gap Analysis & Roadmap

**Question**: Can Dark App Factory do the complete web setup — HTTPS site, Austrian registrar, Hetzner host — fully automatic?

**Short answer**: **Phase 1 done.** The factory now outputs deploy artifacts (`deploy.sh`, `deploy_config.example.yaml`, `docker-compose.prod.yml`, `nginx.conf`). User runs `deploy.sh` with API keys for Hetzner/INWX. Phases 2–3 (meta-mcp integration, auto domain registration) are planned.

**Last Updated**: 2026-02-11

---

## What Dark Factory Does Today

| Output | Status |
|--------|--------|
| App code (backend, frontend) | Done |
| `www/index.html` landing page | Done |
| `Dockerfile` | Done |
| `requirements.txt` / `package.json` | Done |
| Marketing kit (press, blog, social) | Done |
| **Phase 1 deploy artifacts** | **Done** |
| `deploy.sh` | Done |
| `deploy_config.example.yaml` | Done |
| `docker-compose.prod.yml` | Done (if missing) |
| `nginx.conf` | Done (template) |

---

## What's Missing for Full Auto

| Step | Current | Needed |
|------|---------|--------|
| Domain | None | Registrar API (nic.at, INWX, Cloudflare) |
| DNS | None | DNS API (typically bundled with registrar) |
| Hosting | None | Hetzner / DigitalOcean / etc. API |
| SSL/HTTPS | None | Let's Encrypt + Certbot or Cloudflare |
| Deploy | None | SSH + Docker, or CI/CD (GitHub Actions) |

---

## Austrian Domain Options

### nic.at (Official .at Registry)

- **Direct**: No public API for end users. EPP protocol for accredited registrars only.
- **Resellers**: Must use a registrar (INWX, Strato, Ionos, etc.) that talks to nic.at.

### INWX (Recommended for Automation)

- **API**: XML-RPC and JSON-RPC. Python, Node, PHP libs.
- **.at price**: ~€12–15/year.
- **Docs**: https://www.inwx.com/en/help/apidoc/
- **Test system**: ote.inwx.com for sandbox.

### Alternative: Cloudflare Registrar

- **API**: Full REST API.
- **.at**: Cloudflare doesn't sell .at directly; use .com, .de, .io.
- **DNS + SSL**: Bundled, free, trivial to automate.

### Free Subdomain Fallback

- **FreeDNS** (afraid.org): Free subdomains like `myapp.mooo.com`.
- **Cloudflare Tunnel**: Free hostname routing, no domain needed (they assign one).
- **Firebase Hosting**: Free subdomain `yourapp.web.app`, auto SSL.

---

## Hosting Options

### Hetzner Cloud (EU, Cheap)

- **API**: Full REST. Python lib: `hcloud`.
- **Price**: CX11 ~€4/mo, CX21 ~€6/mo.
- **Flow**: Create server -> SSH -> install Docker -> deploy.

### DigitalOcean, Linode, Vultr

- Similar API-first provisioning.
- Slightly higher price than Hetzner.

### Static Hosting (If App Is Static)

- **Cloudflare Pages**: Free, Git push to deploy.
- **Vercel, Netlify**: Free tier, connect repo.
- **Firebase Hosting**: Free.

---

## SSL/HTTPS

| Method | Automation |
|--------|------------|
| **Let's Encrypt + Certbot** | Scriptable. Certbot standalone or nginx plugin. |
| **Cloudflare** | Free SSL, automatic if DNS via Cloudflare. |
| **Firebase / Vercel / Netlify** | Built-in, zero config. |

---

## Full Auto Flow (Target)

```
vibe.md  -->  factory run  -->  output_001/
                                    |
                                    v
                    [NEW: Deploy specialist or post-step]
                                    |
          +-------------------------+-------------------------+
          v                         v                         v
   Domain (INWX API)          Server (Hetzner API)      DNS (INWX/Cloudflare)
   - register domain          - create CX11             - point domain -> server IP
   - or use free subdomain    - install Docker          - or Cloudflare proxy
          |                         |
          +-------------------------+
                                    v
                            SSL (Certbot or Cloudflare)
                                    |
                                    v
                            Deploy (Docker run, or static deploy)
                                    |
                                    v
                            https://client-app.at  LIVE
```

---

## Implementation Options

### A. New Factory Step: `deploy`

Add a `deploy` subcommand or factory step that:

1. Reads config: `deploy_config.yaml` (domain provider, hoster, credentials)
2. Calls INWX API to register domain (or skips if free subdomain)
3. Calls Hetzner API to create server
4. SSHs into server, installs Docker, copies output, runs container
5. Runs Certbot or configures Cloudflare
6. Returns live URL

**Requires**: New specialist or `scripts/deploy.py`. Credentials (API keys) from user. Not in the vibe — user provides deploy config separately.

### B. meta-mcp Tools

meta-mcp could expose:

- `deploy_hetzner_server(spec)`
- `register_domain_inwx(domain, contact)`
- `deploy_static_to_cloudflare(site_dir)`

Factory would call these via MCP after build. User configures meta-mcp with API keys.

### C. GitHub Actions + Secrets

- Factory runs locally or in CI.
- Output pushed to GitHub.
- GitHub Action: deploy to Vercel/Firebase/Cloudflare Pages (all have free tiers, Connect repo).
- Domain: manual or separate script. For MVP, `*.vercel.app` or `*.web.app` is enough.

### D. "Deployer" Specialist

A new specialist that generates:

- `deploy.sh` (Hetzner + Certbot script)
- `docker-compose.prod.yml`
- `nginx.conf` with SSL
- `deploy_config.example.yaml`

User runs the script with their API keys. Not fully automatic, but one command for user.

---

## Phase 1 Usage (Implemented)

1. Run the factory. Output contains `deploy.sh`, `deploy_config.example.yaml`, `docker-compose.prod.yml`, `nginx.conf`.
2. Copy `deploy_config.example.yaml` to `deploy_config.yaml`, fill in Hetzner/INWX API keys (optional for minimal deploy).
3. Copy the output directory to your Hetzner server (scp/rsync).
4. SSH into the server, run `./deploy.sh`. Script installs Docker if needed, builds and runs containers.
5. For SSL: run `certbot certonly --standalone -d yourdomain.at` and update nginx.conf, then reload nginx.

## Recommendation

**Phase 2**: Integrate with meta-mcp. Factory can optionally call `deploy_to_cloudflare_pages` or `deploy_to_hetzner` if user has configured meta-mcp with keys. No domain in Phase 2 — use free subdomain.

**Phase 3**: Add INWX (or Cloudflare) domain registration. Full flow: vibe -> app -> domain -> host -> HTTPS. User provides API keys once, everything else automatic.

---

## Austrian Small Company Context

For the €100/€300 business model:

- **€100 app**: Deploy could be "I host it for you on my Hetzner" — you run the deploy script, client gets `https://client-app.yourdomain.at` or similar. You eat the ~€6/mo cost or add hosting fee.
- **€300 factory**: User gets factory + support. Deploy is their problem, or you offer "I'll deploy your first app" as part of support.

---

## Summary

| Capability | Today | With Phase 1 | With Phase 2 | With Phase 3 |
|------------|-------|--------------|--------------|--------------|
| Generate app | Yes | Yes | Yes | Yes |
| Deploy script | No | Yes | Yes | Yes |
| Auto Hetzner | No | No | Optional | Yes |
| Auto domain | No | No | No | Yes (INWX) |
| HTTPS | No | Manual | Auto (Cloudflare) | Auto |
| Full auto | No | No | Partial | Yes |
