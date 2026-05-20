# Skill: E-Commerce Store (2026 SOTA)

## 1. Domain Context
A modern e-commerce storefront with product catalogue, cart, checkout, and order management.
Austrian/EU context: GDPR-compliant data handling, VAT 20% Austria standard, €/EUR currency, IBAN payment support alongside cards.

## 2. Mandatory Pages & Routes
- `/` — Hero with featured products, category grid, promotional banner
- `/products` — Filterable product grid (category, price range, in-stock toggle)
- `/products/:slug` — Product detail: images, description, variants (size/colour), add-to-cart, reviews
- `/cart` — Line items, quantity controls, subtotal, VAT breakdown, promo codes
- `/checkout` — Step flow: Shipping → Payment → Confirmation
- `/orders` — Order history with status badges (Pending / Shipped / Delivered)
- `/account` — Profile, saved addresses, payment methods

## 3. Data Model (PostgreSQL preferred)
```sql
products (id, slug, name, description, price_cents, vat_rate, stock_qty, category_id, images JSONB, metadata JSONB)
categories (id, slug, name, parent_id)
orders (id, user_id, status, total_cents, shipping_address JSONB, line_items JSONB, created_at)
reviews (id, product_id, user_id, rating INT, body TEXT, created_at)
```

## 4. Backend Specifics
- Cart: server-side session OR JWT-scoped cart table — NOT localStorage only
- Payment: integrate via `STRIPE_API_URL` env var (DTU-compatible); never hardcode keys
- Order status webhook endpoint: `POST /api/webhooks/stripe` with signature verification
- Search: full-text search on `products.name` + `products.description` via `tsvector`
- Pagination: all list endpoints use cursor-based pagination (not offset)

## 5. Frontend Specifics
- Product grid: Masonry or 3-column responsive, hover zoom, quick-add button
- Cart drawer: slides in from right, framer-motion slide animation
- Checkout: react-hook-form with Zod validation on every step; no full-page reloads
- Price display: always show `€ X,XX` format (comma as decimal separator for AT/DE locale)
- Loading states: skeleton cards, not spinners

## 6. Austrian / EU Compliance
- Impressum page mandatory (§ 5 E-Commerce-Gesetz)
- Cookie consent banner (DSGVO / ePrivacy)
- Right of withdrawal (14 days) notice at checkout
- VAT clearly broken out on order confirmation
- Privacy Policy link in footer

## 7. Key Third-Party Integrations (all via env vars)
- `STRIPE_API_URL` — payments
- `EMAIL_API_URL` — order confirmations, shipping notifications
- `STORAGE_API_URL` — product image uploads
