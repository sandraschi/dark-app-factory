# Skill: Healthcare / Medical Practice Management (2026 SOTA)

## 1. Domain Context
Patient management, medical records, prescription tracking, and practice administration.
Covers GP, specialist (dentist, physio, psychiatrist, dermatologist), and multi-doctor clinics.
Austrian context: e-card (ELGA) awareness, DSGVO strict health-data handling, ÖÄK compliance notes.

**IMPORTANT**: This is a management tool, NOT a diagnostic tool. Never generate AI-driven diagnosis logic.

## 2. Mandatory Pages & Routes

### Patient-facing
- `/` — Practice landing: about, services, team, opening hours, booking CTA
- `/book` — Appointment booking wizard (link to booking-appointment skill for slot logic)
- `/impressum` — Austrian legal requirement

### Staff / Doctor back-office (`/app` prefix, auth-gated)
- `/app/dashboard` — Today's appointments list, new patient notifications, overdue follow-ups
- `/app/patients` — Searchable patient list with DSGVO-compliant data display
- `/app/patients/new` — Registration form
- `/app/patients/:id` — Patient profile: demographics, insurance, appointment history, documents
- `/app/patients/:id/records` — Medical records timeline (chronological notes, diagnoses, procedures)
- `/app/patients/:id/records/new` — Create record: date, type, findings (Markdown), attachments
- `/app/appointments` — Calendar view (day/week) with drag-reschedule
- `/app/billing` — Invoice generation, payment status, insurance claim tracking

## 3. Data Model (PostgreSQL — strict)
```sql
patients (id, svnr_hash BYTEA,  -- hash of Sozialversicherungsnummer, NEVER store plaintext
          first_name, last_name, date_of_birth DATE, gender ENUM('m','f','d','x'),
          email, phone, address JSONB, insurance_provider, insurance_number_hash BYTEA,
          gdpr_consent_at TIMESTAMPTZ, gdpr_consent_version VARCHAR(10),
          created_at, updated_at)
medical_records (id, patient_id FK, provider_id FK,
                 record_date DATE, record_type ENUM('anamnesis','diagnosis','procedure','prescription','lab','note','referral'),
                 findings_md TEXT,  -- Markdown, never raw HTML
                 icd10_codes TEXT[],  -- ICD-10 diagnosis codes
                 attachments JSONB,
                 created_at)
prescriptions (id, patient_id FK, provider_id FK, medication_name, dosage, frequency,
               prescribed_at DATE, valid_until DATE, repeats_allowed INT, repeats_used INT)
invoices (id, patient_id FK, appointment_id FK, line_items JSONB, total_cents INT,
          vat_rate DECIMAL, status ENUM('draft','sent','paid','cancelled'), issued_at DATE)
```

## 4. Backend Specifics
- **DSGVO / Health data**: Encrypt `findings_md` at rest using AES-256 via application-layer encryption (not just DB encryption); key stored in env var `ENCRYPTION_KEY`
- **SVNR**: Never store Austrian SVN in plaintext; store `SHA-256(svnr + SALT)` for lookup
- **Access control**: Doctors see only their patients unless clinic-admin role; no cross-provider data leakage
- **Audit trail**: Every read/write to `medical_records` and `patients` appended to immutable `audit_logs` table
- **Data export**: `GET /api/patients/:id/export` — DSGVO Auskunftsrecht (right of access), returns JSON zip
- **Data deletion**: `DELETE /api/patients/:id` — DSGVO Recht auf Löschung, anonymises records but retains billing for 7 years (Austrian UGB)

## 5. Frontend Specifics
- Patient search: debounced, searches by name OR date of birth — never show full SVNR in UI
- Medical records timeline: chronological list, filterable by record_type, expandable cards
- Markdown editor for findings: simple toolbar (bold, italic, headings, bullet list); no raw HTML input
- ICD-10 picker: searchable combobox against ICD-10-GM (German version) code list
- Invoice builder: line-item table with quantity × unit price, VAT calculation, PDF generation button
- DSGVO banner on patient profile: shows consent date and version; "Widerrufen" (revoke) button

## 6. Austrian / EU Compliance (mandatory, not optional)
- DSGVO Art. 9 special category data (health) — explicit consent required, documented
- Aufbewahrungspflicht: medical records 10 years (ÄrzteG), billing records 7 years (BAO)
- Impressum with ärztliche Berufsbezeichnung
- No cross-border data transfer without SCCs (no US-only cloud storage)
- Password requirements: minimum 12 chars, MFA strongly recommended

## 7. Key Third-Party Integrations (all via env vars)
- `EMAIL_API_URL` — appointment reminders, prescription renewals, billing
- `SMS_API_URL` — reminder SMS 24h before appointment
- `STORAGE_API_URL` — lab result PDFs, X-rays, referral letters
