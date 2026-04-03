"""
Satisfaction Scorer -- probabilistic evaluation of scenario execution results.

Instead of binary pass/fail, this module computes a "satisfaction rate"
that answers: "How well does the generated app satisfy the specified
usage scenarios?"

Scoring tiers:
  - Mechanical score:  Based on HTTP status codes, response structure,
                       and deterministic assertion checks.
  - LLM-assisted score: For ambiguous assertions that can't be checked
                        mechanically, an LLM evaluates the evidence.
  - Aggregate score:   Weighted combination producing 0.0-1.0.

The output is a SatisfactionReport that the judge can use for its
final verdict instead of (or in addition to) the existing LLM-only
verdict.
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List

from src.verification.scenario_executor import ScenarioResult
from src.verification.scenario_parser import Scenario

logger = logging.getLogger("dark_factory")


@dataclass
class ScenarioScore:
    """Score for a single scenario."""

    title: str
    satisfaction: float  # 0.0 - 1.0
    confidence: float  # 0.0 - 1.0 (how reliable is the score)
    method: str  # "mechanical", "llm_assisted", "skipped"
    reasoning: str = ""
    category: str = ""


@dataclass
class SatisfactionReport:
    """Aggregate satisfaction report across all scenarios."""

    total_scenarios: int = 0
    executed: int = 0
    skipped: int = 0
    errored: int = 0

    # Per-scenario scores
    scores: List[ScenarioScore] = field(default_factory=list)

    # Aggregate metrics
    overall_satisfaction: float = 0.0  # Weighted mean of scenario scores
    overall_confidence: float = 0.0  # Mean confidence across scores
    mechanical_satisfaction: float = 0.0  # Mean of mechanically-scored only
    category_scores: Dict[str, float] = field(default_factory=dict)

    # Threshold-based verdict
    verdict: str = "UNDETERMINED"  # SATISFACTORY / PARTIAL / UNSATISFACTORY
    verdict_threshold: float = 0.6  # Configurable pass threshold

    def to_dict(self) -> dict:
        """Serialize for JSON output or LLM prompt embedding."""
        return {
            "total_scenarios": self.total_scenarios,
            "executed": self.executed,
            "skipped": self.skipped,
            "errored": self.errored,
            "overall_satisfaction": round(self.overall_satisfaction, 3),
            "overall_confidence": round(self.overall_confidence, 3),
            "mechanical_satisfaction": round(self.mechanical_satisfaction, 3),
            "verdict": self.verdict,
            "category_scores": {
                k: round(v, 3) for k, v in self.category_scores.items()
            },
            "scenarios": [
                {
                    "title": s.title,
                    "satisfaction": round(s.satisfaction, 3),
                    "confidence": round(s.confidence, 3),
                    "method": s.method,
                    "reasoning": s.reasoning[:200],
                }
                for s in self.scores
            ],
        }

    def summary_text(self) -> str:
        """Human-readable summary for logs and reports."""
        lines = [
            f"Satisfaction Report: {self.verdict}",
            f"  Overall: {self.overall_satisfaction:.1%} satisfaction "
            f"({self.overall_confidence:.1%} confidence)",
            f"  Mechanical: {self.mechanical_satisfaction:.1%}",
            f"  Scenarios: {self.executed}/{self.total_scenarios} executed, "
            f"{self.skipped} skipped, {self.errored} errored",
        ]
        if self.category_scores:
            lines.append("  Category breakdown:")
            for cat, score in sorted(self.category_scores.items(), key=lambda x: x[1]):
                lines.append(f"    {cat}: {score:.1%}")
        return "\n".join(lines)


def _score_mechanical(result: ScenarioResult) -> ScenarioScore:
    """Score a scenario result using only mechanical checks."""
    if not result.executed:
        return ScenarioScore(
            title=result.scenario_title,
            satisfaction=0.0,
            confidence=0.0,
            method="skipped",
            reasoning=result.skipped_reason or result.error or "Not executed",
        )

    if result.error and not result.status_code:
        # Connection error = endpoint doesn't exist
        # But that's still information: 0.1 satisfaction
        # (the app ran, just doesn't have this endpoint)
        return ScenarioScore(
            title=result.scenario_title,
            satisfaction=0.1,
            confidence=0.7,
            method="mechanical",
            reasoning=f"Connection/execution error: {result.error[:150]}",
        )

    # Use the executor's assertion evaluation
    if result.assertion_met is True:
        return ScenarioScore(
            title=result.scenario_title,
            satisfaction=result.confidence,
            confidence=result.confidence,
            method="mechanical",
            reasoning=result.assertion_evidence,
        )
    elif result.assertion_met is False:
        # Assertion failed, but the app responded -- partial credit
        base = 0.2 if result.status_code and result.status_code < 500 else 0.05
        return ScenarioScore(
            title=result.scenario_title,
            satisfaction=base,
            confidence=result.confidence,
            method="mechanical",
            reasoning=result.assertion_evidence,
        )
    else:
        # Ambiguous -- needs LLM
        return ScenarioScore(
            title=result.scenario_title,
            satisfaction=0.5,  # Neutral prior
            confidence=0.3,  # Low confidence = candidate for LLM
            method="mechanical",
            reasoning=result.assertion_evidence or "Ambiguous assertion",
        )


async def _score_with_llm(
    scenario: Scenario,
    result: ScenarioResult,
    mechanical_score: ScenarioScore,
    llm_client,
) -> ScenarioScore:
    """Use an LLM to evaluate ambiguous assertions.

    Only called when mechanical confidence is below threshold.
    The LLM sees the scenario THEN clause and the actual response,
    and judges on a 0.0-1.0 scale.
    """
    prompt = f"""Evaluate whether this API response satisfies the scenario expectation.

