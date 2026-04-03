"""
Scenario Executor -- runs parsed scenarios against a live generated app.

Execution strategies by ScenarioType:
  - API:     httpx requests against the app's HTTP endpoints
  - BROWSER: Rodney headless browser interaction (fallback: skip with note)
  - STATIC:  skipped (cannot be mechanically verified)

Each scenario execution produces a ScenarioResult with:
  - actual response data (status code, body snippet, headers)
  - assertion evaluation (did the THEN condition hold?)
  - confidence level (how sure are we about the evaluation?)
  - evidence (screenshots, response bodies, error messages)

The executor does NOT make pass/fail judgments itself. It collects raw
evidence for the SatisfactionScorer to evaluate probabilistically.
"""

import logging
import time
from dataclasses import dataclass
from typing import List, Optional

from src.verification.scenario_parser import (
    HttpAction,
    Scenario,
    ScenarioType,
)

logger = logging.getLogger("dark_factory")


@dataclass
class ScenarioResult:
    """Result of executing a single scenario."""

    scenario_title: str
    scenario_type: str
    executed: bool = False
    skipped_reason: str = ""

    # HTTP response data (for API scenarios)
    status_code: Optional[int] = None
    response_body: str = ""
    response_time_ms: float = 0.0

    # Browser data (for browser scenarios)
    page_title: str = ""
    screenshot_path: str = ""

    # Assertion evaluation (raw, pre-scoring)
    assertion_met: Optional[bool] = None  # True/False/None (ambiguous)
    assertion_evidence: str = ""  # Why we think it passed or failed
    confidence: float = 0.0  # 0.0-1.0 how sure we are

    # Errors during execution
    error: str = ""


def _generate_sample_body(
    http_action: HttpAction, scenario: Scenario
) -> Optional[dict]:
    """Generate a plausible request body based on scenario context."""
    if http_action.method in ("GET", "DELETE"):
        return None

    lower_title = scenario.title.lower()
    lower_given = scenario.given.lower()
    lower_when = scenario.when.lower()
    is_invalid = "invalid" in http_action.body_hint or "invalid" in lower_given

    if "user" in lower_title or "register" in lower_title or "signup" in lower_title:
        if is_invalid:
            return {"username": "", "password": ""}
        return {"username": "testuser", "email": "test@example.com", "password": "TestPass123"}

    if "login" in lower_title or "auth" in lower_title:
        if is_invalid:
            return {"email": "wrong@example.com", "password": "wrongpass"}
        return {"email": "test@example.com", "password": "TestPass123"}

    if "treatment" in lower_title:
        return {"title": "Test Treatment", "description": "Automated test treatment", "duration_minutes": 30}

    if "appointment" in lower_title or "booking" in lower_title:
        if "duplicate" in http_action.body_hint:
            return {"user_id": 1, "treatment_id": 1, "date": "2026-01-01", "time": "10:00"}
        return {"user_id": 1, "treatment_id": 1, "date": "2026-06-15", "time": "14:00"}

    if "task" in lower_title:
        if is_invalid:
            return {"title": ""}
        return {"title": "Test Task", "status": "active", "priority": "normal"}

    if "roast" in lower_title:
        return {"name": "Test Roast", "description": "Automated test roast", "price": 12.99}

    if "order" in lower_title:
        return {"user_id": 1, "roast_id": 1, "quantity": 2}

    if "product" in lower_title:
        return {"name": "Test Product", "price": 9.99, "stock": 10}

    if "password" in lower_title or "reset" in lower_title:
        if is_invalid:
            return {"email": "wrong@example.com"}
        return {"email": "test@example.com"}

    if "digital twin" in lower_title or "configure" in lower_title:
        return {"enabled": True, "sync_interval": 60}

    # Fallback: try to derive field name from path
    path_parts = [p for p in http_action.path.strip("/").split("/") if p and not p.startswith("{")]
    resource = path_parts[-1] if path_parts else "item"
    # Singularise naively (strip trailing s)
    if resource.endswith("s") and len(resource) > 3:
        resource = resource[:-1]
    return {"name": f"test_{resource}", "description": "automated scenario test"}


def _resolve_path(path: str) -> str:
    """Replace path parameters like {id} with test values."""
    path = path.replace("{id}", "1")
    return path


