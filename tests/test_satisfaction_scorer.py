"""Tests for the satisfaction scorer module."""

import pytest
from unittest.mock import AsyncMock

from src.verification.scenario_parser import (
    Assertion,
    HttpAction,
    Scenario,
    ScenarioType,
)
from src.verification.scenario_executor import ScenarioResult
from src.verification.satisfaction_scorer import (
    SatisfactionReport,
    _score_mechanical,
    compute_satisfaction,
)


# ---------------------------------------------------------------------------
# Mechanical scoring
# ---------------------------------------------------------------------------


class TestScoreMechanical:
    def test_not_executed_scores_zero(self):
        result = ScenarioResult(
            scenario_title="Test", scenario_type="api", executed=False, skipped_reason="No httpx"
        )
        score = _score_mechanical(result)
        assert score.satisfaction == 0.0
        assert score.method == "skipped"

    def test_connection_error_low_score(self):
        result = ScenarioResult(
            scenario_title="Test",
            scenario_type="api",
            executed=True,
            error="Connection refused",
            status_code=None,
        )
        score = _score_mechanical(result)
        assert score.satisfaction == 0.1
        assert score.confidence == 0.7

    def test_assertion_passed(self):
        result = ScenarioResult(
            scenario_title="Test",
            scenario_type="api",
            executed=True,
            status_code=200,
            assertion_met=True,
            confidence=0.9,
            assertion_evidence="Status matched",
        )
        score = _score_mechanical(result)
        assert score.satisfaction == 0.9
        assert score.method == "mechanical"

    def test_assertion_failed_not_500(self):
        result = ScenarioResult(
            scenario_title="Test",
            scenario_type="api",
            executed=True,
            status_code=422,
            assertion_met=False,
            confidence=0.8,
            assertion_evidence="Schema mismatch",
        )
        score = _score_mechanical(result)
        assert score.satisfaction == 0.2  # Partial credit for non-500
        assert score.method == "mechanical"

    def test_assertion_failed_500(self):
        result = ScenarioResult(
            scenario_title="Test",
            scenario_type="api",
            executed=True,
            status_code=500,
            assertion_met=False,
            confidence=0.9,
            assertion_evidence="Internal server error",
        )
        score = _score_mechanical(result)
        assert score.satisfaction == 0.05  # Very low

    def test_ambiguous_assertion(self):
        result = ScenarioResult(
            scenario_title="Test",
            scenario_type="api",
            executed=True,
            status_code=200,
            assertion_met=None,
            confidence=0.3,
            assertion_evidence="Ambiguous",
        )
        score = _score_mechanical(result)
        assert score.satisfaction == 0.5  # Neutral prior
        assert score.confidence == 0.3


# ---------------------------------------------------------------------------
# Report serialization
# ---------------------------------------------------------------------------


class TestSatisfactionReport:
    def test_to_dict(self):
        report = SatisfactionReport(
            total_scenarios=5,
            executed=3,
            skipped=2,
            overall_satisfaction=0.75,
            verdict="SATISFACTORY",
        )
        d = report.to_dict()
        assert d["total_scenarios"] == 5
        assert d["overall_satisfaction"] == 0.75
        assert d["verdict"] == "SATISFACTORY"

    def test_summary_text(self):
        report = SatisfactionReport(
            total_scenarios=5,
            executed=3,
            skipped=2,
            overall_satisfaction=0.75,
            overall_confidence=0.8,
            mechanical_satisfaction=0.7,
            verdict="SATISFACTORY",
        )
        text = report.summary_text()
        assert "SATISFACTORY" in text
        assert "75.0%" in text


# ---------------------------------------------------------------------------
# Full satisfaction computation (no LLM)
# ---------------------------------------------------------------------------


