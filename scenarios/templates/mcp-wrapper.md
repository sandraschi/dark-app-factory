# MCP + Webapp Wrapper Scenario Template
# ==========================================
# For apps that wrap a Windows executable with MCP tools + web dashboard.
# Replace {app} with app name (vlc, 7zip, etc.). Replace /api/... with your paths.

## MCP Tool Parity (API)

### 1. Control Action via API
  - [ ] **Control via API**: Webapp and MCP share the same backend; API mirrors MCP tools.
    - GIVEN: Backend is running with wrappee (e.g. VLC, 7z) available.
    - WHEN: Submit a POST request to `/api/{app}/control` with valid JSON (action, params).
    - THEN: The action is executed and status is returned.

### 2. Status Endpoint
  - [ ] **Status Endpoint**: Status can be retrieved via API.
    - GIVEN: Backend is running.
    - WHEN: Submit a GET request to `/api/{app}/status`.
    - THEN: JSON with current state (e.g. playing, idle, error) is returned.

### 3. Health Check
  - [ ] **Health Check**: Backend reports health including wrappee availability.
    - GIVEN: Backend is running.
    - WHEN: Submit a GET request to `/health`.
    - THEN: JSON includes `wrappee_available` or similar field.

## Web UI

### 4. Dashboard Loads
  - [ ] **Dashboard Loads**: Main page renders without error.
    - GIVEN: Frontend and backend are running.
    - WHEN: Navigate to the root URL.
    - THEN: The dashboard or control UI is visible.

### 5. Control Button Triggers API
  - [ ] **Control Button Works**: Clicking a control (e.g. Play, Pause) calls the API.
    - GIVEN: Dashboard is loaded.
    - WHEN: User clicks a control button (e.g. Play).
    - THEN: A request is sent to the backend and the UI updates (or shows feedback).

## Error Handling

### 6. Wrappee Not Found
  - [ ] **Wrappee Not Found**: Clear error when executable is missing.
    - GIVEN: Backend is configured with invalid wrappee path (or wrappee not installed).
    - WHEN: Submit a POST request to `/api/{app}/control` with a valid action.
    - THEN: A 503 or 500 with clear message (e.g. "VLC not found") is returned.
