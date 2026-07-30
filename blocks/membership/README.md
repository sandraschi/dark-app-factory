# Membership Block

User registration, JWT authentication, role-based access control, and member/customer/employee management with SQLite.

**Triggers**: member, register, login, auth, user, role, profile, club, org, society, employee, customer, team, signup, account

**Env vars**:
| Variable | Default | Description |
|----------|---------|-------------|
| `JWT_SECRET` | `change-me-to-a-random-secret` | Secret key for JWT signing |
| `JWT_ALGORITHM` | `HS256` | JWT signing algorithm |

**API endpoints**: `/api/auth/register`, `/api/auth/login`, `/api/auth/me`, `/api/members`, `/api/customers`, `/api/employees`

**Dependencies**: `pip: python-jose[cryptography]>=3.3.0, aiosqlite>=0.20.0`
