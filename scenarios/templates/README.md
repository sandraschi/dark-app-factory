# Scenario Templates

Prebuilt GIVEN/WHEN/THEN scenario skeletons for common domains. Use these to bootstrap `scenarios.md` instead of relying solely on Foreman LLM generation.

## Available Templates

| Template | Domain | Scenarios |
|----------|--------|-----------|
| `ecommerce.md` | Online store, shop, cart, checkout | 14 (auth, browse, cart, checkout, edge cases) |
| `saas-auth.md` | B2B SaaS, dashboards, multi-tenant auth | 13 (register, login, password, access control) |
| `crud-resource.md` | Generic CRUD (users, items, posts, etc.) | 12 (create, read, update, delete, validation) |

## How to Use

### 1. Copy into vibe.md or specs

Mention in your vibe that the Foreman should include scenarios from a template:

```
Include standard e-commerce flows: registration, product browsing, add to cart, checkout.
Use paths: /products, /cart, /orders.
```

### 2. Copy-paste and parameterize

Copy the relevant sections from a template into `specs/scenarios.md` (or let the Foreman generate a variant), then replace:

- `/products` → your actual product path (e.g. `/api/v1/products`)
- `{resource}` → your resource name (e.g. `users`, `posts`)
- Payload hints → match your API schema

### 3. Enhance Foreman prompt

In `foreman.py` or the planning prompt, add instructions such as:

> When generating scenarios, prefer patterns from `scenarios/templates/` for the detected domain (e-commerce, SaaS auth, CRUD). Use the same GIVEN/WHEN/THEN structure and HTTP-style WHEN clauses.

## Format Requirements

The scenario parser expects:

- `## Category` headings
- `### N. Title` headings
- `- [ ] **Title**: Description.`
- `- GIVEN: ...` / `- WHEN: ...` / `- THEN: ...` lines

WHEN clauses should use the pattern:

- `Submit a POST request to \`/path\` with valid JSON payload.`
- `Submit a GET request to \`/path\`.`

See `src/verification/scenario_parser.py` for the exact regex patterns.

## Adding New Templates

Create a new `.md` file in this directory. Use the same structure as the existing templates. Domain ideas: content management, booking/scheduling, file storage, notifications, analytics dashboards.
