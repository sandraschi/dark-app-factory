# Skill: IoT Dashboard & Device Management (2026 SOTA)

## 1. Domain Context
Real-time monitoring and control of connected devices: sensors, actuators, smart home hardware, industrial PLCs, robotics.
Covers MQTT, WebSocket, REST polling, and SSE ingestion patterns.
Can power: home automation dashboard, factory floor monitor, greenhouse controller, robotics telemetry HUD.

## 2. Mandatory Pages & Routes
- `/` — Live dashboard: device cards with real-time metric tiles, alert badges, map (if GPS devices)
- `/devices` — Device registry: list with online/offline status, last-seen, signal strength
- `/devices/new` — Register device: name, type, location, MQTT topic prefix or API key
- `/devices/:id` — Device detail: live telemetry stream, historical charts, command console, event log
- `/rules` — Automation rules: if sensor_value > threshold → trigger action (email, webhook, command)
- `/alerts` — Alert history: severity, device, value, acknowledged status
- `/settings` — MQTT broker config, polling intervals, notification preferences

## 3. Data Model (PostgreSQL + TimescaleDB optional)
```sql
devices (id, name, type VARCHAR(50), location VARCHAR(100), online BOOL,
         last_seen_at TIMESTAMPTZ, mqtt_topic_prefix, api_key_hash, metadata JSONB, created_at)
telemetry (time TIMESTAMPTZ NOT NULL, device_id FK, metric VARCHAR(50), value DOUBLE PRECISION, unit VARCHAR(20))
  -- If TimescaleDB: CREATE TABLE telemetry (...); SELECT create_hypertable('telemetry','time');
  -- If plain PG: partition by month or use BRIN index on time
events (id, device_id FK, severity ENUM('info','warning','critical'), message TEXT,
        raw_payload JSONB, acknowledged BOOL, acknowledged_by FK, created_at)
rules (id, device_id FK, metric VARCHAR(50), operator ENUM('gt','lt','eq','ne'), threshold DOUBLE PRECISION,
       action_type ENUM('email','webhook','command'), action_payload JSONB, enabled BOOL)
commands (id, device_id FK, command TEXT, payload JSONB, status ENUM('pending','sent','ack','failed'),
          issued_by FK, issued_at TIMESTAMPTZ, acked_at TIMESTAMPTZ)
```

## 4. Backend Specifics
- MQTT ingestion: `paho-mqtt` (Python) or `mqtt.js` (Node) subscriber; on message → upsert `telemetry` + check rules
- SSE endpoint: `GET /api/devices/:id/stream` — push telemetry updates to frontend every ingest
- Downsampling: `GET /api/devices/:id/telemetry?metric=temp&from=X&to=Y&bucket=5m` — aggregate into time buckets for charts
- Rule engine: evaluated on every telemetry insert; debounce 60s to prevent alert storms
- Command dispatch: write to `commands` table, MQTT publish to `{device.mqtt_topic_prefix}/commands`; device ACKs via MQTT
- Device heartbeat: device publishes to `{prefix}/heartbeat` every 30s; backend marks online; cron marks offline after 90s silence

## 5. Frontend Specifics
- Device cards: coloured border (green=online, red=offline, yellow=warning), current metric value large
- Live charts: Recharts `<LineChart>` or `<AreaChart>` with SSE streaming data; rolling 60-point window
- Metric tiles: animate value change (framer-motion number counter transition)
- Command console: text input + Send button; shows sent commands and ACK status in a scrollable log
- Alert list: sortable by severity, "Acknowledge" button per row, bulk-acknowledge
- Map (if GPS): Leaflet.js with device markers, colour-coded by online status and alert severity

## 6. Real-Time Architecture
- **Python**: FastAPI + `fastapi-sse` for SSE; background `asyncio` task subscribes to MQTT broker and pushes to per-device event queues; SSE handler drains queue
- **Node**: Express + `sse-express`; `mqtt.js` subscriber emits to EventEmitter per device; SSE handler attaches listener
- **Scaling**: Redis pubsub as broker between MQTT worker and SSE handlers when running multiple server instances

## 7. Key Third-Party Integrations (all via env vars)
- `MQTT_BROKER_URL` — MQTT broker (Mosquitto, HiveMQ, EMQX); e.g. `mqtt://localhost:1883`
- `EMAIL_API_URL` — alert notifications
- `WEBHOOK_URL` — outbound webhook actions from rule engine
- `SLACK_WEBHOOK_URL` — optional critical-alert Slack messages

## 8. Applicable Vibes
`smart home`, `greenhouse`, `weather station`, `robotics telemetry`, `factory monitor`, `server rack`, `aquarium controller`, `energy monitor`, `solar panel dashboard`