class TestComputeSatisfaction:
    @pytest.fixture
    def scenarios_and_results(self):
        s1 = Scenario(
            title="Create User",
            description="",
            category="User Management",
            given="",
            when="",
            then="",
            scenario_type=ScenarioType.API,
            assertion=Assertion(raw_text="created", expects_creation=True),
        )
        r1 = ScenarioResult(
            scenario_title="Create User",
            scenario_type="api",
            executed=True,
            status_code=201,
            assertion_met=True,
            confidence=1.0,
            assertion_evidence="Status 201, creation confirmed",
        )

        s2 = Scenario(
            title="List Users",
            description="",
            category="User Management",
            given="",
            when="",
            then="",
            scenario_type=ScenarioType.API,
            assertion=Assertion(raw_text="list returned", expects_list=True),
        )
        r2 = ScenarioResult(
            scenario_title="List Users",
            scenario_type="api",
            executed=True,
            status_code=200,
            response_body='[{"id": 1}]',
            assertion_met=True,
            confidence=1.0,
            assertion_evidence="JSON array returned",
        )

        s3 = Scenario(
            title="Encryption",
            description="",
            category="Security",
            given="",
            when="",
            then="",
            scenario_type=ScenarioType.STATIC,
        )
        r3 = ScenarioResult(
            scenario_title="Encryption",
            scenario_type="static",
            skipped_reason="Static scenario",
        )

        return [s1, s2, s3], [r1, r2, r3]

    @pytest.mark.asyncio
    async def test_mechanical_only(self, scenarios_and_results):
        scenarios, results = scenarios_and_results
        report = await compute_satisfaction(scenarios, results, llm_client=None)
        assert report.total_scenarios == 3
        assert report.executed == 2
        assert report.skipped == 1
        assert report.verdict == "SATISFACTORY"
        assert report.overall_satisfaction > 0.6

    @pytest.mark.asyncio
    async def test_all_failed(self):
        s = Scenario(
            title="Fail",
            description="",
            category="Test",
            given="",
            when="",
            then="",
            scenario_type=ScenarioType.API,
            assertion=Assertion(raw_text="fail", expected_status=200),
        )
        r = ScenarioResult(
            scenario_title="Fail",
            scenario_type="api",
            executed=True,
            status_code=500,
            assertion_met=False,
            confidence=0.9,
            assertion_evidence="500 error",
        )
        report = await compute_satisfaction([s], [r], llm_client=None)
        assert report.verdict == "UNSATISFACTORY"
        assert report.overall_satisfaction < 0.3

    @pytest.mark.asyncio
    async def test_category_breakdown(self, scenarios_and_results):
        scenarios, results = scenarios_and_results
        report = await compute_satisfaction(scenarios, results, llm_client=None)
        assert "User Management" in report.category_scores
        assert report.category_scores["User Management"] > 0.5

    @pytest.mark.asyncio
    async def test_empty_scenarios(self):
        report = await compute_satisfaction([], [], llm_client=None)
        assert report.verdict == "UNDETERMINED"
        assert report.total_scenarios == 0

    @pytest.mark.asyncio
    async def test_with_mock_llm(self):
        """Ambiguous scenario triggers LLM evaluation."""
        s = Scenario(
            title="Ambiguous",
            description="",
            category="Test",
            given="",
            when="POST /test",
            then="Something happens",
            scenario_type=ScenarioType.API,
            http_action=HttpAction(method="POST", path="/test"),
            assertion=Assertion(raw_text="Something happens"),
        )
        r = ScenarioResult(
            scenario_title="Ambiguous",
            scenario_type="api",
            executed=True,
            status_code=200,
            response_body='{"ok": true}',
            assertion_met=None,
            confidence=0.3,
            assertion_evidence="Ambiguous assertion",
        )

        mock_llm = AsyncMock()
        mock_llm.generate = AsyncMock(
            return_value="SCORE: 0.8\nREASONING: Response looks correct"
        )

        report = await compute_satisfaction(
            [s], [r], llm_client=mock_llm, llm_confidence_threshold=0.5
        )
        # LLM should have been called (confidence 0.3 < threshold 0.5)
        mock_llm.generate.assert_called_once()
        # Score should reflect LLM evaluation
        assert report.scores[0].method == "llm_assisted"
        assert report.scores[0].satisfaction == 0.8
