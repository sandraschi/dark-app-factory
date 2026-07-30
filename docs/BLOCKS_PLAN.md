# Blocks System — Plan

**Goal**: Turn DAF from "LLM writes every line from scratch" to "LLM assembles and configures pre-built modules." Each block is a tested, reusable package that the factory installs and wires instead of generating.

## Why

The current approach requires the LLM to generate payment flows, auth middleware, and email templates from scratch every run. This is slow (thousands of tokens per specialist), fragile (each generation can introduce new bugs), and produces shallow implementations (the LLM can't hold a full Stripe webhook flow in context).

The fix: ship the 80% that's the same every time as installable blocks. The LLM's job becomes selecting, configuring, and gluing blocks — work it's actually good at.

## Block Structure

Each block lives in `blocks/{name}/` and is a self-contained, installable package:

```
blocks/stripe/
  block.json              # Metadata: name, version, deps, env vars, specialists
  README.md               # What this block provides, how to configure
  backend/
    __init__.py
    routes.py             # FastAPI router: /checkout, /webhook, /subscriptions
    models.py             # SQLAlchemy/Pydantic models
    schemas.py            # Request/response schemas
    service.py            # Stripe API client wrapper
  frontend/
    pages/
      PricingPage.tsx
      SubscriptionPage.tsx
    components/
      CheckoutButton.tsx
      PricingCard.tsx
      SubscriptionStatus.tsx
  tests/
    test_routes.py
    test_service.py
  glue/
    main.py.append        # Lines to append to main.py (route registration)
    App.tsx.append        # Lines to append to App.tsx (route imports)
```

### block.json schema

```json
{
  "name": "stripe",
  "version": "0.1.0",
  "description": "Stripe payment processing — checkout, subscriptions, webhooks",
  "triggers": ["payment", "stripe", "checkout", "subscription", "billing"],
  "dependencies": {
    "python": ["stripe>=9.0.0"],
    "node": ["@stripe/stripe-js", "@stripe/react-stripe-js"]
  },
  "env_vars": {
    "STRIPE_SECRET_KEY": "",
    "STRIPE_PUBLISHABLE_KEY": "",
    "STRIPE_WEBHOOK_SECRET": ""
  },
  "specialists": {
    "Plumber": { "append": ["backend/routes.py", "backend/models.py"], "config": {"webhook_path": "/api/stripe/webhook"} },
    "Sculptor": { "append": ["frontend/pages/PricingPage.tsx"], "imports": ["PricingPage", "CheckoutButton"] }
  },
  "backend_routes": ["/api/stripe/checkout", "/api/stripe/webhook", "/api/stripe/subscriptions"],
  "frontend_pages": ["/pricing", "/subscription"]
}
```

## How the Pipeline Uses Blocks

### Detect (during Foreman planning)

The Foreman scans specs for trigger keywords (e.g. "stripe", "payment"). Matched block names are added to the build manifest.

### Install (before specialist execution)

The Registrar reads the manifest, copies block files into the output directory, adds deps to `requirements.txt`/`package.json`, and appends glue code to entry points.

### Configure (during specialist execution)

Each specialist reads its block's `config` and writes configuration. Plumber writes the Stripe route registration into entry points. Sculptor adds the pricing page route to `App.tsx`. The block provides the real implementation; the specialist writes 3-5 lines of registration code.

### Verify (during Judge)

Judge checks each block's env vars are configured and its endpoints respond. Block tests run as part of the lint/verify pipeline.

## Implementation Plan

### Phase 1 — Block infrastructure

| Task | Description |
|------|-------------|
| P1.1 | `blocks/` directory + `block.json` schema + loader |
| P1.2 | `Registrar.match_blocks(specs)` — keyword matching |
| P1.3 | `Registrar.install_block(name, output_dir)` — copy, append glue, add deps |
| P1.4 | Update manifest to include `"blocks": [...]` |
| P1.5 | Tests: block match, install, glue append |

### Phase 2 — Stripe block (prototype)

| Task | Description |
|------|-------------|
| P2.1 | `blocks/stripe/block.json` — triggers, deps, env vars |
| P2.2 | `blocks/stripe/backend/` — FastAPI routes, models, schemas, service |
| P2.3 | `blocks/stripe/frontend/` — PricingPage, CheckoutButton |
| P2.4 | `blocks/stripe/glue/` — main.py.append, App.tsx.append |
| P2.5 | `blocks/stripe/tests/` — route + service tests |
| P2.6 | e2e: vibe with "stripe" triggers block install, app boots |

### Phase 3 — Auth block

| Task | Description |
|------|-------------|
| P3.1 | `blocks/auth/` — JWT auth, register, login, password reset, OAuth stubs |
| P3.2 | Frontend: LoginPage, RegisterPage, ProtectedRoute |
| P3.3 | Tests + e2e |

### Phase 4 — Generalize

| Task | Description |
|------|-------------|
| P4.1 | Block registry in `blocks/index.json` for auto-discovery |
| P4.2 | UI in Settings: list available blocks, toggle inclusion |
| P4.3 | Block versioning and update mechanism |

## Block Design Principles

1. **No business logic in glue code.** Glue just registers routes/pages. All logic lives in the block's own files.
2. **Blocks are independently testable.** Each ships with pytest tests using mocked external services.
3. **Env vars are the only configuration surface.** Never hardcode API keys or URLs.
4. **Specialists configure, blocks implement.** Specialist writes 2 lines of registration; block provides 200 lines of implementation.
5. **One model, one block.** Blocks don't depend on each other. Glue composes them independently.
