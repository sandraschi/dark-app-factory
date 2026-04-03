Here is the generated `scenarios.md` file:

## Scenarios
-------------

### Happy Paths
--------------

*   [ ] **Successful Task Creation**
    - GIVEN: A user is logged in and has no existing tasks
    - WHEN: Submit a POST request to `/tasks` with valid JSON payload (e.g. `{ "title": "Buy groceries", "status": "active", "priority": "normal" }`)
    - THEN: The task is created successfully, and the response contains the newly created task object

*   [ ] **Successful Task Retrieval**
    - GIVEN: A user is logged in and has existing tasks
    - WHEN: Submit a GET request to `/tasks`
    - THEN: A list of tasks for the current user is returned, including their status and priority

### Edge Cases
--------------

*   [ ] **Invalid User Data Submission**
    - GIVEN: An invalid or missing user ID in the request headers
    - WHEN: Attempt to create a new task with an invalid user ID
    - THEN: A 401 Unauthorized error is returned, along with a message indicating that authentication is required

*   [ ] **Duplicate Task Submission**
    - GIVEN: A user attempts to submit a duplicate task title
    - WHEN: Submit a POST request to `/tasks` with a title already in use by another task
    - THEN: The task creation fails, and the response contains an error message indicating that the title is already taken

### Error States
--------------

*   [ ] **Task Status Transition Failure**
    - GIVEN: A user attempts to transition a task from `active` to `shadow`
    - WHEN: Submit a POST request to `/tasks/<task_id>` with the `status` parameter set to `shadow`
    - THEN: The task status is not updated, and an error message is returned indicating that the transition failed

*   [ ] **Database Connection Failure**
    - GIVEN: A database connection issue
    - WHEN: Submit a request to any endpoint
    - THEN: An internal server error (500) is returned, along with an error message indicating that the database is unavailable

### Security Boundaries
---------------------

*   [ ] **Unauthorized Access Attempt**
    - GIVEN: An unauthorized user attempts to access protected endpoints
    - WHEN: Submit a request to any endpoint without valid authentication credentials
    - THEN: A 401 Unauthorized error is returned, along with an error message indicating that authentication is required

*   [ ] **Cross-Site Request Forgery (CSRF) Attack**
    - GIVEN: An attacker attempts to simulate a legitimate user session by sending a request with a forged CSRF token
    - WHEN: Submit a request to any endpoint with a forged CSRF token
    - THEN: The request is rejected, and an error message is returned indicating that the CSRF token is invalid