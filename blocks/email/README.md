# Email Block

Transactional email via SendGrid or SMTP with template management, verification flows, and welcome email automation.

**Triggers**: email, mail, sendgrid, smtp, newsletter, notification, verify, welcome

**Env vars**:
| Variable | Default | Description |
|----------|---------|-------------|
| `SENDGRID_API_KEY` | — | SendGrid API key |
| `SMTP_HOST` | — | SMTP server hostname |
| `SMTP_PORT` | `587` | SMTP server port |
| `SMTP_USER` | — | SMTP username |
| `SMTP_PASS` | — | SMTP password |
| `FROM_EMAIL` | `noreply@example.com` | Default sender address |

**API endpoints**: `/api/email/send`, `/api/email/templates`, `/api/email/verify`

**Dependencies**: `pip: sendgrid>=6.0.0, python-multipart>=0.0.9`