SCENARIO: {scenario.title}
GIVEN: {scenario.given}
WHEN: {scenario.when}
THEN (expected): {scenario.then}

ACTUAL RESPONSE:
  Status Code: {result.status_code}
  Response Body (truncated): {result.response_body[:500]}
  Response Time: {result.response_time_ms}ms
  Execution Error: {result.error or "None"}

MECHANICAL EVALUATION: {mechanical_score.reasoning}

Rate the satisfaction on a scale of 0.0 to 1.0:
  0.0 = completely wrong (endpoint missing, wrong behavior)
  0.3 = endpoint exists but wrong response
  0.5 = partially correct (right idea, wrong details)
  0.7 = mostly correct (minor issues)
  1.0 = fully satisfies the THEN condition

Respond in EXACTLY this format:
SCORE: <number>
REASONING: <one sentence>"""

    try:
        response = await llm_client.generate(
            prompt,
            system_prompt=(
                "You are a QA evaluator. Be precise. "
                "A score of 0.5 means genuinely ambiguous. "
                "Do not be lenient -- if the response clearly "
                "doesn't match, score 0.0-0.3."
            ),
            temperature=0.1,
        )

        # Parse score from response
        score_val = 0.5
        reasoning = mechanical_score.reasoning

        for line in response.strip().split("\n"):
            if line.upper().startswith("SCORE:"):
                try:
                    score_val = float(line.split(":", 1)[1].strip())
                    score_val = max(0.0, min(1.0, score_val))
                except (ValueError, IndexError):
                    pass
            elif line.upper().startswith("REASONING:"):
                reasoning = line.split(":", 1)[1].strip()

        return ScenarioScore(
            title=scenario.title,
            satisfaction=score_val,
            confidence=0.7,  # LLM evaluation has moderate confidence
            method="llm_assisted",
            reasoning=reasoning,
        )

    except Exception as exc:
        logger.warning("LLM scoring failed for '%s': %s", scenario.title, exc)
        return mechanical_score


async def compute_satisfaction(
    scenarios: List[Scenario],
    results: List[ScenarioResult],
    llm_client=None,
    llm_confidence_threshold: float = 0.5,
    pass_threshold: float = 0.6,
) -> SatisfactionReport:
    """Compute the aggregate satisfaction score.

    Args:
        scenarios: Parsed scenarios
        results: Execution results (same order as scenarios)
        llm_client: Optional LLMClient for ambiguous assertion evaluation.
                    If None, only mechanical scoring is used.
        llm_confidence_threshold: If mechanical confidence is below this,
                                  use LLM for re-evaluation.
        pass_threshold: Overall satisfaction >= this = SATISFACTORY.

    Returns:
        SatisfactionReport with per-scenario and aggregate scores.
    """
    report = SatisfactionReport(
        total_scenarios=len(scenarios),
        verdict_threshold=pass_threshold,
    )

    scenario_map = {s.title: s for s in scenarios}

    for result in results:
        if result.executed:
            report.executed += 1
        elif result.skipped_reason:
            report.skipped += 1
        if result.error:
            report.errored += 1

    # Phase 1: Mechanical scoring
    mechanical_scores = []
    for result in results:
        score = _score_mechanical(result)
        # Attach category from scenario
        scenario = scenario_map.get(result.scenario_title)
        if scenario:
            score.category = scenario.category
        mechanical_scores.append((result, score))

    # Phase 2: LLM-assisted scoring for low-confidence results
    final_scores = []
    for result, mech_score in mechanical_scores:
        scenario = scenario_map.get(result.scenario_title)

        if (
            llm_client
            and mech_score.confidence < llm_confidence_threshold
            and result.executed
            and scenario
        ):
            logger.info(
                "LLM-evaluating ambiguous scenario '%s' (mechanical confidence=%.2f)",
                result.scenario_title,
                mech_score.confidence,
            )
            final_score = await _score_with_llm(
                scenario, result, mech_score, llm_client
            )
        else:
            final_score = mech_score

        final_scores.append(final_score)

    report.scores = final_scores

    # Aggregate computation
    _compute_aggregates(report)

    logger.info(report.summary_text())
    return report


def _compute_aggregates(report: SatisfactionReport) -> None:
    """Compute aggregate metrics from per-scenario scores."""
    if not report.scores:
        report.verdict = "UNDETERMINED"
        return

    # Weighted mean: weight by confidence
    total_weight = 0.0
    weighted_sum = 0.0
    confidence_sum = 0.0
    mechanical_scores = []
    category_accum: Dict[str, List[float]] = {}

    for score in report.scores:
        if score.method == "skipped":
            continue

        weight = max(score.confidence, 0.1)  # Floor to avoid zero-weight
        weighted_sum += score.satisfaction * weight
        total_weight += weight
        confidence_sum += score.confidence

        if score.method == "mechanical":
            mechanical_scores.append(score.satisfaction)

        if score.category:
            category_accum.setdefault(score.category, []).append(score.satisfaction)

    scored_count = sum(1 for s in report.scores if s.method != "skipped")

    if total_weight > 0:
        report.overall_satisfaction = weighted_sum / total_weight
    if scored_count > 0:
        report.overall_confidence = confidence_sum / scored_count
    if mechanical_scores:
        report.mechanical_satisfaction = sum(mechanical_scores) / len(mechanical_scores)

    # Category breakdown
    for cat, scores in category_accum.items():
        report.category_scores[cat] = sum(scores) / len(scores) if scores else 0.0

    # Verdict
    if report.overall_satisfaction >= report.verdict_threshold:
        report.verdict = "SATISFACTORY"
    elif report.overall_satisfaction >= report.verdict_threshold * 0.5:
        report.verdict = "PARTIAL"
    else:
        report.verdict = "UNSATISFACTORY"