def _evaluate_api_assertion(scenario: Scenario, result: ScenarioResult) -> None:
    """Evaluate a THEN clause against the actual HTTP response.

    Sets assertion_met, assertion_evidence, and confidence on the result.
    """
    assertion = scenario.assertion
    if not assertion:
        result.assertion_met = None
        result.assertion_evidence = "No assertion parsed from THEN clause"
        result.confidence = 0.0
        return

    evidence_parts = []
    score = 0.0
    checks = 0
    passed = 0

    # Check 1: Status code match
    if assertion.expected_status and result.status_code:
        checks += 1
        if result.status_code == assertion.expected_status:
            passed += 1
            evidence_parts.append(
                f"Status code matched: expected {assertion.expected_status}, "
                f"got {result.status_code}"
            )
        else:
            # Allow range matches (2xx for 200-299, etc.)
            expected_class = assertion.expected_status // 100
            actual_class = result.status_code // 100
            if expected_class == actual_class:
                passed += 0.7
                evidence_parts.append(
                    f"Status code class matched: expected {assertion.expected_status}, "
                    f"got {result.status_code} (same {expected_class}xx class)"
                )
            else:
                evidence_parts.append(
                    f"Status code mismatch: expected {assertion.expected_status}, "
                    f"got {result.status_code}"
                )

    # Check 2: Response structure matches expectation
    if assertion.expects_list:
        checks += 1
        body_lower = result.response_body.lower()
        if result.response_body.strip().startswith("["):
            passed += 1
            evidence_parts.append("Response is a JSON array (list expected)")
        elif (
            '"results"' in body_lower
            or '"data"' in body_lower
            or '"items"' in body_lower
        ):
            passed += 0.8
            evidence_parts.append("Response contains list-like wrapper field")
        else:
            evidence_parts.append("Expected list response but got different structure")

    if assertion.expects_creation:
        checks += 1
        if result.status_code and 200 <= result.status_code <= 201:
            passed += 1
            evidence_parts.append("Creation response received (2xx)")
        elif result.status_code and result.status_code == 422:
            passed += 0.3
            evidence_parts.append(
                "422 Unprocessable Entity -- app validates input "
                "(creation endpoint exists but test payload may not match schema)"
            )
        else:
            evidence_parts.append(
                f"Creation may have failed: status={result.status_code}"
            )

    if assertion.expects_error:
        checks += 1
        if result.status_code and result.status_code >= 400:
            passed += 1
            evidence_parts.append(f"Error response received: {result.status_code}")
        else:
            evidence_parts.append(f"Expected error but got status={result.status_code}")

    # Compute overall confidence
    if checks > 0:
        score = passed / checks
        result.assertion_met = score >= 0.5
        result.confidence = min(1.0, score)
    else:
        # No specific checks possible -- ambiguous
        result.assertion_met = None
        result.confidence = 0.3
        evidence_parts.append(
            "THEN clause is too ambiguous for mechanical verification -- "
            "needs LLM-assisted evaluation"
        )

    result.assertion_evidence = "; ".join(evidence_parts)


async def execute_api_scenario(
    scenario: Scenario,
    base_url: str,
    timeout: float = 10.0,
) -> ScenarioResult:
    """Execute an API-type scenario via HTTP request.

    Args:
        scenario: Parsed scenario with http_action set
        base_url: Base URL of the running app (e.g. http://localhost:3000)
        timeout: Request timeout in seconds

    Returns:
        ScenarioResult with response data and assertion evaluation
    """
    result = ScenarioResult(
        scenario_title=scenario.title,
        scenario_type=ScenarioType.API.value,
    )

    if not scenario.http_action:
        result.skipped_reason = "No HTTP action parsed from WHEN clause"
        return result

    action = scenario.http_action
    path = _resolve_path(action.path)
    url = f"{base_url.rstrip('/')}{path}"
    body = _generate_sample_body(action, scenario)

    try:
        import httpx

        async with httpx.AsyncClient(timeout=timeout) as client:
            start = time.monotonic()

            kwargs = {"headers": {"Content-Type": "application/json"}}
            if body and action.method in ("POST", "PUT", "PATCH"):
                kwargs["json"] = body

            response = await client.request(action.method, url, **kwargs)

            elapsed = (time.monotonic() - start) * 1000

            result.executed = True
            result.status_code = response.status_code
            result.response_time_ms = round(elapsed, 1)

            # Capture truncated body
            try:
                result.response_body = response.text[:2000]
            except Exception:
                result.response_body = "(binary or unreadable)"

            logger.info(
                "Scenario '%s': %s %s -> %d (%.1fms)",
                scenario.title,
                action.method,
                url,
                response.status_code,
                elapsed,
            )

    except ImportError:
        result.error = "httpx not installed -- cannot execute API scenarios"
        logger.warning(result.error)
        return result
    except Exception as exc:
        result.executed = True
        result.error = str(exc)
        logger.warning(
            "Scenario '%s' execution error: %s %s -> %s",
            scenario.title,
            action.method,
            url,
            exc,
        )

    # Evaluate assertion
    _evaluate_api_assertion(scenario, result)
    return result


