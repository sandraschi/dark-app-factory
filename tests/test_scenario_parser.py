"""Tests for the scenario parser module."""

from src.verification.scenario_parser import (
    HttpAction,
    ScenarioType,
    classify_scenario,
    parse_assertion,
    parse_http_action,
    parse_scenarios,
)


# ---------------------------------------------------------------------------
# HTTP Action parsing
# ---------------------------------------------------------------------------


class TestParseHttpAction:
    def test_post_request(self):
        action = parse_http_action(
            "Submit a POST request to `/users` with valid JSON payload."
        )
        assert action is not None
        assert action.method == "POST"
        assert action.path == "/users"
        assert action.body_hint == "valid"

    def test_get_request(self):
        action = parse_http_action("Submit a GET request to `/treatments`.")
        assert action is not None
        assert action.method == "GET"
        assert action.path == "/treatments"
        assert action.body_hint == ""

    def test_put_request_with_id(self):
        action = parse_http_action(
            "Submit a PUT request to `/users/{id}` with valid JSON payload."
        )
        assert action is not None
        assert action.method == "PUT"
        assert action.path == "/users/{id}"

    def test_get_put_combo_takes_first(self):
        action = parse_http_action(
            "Submit GET/PUT requests to `/treatments/{id}` with invalid ID `123`."
        )
        assert action is not None
        assert action.method == "GET"
        assert action.path == "/treatments/{id}"

    def test_invalid_credentials_body(self):
        action = parse_http_action(
            "Submit a POST request to `/users/login` with invalid JSON payload."
        )
        assert action is not None
        assert action.body_hint == "invalid"

    def test_duplicate_body(self):
        action = parse_http_action(
            "Submit a POST request to `/appointments` with valid JSON payload "
            "duplicating an existing appointment."
        )
        assert action is not None
        assert action.body_hint == "duplicate"

    def test_no_match(self):
        action = parse_http_action("Click the login button.")
        assert action is None


# ---------------------------------------------------------------------------
# Assertion parsing
# ---------------------------------------------------------------------------


class TestParseAssertion:
    def test_creation_assertion(self):
        a = parse_assertion(
            "The new user is created, and an email confirmation link is sent."
        )
        assert a.expects_creation is True
        assert a.expected_status == 201

    def test_list_assertion(self):
        a = parse_assertion(
            "The list of users is returned, including user IDs and names."
        )
        assert a.expects_list is True

    def test_error_404(self):
        a = parse_assertion("A 404 Not Found error is returned.")
        assert a.expects_error is True
        assert a.expected_status == 404

    def test_error_409(self):
        a = parse_assertion("A 409 Conflict error is returned.")
        assert a.expects_error is True
        assert a.expected_status == 409

    def test_rejection(self):
        a = parse_assertion(
            "The login attempt is rejected, and an error message is returned."
        )
        assert a.expects_rejection is True
        assert a.expects_error is True

    def test_forbidden(self):
        a = parse_assertion("A 403 Forbidden error is returned.")
        assert a.expects_error is True
        assert a.expected_status == 403


# ---------------------------------------------------------------------------
# Scenario classification
# ---------------------------------------------------------------------------


class TestClassifyScenario:
    def test_api_with_http_action(self):
        action = HttpAction(method="GET", path="/users")
        assert classify_scenario(action, "list returned") == ScenarioType.API

    def test_static_encryption(self):
        assert (
            classify_scenario(None, "data is returned encrypted") == ScenarioType.STATIC
        )

    def test_browser_fallback(self):
        assert (
            classify_scenario(None, "the page loads successfully")
            == ScenarioType.BROWSER
        )


# ---------------------------------------------------------------------------
# Full scenario parsing
# ---------------------------------------------------------------------------


class TestParseScenarios:
    SAMPLE_MD = """# User Scenarios
================

## User Management

### 1. Create New User
  - [ ] **Create New User**: A new user can be created with valid credentials.
    - GIVEN: No users exist in the system.
    - WHEN: Submit a POST request to `/users` with valid JSON payload.
    - THEN: The new user is created, and an email confirmation link is sent.

### 2. Retrieve List of Users
  - [ ] **Retrieve List of Users**: A list of all users can be retrieved.
    - GIVEN: Multiple users exist in the system.
    - WHEN: Submit a GET request to `/users`.
    - THEN: The list of users is returned, including user IDs and names.

## Security Scenarios

### 1. Invalid Credentials
  - [ ] **Invalid Credentials**: Login with invalid credentials should be rejected.
    - GIVEN: An existing user exists in the system with invalid credentials.
    - WHEN: Submit a POST request to `/users/login` with invalid JSON payload.
    - THEN: The login attempt is rejected, and an error message is returned.

## Security Boundaries

### 1. Data Encryption
  - [ ] **Data Encryption**: All sensitive data should be encrypted using AES-256.
    - GIVEN: An existing user exists in the system with sensitive data.
    - WHEN: Submit a GET request to `/users/{id}` with valid ID `123`.
    - THEN: The sensitive data is returned encrypted.
"""

    def test_parses_correct_count(self):
        scenarios = parse_scenarios(self.SAMPLE_MD)
        assert len(scenarios) == 4

    def test_first_scenario_structure(self):
        scenarios = parse_scenarios(self.SAMPLE_MD)
        s = scenarios[0]
        assert s.title == "Create New User"
        assert s.category == "User Management"
        assert s.scenario_type == ScenarioType.API
        assert s.http_action is not None
        assert s.http_action.method == "POST"
        assert s.http_action.path == "/users"

    def test_category_tracking(self):
        scenarios = parse_scenarios(self.SAMPLE_MD)
        categories = [s.category for s in scenarios]
        assert "User Management" in categories
        assert "Security Scenarios" in categories
        assert "Security Boundaries" in categories

    def test_static_scenario_detected(self):
        scenarios = parse_scenarios(self.SAMPLE_MD)
        encryption = [s for s in scenarios if "Encryption" in s.title]
        assert len(encryption) == 1
        assert encryption[0].scenario_type == ScenarioType.STATIC

    def test_security_scenario_assertion(self):
        scenarios = parse_scenarios(self.SAMPLE_MD)
        invalid = [s for s in scenarios if "Invalid" in s.title][0]
        assert invalid.assertion.expects_rejection is True
        assert invalid.assertion.expects_error is True

    def test_empty_input(self):
        scenarios = parse_scenarios("")
        assert scenarios == []

    def test_no_gwt_lines(self):
        scenarios = parse_scenarios("## Category\n### Title\nJust some text.")
        assert scenarios == []
