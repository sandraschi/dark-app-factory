# E-Commerce Scenario Templates
# ==============================
# Copy relevant sections into your vibe.md or specs. Replace /products, /cart, etc.
# with your actual API paths.

## User Registration & Auth

### 1. Register New User
  - [ ] **Register New User**: A new user can create an account with valid credentials.
    - GIVEN: No users exist with the given email.
    - WHEN: Submit a POST request to `/auth/register` with valid JSON payload (email, password, name).
    - THEN: The new user is created, and a confirmation email is sent.

### 2. Login With Valid Credentials
  - [ ] **Login Valid**: An existing user can log in with correct email and password.
    - GIVEN: An existing user exists in the system with valid credentials.
    - WHEN: Submit a POST request to `/auth/login` with valid JSON payload.
    - THEN: A session token or JWT is returned.

### 3. Login Rejected Invalid Credentials
  - [ ] **Login Invalid**: Login with wrong credentials is rejected.
    - GIVEN: An existing user exists in the system.
    - WHEN: Submit a POST request to `/auth/login` with invalid JSON payload (wrong password).
    - THEN: The login attempt is rejected, and a 401 Unauthorized error is returned.

### 4. Password Reset Request
  - [ ] **Password Reset Request**: A user can request a password reset link.
    - GIVEN: An existing user exists in the system with valid credentials.
    - WHEN: Submit a POST request to `/auth/forgot-password` with valid JSON payload (email).
    - THEN: A reset link is sent, and a 200 OK response is returned.

## Product Browsing

### 5. List Products
  - [ ] **List Products**: A list of products can be retrieved.
    - GIVEN: Multiple products exist in the catalog.
    - WHEN: Submit a GET request to `/products`.
    - THEN: The list of products is returned, including IDs, names, and prices.

### 6. Get Single Product
  - [ ] **Get Product By ID**: A single product can be retrieved by ID.
    - GIVEN: A product exists in the system with ID 1.
    - WHEN: Submit a GET request to `/products/1`.
    - THEN: The product details are returned, including name, price, and description.

### 7. Product Not Found
  - [ ] **Product Not Found**: Requesting a non-existent product returns 404.
    - GIVEN: No product exists with ID 999.
    - WHEN: Submit a GET request to `/products/999`.
    - THEN: A 404 Not Found error is returned.

## Shopping Cart

### 8. Add Item To Cart
  - [ ] **Add To Cart**: An authenticated user can add a product to the cart.
    - GIVEN: An authenticated user and a product with ID 1 exist.
    - WHEN: Submit a POST request to `/cart/items` with valid JSON payload (product_id, quantity).
    - THEN: The item is added to the cart, and cart details are returned.

### 9. Retrieve Cart
  - [ ] **Retrieve Cart**: An authenticated user can view their cart.
    - GIVEN: An authenticated user has items in the cart.
    - WHEN: Submit a GET request to `/cart`.
    - THEN: The cart contents are returned, including items and totals.

### 10. Remove Item From Cart
  - [ ] **Remove From Cart**: An authenticated user can remove an item from the cart.
    - GIVEN: An authenticated user has item with ID 1 in the cart.
    - WHEN: Submit a DELETE request to `/cart/items/1`.
    - THEN: The item is removed, and the cart is updated.

## Checkout & Orders

### 11. Create Order (Checkout)
  - [ ] **Checkout**: An authenticated user can complete checkout.
    - GIVEN: An authenticated user has items in the cart.
    - WHEN: Submit a POST request to `/orders` with valid JSON payload (payment_method, shipping_address).
    - THEN: The order is created, and order details are returned.

### 12. List User Orders
  - [ ] **List Orders**: An authenticated user can view their order history.
    - GIVEN: An authenticated user has placed orders.
    - WHEN: Submit a GET request to `/orders`.
    - THEN: The list of orders is returned, including IDs and statuses.

## Security & Edge Cases

### 13. Unauthorized Access
  - [ ] **Unauthorized Access**: Protected endpoints reject unauthenticated requests.
    - GIVEN: No valid session or token.
    - WHEN: Submit a GET request to `/cart` without authentication.
    - THEN: A 401 Unauthorized or 403 Forbidden error is returned.

### 14. Out Of Stock
  - [ ] **Out Of Stock**: Adding an out-of-stock product returns an appropriate error.
    - GIVEN: Product ID 2 exists but has quantity 0.
    - WHEN: Submit a POST request to `/cart/items` with product_id 2 and quantity 1.
    - THEN: A 400 Bad Request or 409 Conflict error is returned.
