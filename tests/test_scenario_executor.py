"""Tests for the scenario executor module."""

import pytest

from src.verification.scenario_parser import (
    Assertion,
    HttpAction,
    Scenario,
    ScenarioType,
)
from src.verification.scenario_executor import (
    ScenarioResult,
    _evaluate_api_assertion,
    _generate_sample_body,
    _resolve_path,
    execute_all_scenarios,
)


# ---------------------------------------------------------------------------
# Path resolution
# ---------------------------------------------------------------------------


class TestResolvePath:
    def test_replaces_id(self):
        assert _resolve_path("/users/{id}") == "/users/1"

    def test_no_replacement_needed(self):
        assert _resolve_path("/users") == "/users"


# ---------------------------------------------------------------------------
# Sample body generation
# ---------------------------------------------------------------------------


class TestGenerateSampleBody:
    def _make_scenario(self, title, given="", body_hint="valid"):
        return Scenario(
            title=title,
            description="",
            category="",
            given=given,
            when="",
            then="",
            http_action=HttpAction(method="POST", path="/test", body_hint=body_hint),
        )

    def test_user_body(self):
        s = self._make_scenario("Create New User")
        body = _generate_sample_body(s.http_action, s)
        assert "username" in body
        assert "password" in body

    def test_invalid_user_body(self):
        s = self._make_scenario(
            "Invalid Credentials", given="invalid credentials", body_hint="invalid"
        )
        body = _generate_sample_body(s.http_action, s)
        # Falls through to fallback for unrecognized title
        assert "name" in body
        assert "description" in body

    def test_treatment_body(self):
        s = self._make_scenario("Create New Treatment")
        body = _generate_sample_body(s.http_action, s)
        assert "title" in body

    def test_appointment_body(self):
        s = self._make_scenario("Create New Appointment")
        body = _generate_sample_body(s.http_action, s)
        assert "user_id" in body

    def test_get_returns_none(self):
        s = self._make_scenario("List Users")
        s.http_action.method = "GET"
        body = _generate_sample_body(s.http_action, s)
        assert body is None

    def test_fallback_body(self):
        s = self._make_scenario("Something Unknown")
        body = _generate_sample_body(s.http_action, s)
        assert "name" in body


# ---------------------------------------------------------------------------
# API assertion evaluation
# ---------------------------------------------------------------------------


class TestEvaluateApiAssertion:
    def test_status_code_match(self):
        s = Scenario(
            title="Test",
            description="",
            category="",
            given="",
            when="",
            then="",
            assertion=Assertion(raw_text="", expected_status=200),
        )
        r = ScenarioResult(scenario_title="Test", scenario_type="api", executed=True, status_code=200)
        _evaluate_api_assertion(s, r)
        assert r.assertion_met is True
        assert r.confidence > 0.5

    def test_status_code_class_match(self):
        s = Scenario(
            title="Test",
            description="",
            category="",
            given="",
            when="",
            then="",
            assertion=Assertion(raw_text="", expected_status=200),
        )
        r = ScenarioResult(scenario_title="Test", scenario_type="api", executed=True, status_code=201)
        _evaluate_api_assertion(s, r)
        assert r.assertion_met is True  # Same 2xx class

    def test_status_code_mismatch(self):
        s = Scenario(
            title="Test",
            description="",
            category="",
            given="",
            when="",
            then="",
            assertion=Assertion(raw_text="", expected_status=200),
        )
        r = ScenarioResult(scenario_title="Test", scenario_type="api", executed=True, status_code=404)
        _evaluate_api_assertion(s, r)
        assert r.assertion_met is False

    def test_list_response_array(self):
        s = Scenario(
            title="Test",
            description="",
            category="",
            given="",
            when="",
            then="",
            assertion=Assertion(raw_text="", expects_list=True),
        )
        r = ScenarioResult(
            scenario_title="Test",
            scenario_type="api",
            executed=True,
            status_code=200,
            response_body='[{"id": 1}]',
        )
        _evaluate_api_assertion(s, r)
        assert r.assertion_met is True

    def test_error_response(self):
        s = Scenario(
            title="Test",
            description="",
            category="",
            given="",
            when="",
            then="",
            assertion=Assertion(raw_text="", expects_error=True, expected_status=404),
        )
        r = ScenarioResult(scenario_title="Test", scenario_type="api", executed=True, status_code=404)
        _evaluate_api_assertion(s, r)
        assert r.assertion_met is True

    def test_no_assertion(self):
        s = Scenario(
            title="Test",
            description="",
            category="",
            given="",
            when="",
            then="",
            assertion=None,
        )
        r = ScenarioResult(scenario_title="Test", scenario_type="api", executed=True, status_code=200)
        _evaluate_api_assertion(s, r)
        assert r.assertion_met is None
        assert r.confidence == 0.0


# ---------------------------------------------------------------------------
# Full scenario execution (mocked HTTP)
# ---------------------------------------------------------------------------


class TestExecuteAllScenarios:
    @pytest.fixture
    def api_scenario(self):
        return Scenario(
            title="Create User",
            description="Test",
            category="User Management",
            given="No users",
            when="POST /users",
            then="User created",
            scenario_type=ScenarioType.API,
            http_action=HttpAction(method="POST", path="/users", body_hint="valid"),
            assertion=Assertion(raw_text="User created", expects_creation=True),
        )

    @pytest.fixture
    def static_scenario(self):
        return Scenario(
            title="Data Encryption",
            description="AES-256",
            category="Security",
            given="User with data",
            when="GET /users/{id}",
            then="Encrypted",
            scenario_type=ScenarioType.STATIC,
        )

    @pytest.mark.asyncio
    async def test_static_scenario_skipped(self, static_scenario):
        results = await execute_all_scenarios(
            [static_scenario], "http://localhost:3000"
        )
        assert len(results) == 1
        assert results[0].skipped_reason
        assert not results[0].executed

    @pytest.mark.asyncio
    async def test_api_scenario_connection_error(self, api_scenario):
        """If app is not running, scenario records a connection error."""
        results = await execute_all_scenarios([api_scenario], "http://localhost:99999")
        assert len(results) == 1
        # Should have attempted execution
        assert results[0].executed is True
        assert results[0].error  # Connection refused
