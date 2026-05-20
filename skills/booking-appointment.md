# Skill: Booking & Appointment System (2026 SOTA)

## 1. Domain Context
Calendar-driven booking for service businesses: medical practices, salons, consultancies, repair shops, tutors.
Austrian context: DSGVO-compliant patient/client data, GDPR consent at booking, Impressum mandatory.
Covers both single-provider (solo practitioner) and multi-provider (clinic with multiple staff) configurations.

## 2. Mandatory Pages & Routes
- `/` — Landing: hero with booking CTA, service overview, provider bios, testimonials
- `/book` — 3-step booking wizard: Select Service → Pick Slot → Enter Details
- `/book/confirm/:token` — Email confirmation landing, show booking summary
- `/book/cancel/:token` — One-click cancellation with reason selector
- `/dashboard` — Provider view: today's agenda, upcoming week, quick reschedule
- `/dashboard/calendar` — Full monthly/weekly calendar view (FullCalendar or custom)
- `/dashboard/clients` — Client list, search, profile with booking history
- `/dashboard/services` — CRUD for service types (name, duration_minutes, price, colour)
- `/dashboard/availability` — Set recurring hours + block-off dates

## 3. Data Model (PostgreSQL preferred)
```sql
providers (id, name, email, bio, avatar_url, timezone VARCHAR(60))
services (id, provider_id FK, name, duration_minutes, price_cents, colour, buffer_minutes)
availability_rules (id, provider_id FK, day_of_week INT, start_time TIME, end_time TIME)
availability_blocks (id, provider_id FK, blocked_from TIMESTAMPTZ, blocked_until TIMESTAMPTZ, reason)
bookings (id, service_id FK, provider_id FK, client_name, client_email, client_phone,
          starts_at TIMESTAMPTZ, ends_at TIMESTAMPTZ, status ENUM('pending','confirmed','cancelled','completed'),
          notes TEXT, confirmation_token UUID, cancel_token UUID, created_at TIMESTAMPTZ)
```

## 4. Slot Availability Algorithm
```
1. Load provider's availability_rules for the requested date's day_of_week
2. Subtract all availability_blocks overlapping the date
3. Subtract existing bookings (status != 'cancelled') + service buffer_minutes
4. Return remaining slots as start-time list (step = service.duration_minutes)
5. Enforce timezone: store all TIMESTAMPTZ in UTC, display in provider.timezone
```
- Endpoint: `GET /api/slots?provider_id=X&service_id=Y&date=YYYY-MM-DD`
- Returns: `{ "slots": ["09:00", "09:30", "10:30", ...] }`

## 5. Backend Specifics
- Confirmation email sent on booking creation via `EMAIL_API_URL`
- Reminder email sent 24h before via background task (APScheduler or Celery)
- Double-booking prevention: `SELECT ... FOR UPDATE` or optimistic locking on slot insert
- All datetimes stored as TIMESTAMPTZ UTC; displayed in provider timezone on frontend
- Admin token auth for `/dashboard` routes (JWT, httpOnly cookie)
- Public endpoints (slot lookup, booking create) are rate-limited: 20 req/min per IP

## 6. Frontend Specifics
- Booking wizard: react-hook-form, Zod validation, no full-page reloads between steps
- Calendar: custom weekly grid preferred over heavy library; show availability as green slots
- Time display: 24h format for AT/DE locale (`09:00` not `9:00 AM`)
- Slot picker: disabled slots visually greyed, selected slot highlighted in accent colour
- Provider dashboard: drag-to-reschedule on calendar (optional), colour-coded by service

## 7. Austrian / EU Compliance
- DSGVO consent checkbox at booking form (explicit, not pre-checked)
- Data retention notice: client data deleted after 3 years unless consent renewed
- Impressum page (§ 5 E-Commerce-Gesetz)
- Phone format validation: accept +43, 0043, and local 0X formats

## 8. Key Third-Party Integrations (all via env vars)
- `EMAIL_API_URL` — confirmation, reminder, cancellation emails
- `SMS_API_URL` — optional SMS reminder (if phone provided)

## 9. Applicable Vibes
`dentist`, `physiotherapy`, `salon`, `barber`, `massage`, `consultant`, `tutor`, `repair shop`, `veterinary`, `beauty clinic`
