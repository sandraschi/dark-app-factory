# Skill: SaaS Dashboard & Admin Panel (2026 SOTA)

## 1. Domain Context
A multi-tenant SaaS product with a user-facing dashboard, admin back-office, billing, and team management.
Typical use cases: analytics platforms, project tools, internal tooling, B2B apps.

## 2. Mandatory Pages & Routes

### User-facing
- `/dashboard` — KPI tiles (revenue, users, events), line/bar charts, recent activity feed
- `/analytics` — Date-range picker, filterable chart suite, exportable data table
- `/projects` or `/workspaces` — Card grid with create/archive actions
- `/settings` — Profile, notifications, API keys, danger zone (delete account)
- `/billing` — Current plan, usage meter, invoice history, upgrade CTA

### Admin back-office (under `/admin` prefix, role-gated)
- `/admin` — Fleet overview: user count, MRR, error rate, server health
- `/admin/users` — Searchable table, impersonate, ban, role change
- `/admin/billing` — Stripe dashboard mirror, manual invoice, refund trigger

## 3. Data Model (PostgreSQL preferred)
```sql
tenants (id, name, plan ENUM('free','pro','enterprise'), stripe_customer_id, created_at)
users (id, tenant_id FK, email, role ENUM('owner','admin','member'), last_login_at)
api_keys (id, user_id FK, key_hash, name, scopes TEXT[], last_used_at, created_at)
audit_logs (id, tenant_id FK, user_id FK, action, resource_type, resource_id, meta JSONB, created_at)
invoices (id, tenant_id FK, amount_cents, status, stripe_invoice_id, issued_at, paid_at)
```

## 4. Backend Specifics
- All endpoints scoped by `tenant_id` extracted from JWT — never trust user-supplied tenant IDs
- Role-based access control: middleware checks `user.role` before every admin endpoint
- Rate limiting per API key: sliding window, 1000 req/hour default
- Audit logging: every mutation writes to `audit_logs` — never skip this
- Stripe webhook: `POST /api/webhooks/stripe` handles `invoice.paid`, `customer.subscription.deleted`
- SSE endpoint: `GET /api/events` streams real-time dashboard updates

## 5. Frontend Specifics
- Charts: Recharts preferred (already in base deps); dark theme with cyan/purple accent palette
- KPI tiles: large number, percentage delta badge (green/red), sparkline
- Data tables: sortable columns, row selection, bulk actions, CSV export button
- Sidebar navigation: collapsible, active route highlight, role-aware (hide admin items for members)
- Toast notifications for all async actions (react-hot-toast or custom)
- Mobile: sidebar collapses to bottom nav on < 768px

## 6. Auth Pattern
- JWT access token (15 min) + refresh token (7 days, httpOnly cookie)
- `/api/auth/login` → returns access JWT in body, refresh in cookie
- `/api/auth/refresh` → rotates both tokens
- `/api/auth/logout` → clears cookie, blacklists refresh token in Redis or DB

## 7. Key Third-Party Integrations (all via env vars)
- `STRIPE_API_URL` — subscription billing
- `EMAIL_API_URL` — welcome emails, password reset, billing alerts
- `WEBHOOK_URL` — outbound webhook delivery to tenants

## 8. Design Tokens
- Background: `#09090b` (zinc-950)
- Surface: `#18181b` (zinc-900) with `border border-zinc-800`
- Accent: `#00f3ff` (cyan) for primary actions
- Danger: `#ef4444` (red-500) for delete/ban actions
- Typography: Inter, 14px base, tight tracking for data density
