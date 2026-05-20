# Skills

Skills are Markdown files in the `skills/` directory that inject domain expertise into specialist prompts. When the Professor specialist detects a matching domain from your vibe, it loads the relevant skill file and makes its content available to all other specialists.

The effect is that specialists know the expected data model, required pages, compliance requirements, and integration patterns for your domain — rather than generating a generic app.

## How skill selection works

At the start of each build, the Professor:

1. Reads all `.md` files from `skills/`
2. Presents a compact index (filename + one-line description) to the LLM
3. The LLM selects the best match based on your specs (8k chars shown)
4. The skill file is loaded into `shared_context` and becomes available to every specialist

If no skill matches, the build proceeds without one. Results will be more generic but still functional.

## Included skills

### `booking-appointment.md`
Calendar-based booking for service businesses. Covers the slot availability algorithm (availability rules minus blocks minus existing bookings), 3-step booking wizard, confirmation/cancellation token flow, DSGVO consent, and Austrian phone format validation.

Applicable vibes: dentist, physiotherapy, salon, barber, massage, consultant, tutor, repair shop, veterinary, beauty clinic.

### `dentist-sota.md`
Austrian dental practice website. Vienna/Lower Austria locale, "Sie" form, specific branding tokens, booking flow, Impressum compliance, DSGVO patient data notes.

### `healthcare-practice.md`
Medical practice management with patient records, prescriptions, and billing. Enforces SVNR hashing (never plaintext), AES-256 encryption for medical record content, DSGVO Art. 9 special-category data handling, Austrian Aufbewahrungspflicht (10-year medical / 7-year billing retention), and audit logging on every read/write.

### `ecommerce-store.md`
Online store with product catalogue, cart, and checkout. Includes Austrian VAT (20% standard, 10% reduced) with explicit breakdown, EU right of withdrawal at checkout, Impressum, DSGVO cookie consent, and Stripe integration via DTU-compatible env vars.

### `saas-dashboard.md`
Multi-tenant SaaS product. Covers tenant-scoped JWT auth, role-based access control, API key management, audit logs, Stripe subscription webhooks, and a full admin back-office with user impersonation and billing management.

### `cms-blog.md`
Content management system with public blog front-end and authoring back-office. Includes full-text search via PostgreSQL `tsvector`, scheduled publishing, RSS/Atom feed, XML sitemap, draft preview via signed tokens, and complete SEO meta / structured data (Article schema).

### `task-project-management.md`
Task tracker with Kanban, list, and calendar views. Covers fractional index reorder, WebSocket real-time events, @mention notifications, activity logging, and keyboard shortcuts. Design tokens included.

### `inventory-management.md`
Stock management for warehouse, retail, or workshop. Stock levels derived from movement log (never a stale cached field), FIFO cost valuation, EAN-13 barcode lookup, Austrian USt rates (20%/10%), and CSV export for valuation and movement reports.

### `realtime-chat.md`
Slack-style workspace messaging. Covers WebSocket event model (message.new, typing indicators, presence), Redis pubsub for horizontal scaling, unread count management, virtual scrolling for large channels, and emoji reactions with optimistic UI.

### `iot-dashboard.md`
IoT device monitoring and control. Covers MQTT ingestion (Python `paho-mqtt` / Node `mqtt.js`), timeseries telemetry storage (plain PostgreSQL or TimescaleDB), rule engine with debounce, SSE streaming to frontend, command dispatch and ACK tracking. Applicable to smart home, greenhouse, robotics telemetry, factory floor monitoring.

### `mcp-windows-app-wrapper.md`
Wrapping a Windows executable (VLC, 7-Zip, etc.) as an MCP server with a FastMCP + FastAPI webapp. Covers the shared service layer pattern, subprocess invocation, FastMCP tool registration, and pyproject.toml packaging.

## Adding a skill

Create a new `.md` file in `skills/`. The filename becomes the identifier used by the LLM router.

A useful skill covers:

- **Domain context** — what kind of app this is, who uses it
- **Mandatory pages/routes** — what the app must have
- **Data model** — SQL schema or equivalent, with field names and types
- **Backend specifics** — non-obvious requirements (atomic transactions, encryption, rate limiting)
- **Frontend specifics** — layout expectations, key interactions
- **Compliance** — legal or regulatory requirements for the domain
- **Applicable vibes** — keywords that should trigger this skill

After adding the file, update the `skill_descriptions` dict in `src/specialists/council.py` (Professor class) with a one-line description. This description is what the LLM sees when routing — make it specific and keyword-rich.

```python
skill_descriptions = {
    # existing entries...
    "my-new-skill.md": "Short description with key domain terms that match likely vibe language",
}
```

## Skill coverage gaps

Currently no skills for: legal / law firm, restaurant / food ordering, real estate, education / LMS, HR / payroll, accounting / invoicing, fitness / gym management. These will produce generic output until a skill is added.
