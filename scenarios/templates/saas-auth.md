# SaaS Authentication Scenario Templates
# =======================================
# Standard auth flows for B2B SaaS, dashboards, and multi-tenant apps.

## Registration & Onboarding

### 1. Sign Up
  - [ ] **Sign Up**: A new user can create an account.
    - GIVEN: No user exists with the given email.
    - WHEN: Submit a POST request to `/api/auth/register` with valid JSON payload.
    - THEN: The new user is created, and a verification email is sent.

### 2. Email Verification
  - [ ] **Email Verification**: A user can verify their email with a token.
    - GIVEN: A user has requested registration and received a verification token.
    - WHEN: Submit a POST request to `/api/auth/verify-email` with valid JSON payload (token).
    - THEN: The email is marked as verified, and the user can log in.

### 3. Resend Verification
  - [ ] **Resend Verification**: A user can request a new verification email.
    - GIVEN: An unverified user exists in the system.
    - WHEN: Submit a POST request to `/api/auth/resend-verification` with valid JSON payload (email).
    - THEN: A new verification email is sent, and 200 OK is returned.

## Login & Session

### 4. Login Success
  - [ ] **Login Success**: Valid credentials yield a session.
    - GIVEN: A verified user exists with valid credentials.
    - WHEN: Submit a POST request to `/api/auth/login` with valid JSON payload.
    - THEN: A session token or JWT is returned with user profile.

### 5. Login Invalid Credentials
  - [ ] **Login Invalid**: Wrong password is rejected.
    - GIVEN: A user exists in the system.
    - WHEN: Submit a POST request to `/api/auth/login` with invalid JSON payload (wrong password).
    - THEN: The login attempt is rejected, and a 401 Unauthorized error is returned.

### 6. Login Unverified User
  - [ ] **Login Unverified**: Unverified user cannot log in.
    - GIVEN: A user exists but has not verified their email.
    - WHEN: Submit a POST request to `/api/auth/login` with valid credentials.
    - THEN: A 403 Forbidden error is returned with a message to verify email.

### 7. Logout
  - [ ] **Logout**: An authenticated user can log out.
    - GIVEN: An authenticated user has a valid session.
    - WHEN: Submit a POST request to `/api/auth/logout` with valid session token.
    - THEN: The session is invalidated, and 200 OK is returned.

## Password Management

### 8. Forgot Password
  - [ ] **Forgot Password**: User can request a password reset link.
    - GIVEN: An existing user exists in the system.
    - WHEN: Submit a POST request to `/api/auth/forgot-password` with valid JSON payload (email).
    - THEN: A reset link is sent, and 200 OK is returned.

### 9. Reset Password
  - [ ] **Reset Password**: User can set a new password with a valid reset token.
    - GIVEN: A user has requested a password reset and received a token.
    - WHEN: Submit a POST request to `/api/auth/reset-password` with valid JSON payload (token, new_password).
    - THEN: The password is updated, and the user can log in with the new password.

### 10. Change Password (Authenticated)
  - [ ] **Change Password**: An authenticated user can change their password.
    - GIVEN: An authenticated user exists with valid credentials.
    - WHEN: Submit a POST request to `/api/auth/change-password` with valid JSON payload (current_password, new_password).
    - THEN: The password is updated successfully.

## Access Control

### 11. Protected Endpoint Requires Auth
  - [ ] **Protected Endpoint Auth Required**: Unauthenticated request to protected resource fails.
    - GIVEN: No valid session or token.
    - WHEN: Submit a GET request to `/api/users/me` without authentication.
    - THEN: A 401 Unauthorized error is returned.

### 12. Admin-Only Endpoint
  - [ ] **Admin Only**: Non-admin user cannot access admin endpoint.
    - GIVEN: An authenticated regular user (non-admin) exists.
    - WHEN: Submit a GET request to `/api/admin/users` with user token.
    - THEN: A 403 Forbidden error is returned.

### 13. Token Refresh
  - [ ] **Token Refresh**: User can refresh an expiring JWT.
    - GIVEN: An authenticated user has a valid refresh token.
    - WHEN: Submit a POST request to `/api/auth/refresh` with valid refresh token.
    - THEN: A new access token is returned.
