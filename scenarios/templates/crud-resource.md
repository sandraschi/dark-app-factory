# Generic CRUD Resource Scenario Templates
# ==========================================
# Replace {resource} with your resource name (users, items, posts, etc.)
# Replace /{resource} with your actual path (e.g. /users, /api/items).

## Create

### 1. Create Resource
  - [ ] **Create {Resource}**: A new resource can be created with valid data.
    - GIVEN: No resource exists with the given unique identifier.
    - WHEN: Submit a POST request to `/{resource}` with valid JSON payload.
    - THEN: The new resource is created, and its details are returned.

### 2. Create Duplicate Fails
  - [ ] **Create Duplicate Rejected**: Creating a duplicate (e.g. same email) returns conflict.
    - GIVEN: A resource already exists with the same unique field.
    - WHEN: Submit a POST request to `/{resource}` with duplicate data.
    - THEN: A 409 Conflict or 422 Unprocessable Entity error is returned.

### 3. Create Validation Error
  - [ ] **Create Validation Error**: Invalid or missing required fields are rejected.
    - GIVEN: No resource exists.
    - WHEN: Submit a POST request to `/{resource}` with invalid or incomplete JSON payload.
    - THEN: A 400 Bad Request or 422 Unprocessable Entity error is returned.

## Read

### 4. List Resources
  - [ ] **List {Resources}**: A list of resources can be retrieved.
    - GIVEN: Multiple resources exist in the system.
    - WHEN: Submit a GET request to `/{resource}`.
    - THEN: The list of resources is returned, including IDs and key fields.

### 5. Get Resource By ID
  - [ ] **Get {Resource} By ID**: A single resource can be retrieved by ID.
    - GIVEN: A resource exists with ID 1.
    - WHEN: Submit a GET request to `/{resource}/1`.
    - THEN: The resource details are returned.

### 6. Resource Not Found
  - [ ] **{Resource} Not Found**: Requesting a non-existent resource returns 404.
    - GIVEN: No resource exists with ID 999.
    - WHEN: Submit a GET request to `/{resource}/999`.
    - THEN: A 404 Not Found error is returned.

### 7. Pagination (Optional)
  - [ ] **List Paginated**: List endpoint supports pagination parameters.
    - GIVEN: More than 10 resources exist.
    - WHEN: Submit a GET request to `/{resource}?page=2&limit=10`.
    - THEN: The second page of resources is returned.

## Update

### 8. Update Resource
  - [ ] **Update {Resource}**: An existing resource can be updated.
    - GIVEN: A resource exists with ID 1.
    - WHEN: Submit a PUT request to `/{resource}/1` with valid JSON payload.
    - THEN: The resource is updated, and the updated details are returned.

### 9. Partial Update (PATCH)
  - [ ] **Partial Update {Resource}**: A resource can be partially updated via PATCH.
    - GIVEN: A resource exists with ID 1.
    - WHEN: Submit a PATCH request to `/{resource}/1` with partial JSON payload.
    - THEN: Only the provided fields are updated, and the resource is returned.

### 10. Update Non-Existent Fails
  - [ ] **Update Non-Existent Returns 404**: Updating a non-existent resource fails.
    - GIVEN: No resource exists with ID 999.
    - WHEN: Submit a PUT request to `/{resource}/999` with valid payload.
    - THEN: A 404 Not Found error is returned.

## Delete

### 11. Delete Resource
  - [ ] **Delete {Resource}**: An existing resource can be deleted.
    - GIVEN: A resource exists with ID 1.
    - WHEN: Submit a DELETE request to `/{resource}/1`.
    - THEN: The resource is deleted, and 204 No Content or 200 OK is returned.

### 12. Delete Non-Existent (Idempotent)
  - [ ] **Delete Non-Existent**: Deleting a non-existent resource returns 404 or 204 (idempotent).
    - GIVEN: No resource exists with ID 999.
    - WHEN: Submit a DELETE request to `/{resource}/999`.
    - THEN: A 404 Not Found error is returned, or 204 No Content (idempotent delete).
