# Stripe Block

Stripe payment processing — checkout sessions, subscriptions, webhooks, payment methods, and customer portal.

**Triggers**: payment, stripe, checkout, subscription, billing, pay, pricing, plan

**Env vars**:
| Variable | Default | Description |
|----------|---------|-------------|
| `STRIPE_SECRET_KEY` | — | Stripe secret API key |
| `STRIPE_PUBLISHABLE_KEY` | — | Stripe publishable API key |
| `STRIPE_WEBHOOK_SECRET` | — | Webhook signing secret |

**API endpoints**: `/api/stripe/create-checkout`, `/api/stripe/webhook`, `/api/stripe/customer-portal`

**Dependencies**: `pip: stripe>=9.0.0` / `npm: @stripe/stripe-js, @stripe/react-stripe-js`
