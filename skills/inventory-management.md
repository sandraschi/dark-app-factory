# Skill: Inventory & Stock Management (2026 SOTA)

## 1. Domain Context
Warehouse, retail, or workshop stock tracking. Single-location or multi-location.
Use cases: small manufacturer, repair shop parts bin, retailer back-office, restaurant larder.
Austrian context: EAN/GTIN barcode support, € pricing, Austrian tax codes (USt).

## 2. Mandatory Pages & Routes
- `/` — Dashboard: low-stock alerts, top movers, stock valuation summary, recent movements
- `/inventory` — Full product list: search, category filter, low-stock toggle, bulk actions
- `/inventory/:id` — Product detail: stock levels per location, movement history, suppliers
- `/inventory/new` — Create product: name, SKU, barcode, category, unit, reorder level
- `/movements` — Stock movement log: receive, consume, adjust, transfer — filterable by date/type
- `/movements/new` — Record movement form: type selector, product lookup, quantity, notes
- `/suppliers` — Supplier list with contact, lead time, last order date
- `/reports` — Stock valuation (FIFO/avg cost), slow movers, reorder suggestions export

## 3. Data Model (PostgreSQL preferred)
```sql
products (id, sku, barcode_ean, name, description, category_id FK, unit VARCHAR(20),
          cost_price_cents, sell_price_cents, reorder_level INT, image_url, created_at)
categories (id, name, parent_id FK)
locations (id, name, description)  -- warehouse zones, shelves
stock_levels (id, product_id FK, location_id FK, qty_on_hand INT, qty_reserved INT,
              UNIQUE(product_id, location_id))
stock_movements (id, product_id FK, location_id FK, movement_type ENUM('receive','consume','adjust','transfer_in','transfer_out'),
                 qty INT, reference VARCHAR(100), notes TEXT, performed_by FK, created_at)
suppliers (id, name, contact_name, email, phone, lead_time_days INT, notes TEXT)
product_suppliers (product_id FK, supplier_id FK, supplier_sku, cost_price_cents, PRIMARY KEY(product_id, supplier_id))
```

## 4. Backend Specifics
- Stock level is always derived from `SUM(stock_movements.qty)` or maintained via trigger — never a stale cached field updated ad-hoc
- Low-stock alert: `stock_levels.qty_on_hand <= products.reorder_level` — expose `GET /api/alerts/low-stock`
- Barcode lookup: `GET /api/products?barcode=XXXXXXXX` — for scanner integration
- Movement recording must be atomic: insert movement + update stock_level in a single transaction
- FIFO cost calculation for stock valuation: walk movements in chronological order
- CSV export: `GET /api/reports/valuation.csv` and `GET /api/reports/movements.csv`

## 5. Frontend Specifics
- Product list: dense data table, sortable columns, inline quantity badge with colour coding
  - `qty <= reorder_level` → red badge; `qty <= 2 * reorder_level` → yellow; else green
- Movement form: product field is a searchable combobox (type SKU or name); barcode scan input support
- Stock chart: line chart showing qty_on_hand over last 30 days per product (recharts)
- Low-stock widget on dashboard: list of products needing reorder with one-click "Order" action
- Reports page: date-range picker, metric selector, download CSV button

## 6. Austrian / EU Notes
- EAN-13 barcode format is standard for Austrian retail
- Cost prices stored in cents (integer) to avoid floating-point rounding
- USt (VAT) rates: 20% standard, 10% reduced (food, books) — store `vat_rate` on product
- Currency display: `€ X,XX` with comma decimal separator

## 7. Key Third-Party Integrations (all via env vars)
- `EMAIL_API_URL` — low-stock alert emails to procurement manager
- `STORAGE_API_URL` — product image uploads
