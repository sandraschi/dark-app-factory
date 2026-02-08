# Skill: Dentist SOTA 2026

## 1. Professional Tone & Voice
- Industrial but empathetic.
- Keywords: "Schmerzfrei" (Pain-free), "Qualitätsgarantie", "Modernste Technik".
- Locale: Vienna/Lower Austria style (Polite, professional, "Sie" form).

## 2. Branding & Aesthetics
- **Colors**: 
  - `primary`: #2C3E50 (Deep Navy)
  - `secondary`: #18BC9C (Clean Teal/Mint)
  - `background`: #F8F9FA (Soft White)
- **Glassmorphism**: Use `backdrop-filter: blur(10px)` for appointment cards.
- **Animations**: Subtle `framer-motion` fade-ins for treatment lists.

## 3. Mandatory Components & Depth
- **TreatmentHero**: High-impact header with a "Calm Image" (Nature/Abstract).
- **ServiceGrid (DEEP)**: 
  - Icons for Checkup, Hygiene, Implants.
  - **CRITICAL**: Every item MUST be a functional link to a dedicated sub-page (e.g., `/treatments/implants`).
  - **NO MOCK PALACES**: Every sub-page must contain at least 400 words of realistic domain content (Benefits, Process, Aftercare).
- **BookingFlow**: Step-based booking (Select Treatment -> Pick Date -> Patient Info).
- **ImpressumSection**: Strict Austrian compliance layout.

## 4. Technical Specifications
- Database: `patients` table must have `last_hygiene_visit` and `treatment_plan` (JSONB).
- Security: Sanitize all patient inputs; strict field validation for phone numbers (+43...).
