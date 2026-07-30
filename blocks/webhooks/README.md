# Webhooks Block

Generic webhook receiver — event ingestion, HMAC signature verification, replay, delivery logging, and retry logic.

**Triggers**: webhook, callback, hook, incoming, event.receive, payload

**Env vars**:
| Variable | Default | Description |
|----------|---------|-------------|
| `WEBHOOK_SECRET` | — | HMAC signing secret for verification |

**API endpoints**: `/api/webhooks/receive/{source}`, `/api/webhooks/log`, `/api/webhooks/replay/{id}`

**Dependencies**: (none)
