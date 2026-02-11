# Dark App Factory: Monetization Plan

**Goal**: Make a bit of money from the factory. Two product legs, Austrian small-company setup, basic landing page.

**Last Updated**: 2026-02-09

---

## Product A: €100 "Make My App"

**Offer**: "Describe your app. I build it. You get a working web app."

**Target**: Austrian small businesses — dentist, beekeeper, local shop, Verein. Non-tech, budget-conscious.

**Delivery**:
- Working app (zip or hosted)
- Landing page (from Propagandist)
- Basic docs (README)

**Scope control**: "One domain, one main purpose." Vibe must be clear. Over-scope = "that's a custom project, different price."

**Hosting**: You host on your Hetzner (~€6/mo) or deliver zip. Client runs locally if they have tech.

---

## Product B: €300 "Dark Factory + Support"

**Offer**: "You get the factory. I help you run it. Build as many apps as you want."

**Target**: Non-tech but adventurous. Wants to tinker, learn, build their own.

**Challenge**: "GitHub? Repo? What?" — they don't know these terms.

**Delivery**:
- **ZIP download** — packaged repo, no Git required. Or use GitHub Releases "Download ZIP."
- **One-page guide** — "1. Extract. 2. Run install.bat. 3. Edit vibe.md. 4. Run build.bat."
- **Support** — 2–3 email exchanges, or 1 video call (30 min).

**Packaging for non-tech**:
- `dark-factory-portable.zip` — everything pre-installed if possible, or minimal "run this installer."
- `install.bat` / `start.bat` — double-click to run. No terminal commands.
- Default env: `WORKER_BASE_URL` pointing to your goliath (or a shared demo server)? That would require you to run a public Ollama, which is a cost. Alternative: user must have Tailscale + their own goliath, or run Ollama locally (7B CPU mode). Document both paths.

---

## Austrian Small Company Setup

**Research needed** (Steuerberater recommended):

| Topic | Notes |
|-------|-------|
| **Rechtsform** | Einzelunternehmen for small volume. GmbH if scaling. |
| **Gewerbe** | Software development, consulting — check if Gewerbe required. |
| **Kleinunternehmer** | If turnover < €35k/year, simplified VAT (no Umsatzsteuer). |
| **Payment** | Stripe, PayPal, SEPA. Rechnung for B2B. |
| **Domain** | nic.at, INWX for .at. Or use your existing domain. |

**Costs**: Steuerberater ~€100–200 for setup consultation. Gewerbe registration often free or low.

---

## Landing Page (meta-mcp)

**Use meta-mcp landing page builder** to create a basic site.

**Content**:
- **Hero**: "Apps from vibes. No API costs. Built for Austrian small business."
- **Product A**: €100 — "I build your app from your idea."
- **Product B**: €300 — "Dark Factory + support. Build your own apps."
- **Optional**: "Remote setup" — +€50, you configure Tailscale + goliath for them.
- **Contact**: Email, Calendly, or simple form.

**Hosting**: GitHub Pages (free), or deploy the generated landing page to Cloudflare Pages / Vercel.

---

## Full Auto Deployment (Future)

See [FULL_AUTO_DEPLOYMENT.md](FULL_AUTO_DEPLOYMENT.md).

**Today**: Factory generates app. You deploy manually (or client runs locally).

**Phase 1**: Factory outputs `deploy.sh` + config. One script, user runs with API keys.

**Phase 2**: meta-mcp deploy tools. Optional auto-deploy to Hetzner/Cloudflare.

**Phase 3**: Full auto — domain (INWX) + Hetzner + HTTPS. User provides keys once.

For €100 app: You run deploy. Could use Phase 1 script. Your Hetzner, your domain reseller.

---

## Action Items

1. **Landing page**: Use meta-mcp to generate. Host on GitHub Pages or similar.
2. **Austrian setup**: Consult Steuerberater. Register Gewerbe if needed.
3. **Product A packaging**: Define scope, create order form or simple process.
4. **Product B packaging**: Create `dark-factory-portable.zip` with install.bat, one-page guide.
5. **Deploy script**: Add Phase 1 from FULL_AUTO_DEPLOYMENT — `deploy.sh` + example config.
