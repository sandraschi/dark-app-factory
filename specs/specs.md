<!-- STACK_PROFILE: {"backend": "node/express", "frontend": "react", "database": "sqlite"} -->

# Technical Specifications: Apis-Bee Management & E-Commerce Suite

**Project Codename:** "Hollabrunn_Hive_Core"  
**Owner:** Julius Stich  
**Status:** Production-Ready Specification  
**Architecture:** Monolithic Backend (Node/Express), Decoupled Frontend (React/Vite)

---

## 1. System Architecture & Core Logic
The system is split into two distinct logical zones to prevent "Route Bleed" (the primary cause of previous failures):
1.  **Public Zone (Webshop):** A customer-facing storefront for purchasing honey and bee products.
2.  **Admin/Management Portal:** A private dashboard for Julius to manage inventory, view hive telemetry (IoT), and plan swarming cycles.

### State Machines
*   **Order Lifecycle:** `Pending` $\rightarrow$ `Paid` $\rightarrow$ `Processing` $\rightarrow$ `Shipped` $\rightarrow$ `Delivered`.
*   **Hive Status:** `Active` $\rightarrow$ `Swarming_Alert` $\rightarrow$ `Maintenance_Required` $\rightarrow$ `Winter_Dormant`.
*   **Telemetry Stream:** Buffer data every 5 minutes for temperature readings to optimize database write frequency.

---

## 2. Core Data Models (Sequelize/SQLite)

### User & Auth
- **User**: `id`, `email`, `password_hash`, `role` (ENUM: 'admin', 'customer'), `name`.
- **Address**: `id`, `user_id`, `street`, `city`, `postal_code`.

### E-Commerce (The Store)
- **Product**: 
    - `id`: UUID
    - `name`: String
    - `description`: Text
    - `price`: Decimal(10,2)
    - `stock_count`: Integer
    - `category`: Enum('honey', 'wax', 'equipment')
- **Order**: 
    - `id`: UUID
    - `customer_id`: FK $\rightarrow$ User
    - `total_amount`: Decimal
    - `status`: String (see State Machine)

### Hive Management & IoT
- **Hive**: 
    - `id`: Integer
    - `identifier`: String (e.g., "Hollabrunn_01")
    - `gps_coords`: Point(x,y)
    - `last_checked`: Timestamp
- **SensorReading**:
    - `hive_id`: FK $\rightarrow$ Hive
    - `temperature`: Float
    - `humidity`: Float (optional)
    - `timestamp`: DateTime
- **SwarmEvent**:
    - `hive_id`: FK $\rightarrow$ Hive
    - `scheduled_date`: Date
    - `status`: Enum('planned', 'observed', 'completed')

---

## 3. API Endpoints (RESTful)

### Public Store API (`/api/v1/shop`)
| Method | Endpoint | Description | Success Response |
| :--- | :--- | :--- | :--- |
| GET | `/products` | Fetch all available products | `200 OK [{id, name, price...}]` |
| GET | `/products/:id` | Get specific product details | `200 OK {data}` |
| POST | `/checkout` | Create order and process payment | `201 Created {"order_id": "..."}` |

### Management API (`/api/v1/admin`)
| Method | Endpoint | Description | Requirement |
| :--- | :--- | :--- | :--- |
| GET | `/hives` | List all hives and statuses | Admin Only |
| GET | `/hives/:id/telemetry` | Get last 24h temperature data | Admin Only |
| POST | `/inventory` | Update stock levels for products | Admin Only |
| POST | `/swarms` | Log or schedule a swarming event | Admin Only |

---

## 4. Frontend View Specifications (React + Tailwind)

### View 1: Public Storefront (`/shop`)
- **Components**: `ProductGrid`, `CategoryFilter`, `CartCounter`.
- **Interactions**: Filter by honey type, "Add to Cart" modal with quantity selection.
- **State Management**: Local state for cart persistence via `localStorage`.

### View 2: Julius's Dashboard (`/dashboard`)
- **Components**: `HiveStatusCard` (Visual status indicators), `TelemetryGraph` (Recharts integration).
- **Logic**: If temperature > 40°C or < 10°C, trigger a visual "Warning" alert on the dashboard.

### View 3: Inventory & Books (`/admin/inventory`)
- **Components**: `DataTable`, `StockAlertBadge`.
- **Functionality**: A table of all products with an "Edit Stock" button that opens a modal to update numbers instantly via a PUT request.

### View 4: Swarming Calendar (`/admin/calendar`)
- **Components**: `CalendarView` (FullCalendar or custom grid).
- **Interaction**: Click a date to open a form: "Select Hive", "Note for Observation".

---

## 5. Digital Twin & Integrations

### IoT Integration (The "HiveTwin")
To provide real-time data from the physical hives in Hollabrunn, the following logic is implemented:
1.  **Temperature Probes**: Connect via **MQTT Broker** or an **HTTP Gateway**. The backend polls these values every 60 seconds and updates the `SensorReading` table.
2.  **HiveCams**: Integration with IP Camera streams (RTSP/RTMP). The frontend will embed a WebRTC stream or an MJPEG proxy for Julius to view live feed on his dashboard.
3.  **Digital Twin Logic**: Each physical hive is represented by a "Twin" object in the database. This twin holds state (Temperature, Humidity, Population Estimate) which mirrors the real-world conditions.

---

## 6. Implementation & Deployment Plan

### Step 1: Database Seeding
Initialize the SQLite schema including `Hollabrunn` specific locations and default inventory for "Pure Honey".

### Step 2: API Development
Build the Express routes first. Ensure strict validation on the `/checkout` route to prevent invalid orders from hitting the database.

### Step 3: UI Construction
Use **Framer Motion** for smooth transitions between the Store pages and the Dashboard (ensuring a "Premium" feel).

---

## 7. README_TEMPLATE

```markdown
# Hollabrunn Hive Management System

## Overview
A dual-purpose platform for Julius Stich, featuring an e-commerce front-end and a high-tech hive management back-end.

## Tech Stack
- **Backend**: Node.js, Express, Sequelize (SQLite)
- **Frontend**: React 18, Vite, TypeScript, Tailwind CSS
- **Animations**: Framer Motion

## Setup Instructions
1. **Clone & Install**: `npm install` in both `/client` and `/server` folders.
2. **Environment Variables**: Create `.env` for:
   - `PORT=3000`
   - `JWT_SECRET=your_secret_key`
   - `MQTT_BROKER_URL=your_broker_url`
3. **Database Migration**: Run `npx sequelize-cli db:migrate`.
4. **First Time Setup**: 
    - Create an admin account for Julius via the `/register` route or seed script.
    - Configure Hive IDs to match physical tags in the yard.

## Digital Twin Integration
The system treats each hive as a 'Digital Twin'. To sync your hardware:
1. Connect temperature probes to the local gateway.
2. Map the Gateway IP in `config/devices.json`.
3. The backend will automatically map incoming telemetry to the correct Hive ID based on unique MAC addresses.

## Deployment
- **Frontend**: Deploy via Vercel or Netlify (Static Build).
- **Backend**: Deploy on a private VPS or local server for low-latency IoT polling.
```