def execute_browser_scenario(
    scenario: Scenario,
    base_url: str,
    screenshot_dir: str,
) -> ScenarioResult:
    """Execute a browser-type scenario via Rodney.

    Currently only performs a basic page load + screenshot.
    Deeper browser interactions (form fill, click) would require
    mapping WHEN clauses to Rodney commands -- future enhancement.
    """
    from src.verification import rodney_runner

    result = ScenarioResult(
        scenario_title=scenario.title,
        scenario_type=ScenarioType.BROWSER.value,
    )

    if not rodney_runner.is_available():
        result.skipped_reason = "Rodney not available for browser scenario"
        return result

    try:
        import os

        os.makedirs(screenshot_dir, exist_ok=True)

        safe_title = scenario.title.replace(" ", "_").replace("/", "_")[:50]
        shot_path = os.path.join(screenshot_dir, f"scenario_{safe_title}.png")

        if not rodney_runner.start():
            result.error = "Rodney failed to start"
            return result

        if not rodney_runner.open_url(base_url):
            result.error = f"Failed to open {base_url}"
            rodney_runner.stop()
            return result

        rodney_runner.wait_stable()
        result.page_title = rodney_runner.title() or ""

        if rodney_runner.screenshot(shot_path):
            result.screenshot_path = shot_path

        # Basic check: page loaded
        body_exists = rodney_runner.exists("body")
        result.executed = True
        result.assertion_met = body_exists
        result.confidence = 0.4  # Low confidence -- just a page load check
        result.assertion_evidence = (
            f"Page loaded (title='{result.page_title}'), "
            f"body exists={body_exists}. "
            "Deeper browser verification not yet implemented."
        )

        rodney_runner.stop()

    except Exception as exc:
        result.error = str(exc)
        logger.warning("Browser scenario '%s' error: %s", scenario.title, exc)
        try:
            rodney_runner.stop()
        except Exception:
            pass

    return result


async def execute_all_scenarios(
    scenarios: List[Scenario],
    base_url: str,
    screenshot_dir: str = "",
    timeout: float = 10.0,
) -> List[ScenarioResult]:
    """Execute all parsed scenarios against the running app.

    Args:
        scenarios: List of parsed Scenario objects
        base_url: Base URL of the running app
        screenshot_dir: Directory for browser screenshots
        timeout: HTTP request timeout

    Returns:
        List of ScenarioResult objects (one per scenario)
    """
    results = []

    for scenario in scenarios:
        if scenario.scenario_type == ScenarioType.API:
            result = await execute_api_scenario(scenario, base_url, timeout)
        elif scenario.scenario_type == ScenarioType.BROWSER:
            result = execute_browser_scenario(scenario, base_url, screenshot_dir)
        elif scenario.scenario_type == ScenarioType.STATIC:
            result = ScenarioResult(
                scenario_title=scenario.title,
                scenario_type=ScenarioType.STATIC.value,
                skipped_reason=(
                    "Static/architectural scenario -- "
                    "requires code inspection, not runtime execution"
                ),
                confidence=0.0,
            )
        else:
            result = ScenarioResult(
                scenario_title=scenario.title,
                scenario_type="unknown",
                skipped_reason=f"Unknown scenario type: {scenario.scenario_type}",
            )
        results.append(result)

    executed = sum(1 for r in results if r.executed)
    skipped = sum(1 for r in results if r.skipped_reason)
    errored = sum(1 for r in results if r.error)

    logger.info(
        "Scenario execution complete: %d total, %d executed, %d skipped, %d errored",
        len(results),
        executed,
        skipped,
        errored,
    )

    return results
