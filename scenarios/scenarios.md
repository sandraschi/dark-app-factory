# Test Scenarios: Hollabrunn_Hive_Core (Hollabrunn_Hive_Core)

## 1. Authentication & Authorization
- [ ] **Title**: Successful Customer Registration
  - GIVEN: A new user wants to create a customer account
  - WHEN: Submit a POST request to `/api/v1/auth/register` with valid name, email, and password
  - THEN: A 201 Created status is returned and a new user record is created.
- [ ] **Title**: Successful Admin Login
  - GIVEN: An existing admin account (Julius)
  - WHEN: Submit a POST request to `/api/v1/auth/login` with correct credentials
  - THEN: A 200 OK status is returned with a valid JWT/session.
- [ ] **Title**: Unauthorized Access to Admin Routes
  - GIVEN: A user authenticated with the 'customer' role
  - WHEN: Submit a GET request to `/api/v1/admin/hives`
  - THEN: A 403 Forbidden error is returned.
- [ ] **Title**: Failed Login - Invalid Credentials
  - GIVEN: A registered user email but incorrect password
  - WHEN: Submit a POST request to `/api/v1/auth/login`
  - THEN: A 401 Unauthorized error is returned.

## 2. Public Storefront (Shop_Zone)
- [ ] **Title**: Fetch All Products
  - GIVEN: The public shop is active
  - WHEN: Submit a GET request to `/api/v1/shop/products`
  - THEN: A 200 OK status is returned with an array of product objects.
- [ ] **Title**: Fetch Specific Product Details
  - GIVEN: A valid UUID for a honey product exists
  - WHEN: Submit a GET request to `/api/v1/shop/products/{id}`
  - THEN: A 200 OK status is returned with the specific product's details.
- [ ] **Title**: Fetch Non-existent Product
  - GIVEN: A random UUID that does not exist in the database
  - WHEN: Submit a GET request to `/api/v1/shop/products/{id}`
  - THEN: A 404 Not Found error is returned.
- [ ] **Title**: Successful Checkout Flow
  - GIVEN: A customer has items in their cart and a valid shipping address
  - WHEN: Submit a POST request to `/api/v1/shop/checkout` with item IDs and quantities
  - THEN: A 201 Created status is returned with an order_id, and stock_count for products is decremented.
- [ ] **Title**: Checkout - Out of Stock Item
  - GIVEN: A product exists but its `stock_count` is 0
  - WHEN: Submit a POST request to `/api/v1/shop/checkout` including that item
  - THEN: A 400 Bad Request error is returned indicating insufficient stock.

## 3. Admin Management Portal (Admin_Zone)
- [ ] **Title**: List All Hives and Statuses
  - GIVEN: An authenticated admin user
  - WHEN: Submit a GET request to `/api/v1/admin/hives`
  - THEN: A 200 OK status is returned containing the list of all hives.
- [ ] **Title**: Retrieve Hive Telemetry Data
  - GIVEN: A valid hive_id (e.g., "Hollabrunn_01")
  - WHEN: Submit a GET request to `/api/v1/admin/hives/{id}/telemetry`
  - THEN: A 200 OK status is returned with the last 24 hours of temperature readings.
- [ ] **Title**: Update Inventory Stock Level
  - GIVEN: An authenticated admin user
  - WHEN: Submit a PUT request to `/api/v1/admin/inventory` with a product ID and new `stock_count`
  - THEN: A 200 OK status is returned and the database reflects the updated count.
- [ ] **Title**: Schedule Swarm Event
  - GIVEN: An authenticated admin user
  - WHEN: Submit a POST request to `/api/v1/admin/swarms` with `hive_id`, `scheduled_date`, and `status`
  - THEN: A 201 Created status is returned.

## 4. Edge Cases & State Machines
- [ ] **Title**: Order Status Transition (Pending -> Paid)
  - GIVEN: An order exists with status `Pending`
  - WHEN: A successful payment confirmation is received by the system
  - THEN: The order status updates to `Paid`.
- [ ] **Title**: Hive Temperature Warning Alert (High)
  - GIVEN: A hive's telemetry data shows a temperature of 45°C
  - WHEN: The dashboard fetches telemetry via `/api/v1/admin/hives/{id}/telemetry`
  - THEN: The frontend renders a visual "Warning" alert.
- [ ] **Title**: Hive Temperature Warning Alert (Low)
  - GIVEN: A hive's telemetry data shows a temperature of 5°C
  - WHEN: The dashboard fetches telemetry via `/api/v1/admin/hives/{id}/telemetry`
  - THEN: The frontend renders a visual "Warning" alert.
- [ ] **Title**: Invalid Telemetry Data (Null/Malformed)
  - GIVEN: A sensor sends a null value for temperature
  - WHEN: The system attempts to process the telemetry update
  - THEN: The backend ignores the mal_formed packet and retains the last valid reading, returning 200 or ignoring.

## 5. Security & Boundary Testing
- [ ] **Title**: SQL Injection Prevention on Product Search
  - GIVEN: A malicious payload in a search query
  - WHEN: Submit a GET request to `/api/v1/shop/products?name='OR 1=1--`
  - THEN: The system handles the input as a literal string and returns 200 or 400, but never executes the raw SQL.
- [ ] **Title**: Payload Size Limit on Checkout
  - GIVEN: A massive JSON payload for the checkout request
  - WHEN: Submit a POST request to `/api/v1/shop/checkout` with an oversized body
  - THEN: A 413 Payload Too Large error is returned.
- [ ] **Title**: Rate Limiting on Login
  - GIVEN: Multiple rapid login attempts from the same IP
  - WHEN: Submit a POST request to `/api/v1/auth/login` 10 times in 5 seconds
  - THEN: A 429 Too Many Requests error is returned.