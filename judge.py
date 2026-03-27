import argparse
import os
import sys
import json

# Normalize import paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
if os.path.join(BASE_DIR, "src") not in sys.path:
    sys.path.insert(1, os.path.join(BASE_DIR, "src"))

from src.utils.logger import logger
from run_manifest import RunManifest
from src.llm_client import LLMClient
from src.verification import rodney_runner, showboat_runner
from src.verification.scenario_parser import parse_scenarios, ScenarioType
from src.verification.scenario_executor import execute_all_scenarios
from src.verification.satisfaction_scorer import compute_satisfaction


class PlaywrightVerifier:
    """Verifies generated apps using a headless browser (legacy fallback)."""

    def __init__(self, url: str = "http://localhost:3000"):
        self.url = url

    async def verify_ui(self, scenarios: str):
        """Asks the browser to check the UI against the scenarios."""
        try:
            from playwright.async_api import async_playwright

            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                logger.info("Navigating to %s...", self.url)
                await page.goto(self.url, timeout=30000)

                page_title = await page.title()
                logger.debug("UI Page Title: %s", page_title)
                has_modal = await page.query_selector(".modal") is not None

                await browser.close()
                return {
                    "success": True,
                    "title": page_title,
                    "has_modal": has_modal,
                    "summary": f"Page loaded successfully with title: {page_title}",
                    "tool": "playwright",
                }
        except Exception as e:
            logger.error("Playwright verification failed: %s", e)
            return {"success": False, "error": str(e), "tool": "playwright"}


def read_file(path: str) -> str:
    """Reads a file and returns its content."""
    if not os.path.exists(path):
        logger.error(f"File not found at {path}")
        return ""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


async def query_dtu_logs(dtu_url: str):
    """Queries the DTU log for service interaction verification."""
    if not dtu_url:
        return []

    try:
        # SOTA: Use httpx for async requests if possible,
        # but using urllib here to avoid extra dependencies for the base gate.
        import urllib.request

        log_url = f"{dtu_url.rstrip('/')}/dtu/log"
        logger.info(f"Querying DTU logs at {log_url}...")

        with urllib.request.urlopen(log_url, timeout=5) as response:
            if response.status == 200:
                return json.loads(response.read().decode())
    except Exception as e:
        logger.warning(f"Failed to query DTU logs: {e}")
    return []


async def run_judgement(
    scenarios_path: str = "scenarios/scenarios.md",
    output_dir: str = "output",
    dtu_url: str = None,
    llm_client=None,
    lint_report: str = "",
):
    logger.info(f"Satisficer Session: Judging {output_dir}")

    scenarios = read_file(scenarios_path)
    if not scenarios:
        return

    judge = llm_client if llm_client else LLMClient(role="foreman")

    # 1. Physical Verification (Real testing vs Hallucination)
    logger.info("Performing physical file check...")
    files_present = []
    for root, dirs, files in os.walk(output_dir):
        for file in files:
            files_present.append(os.path.relpath(os.path.join(root, file), output_dir))

    # 2. Logic Verification (Specialist Auditor)
    from src.specialists.council import Auditor

    auditor = Auditor()

    logger.info("Running automated audit (Static & Contextual)...")
    audit_report = await auditor.generate(
        "full_audit", scenarios, {"files": files_present}, judge
    )

    # 3. Scenario-Based Execution Verification
    #
    # Parse GIVEN/WHEN/THEN scenarios, boot the app, execute each
    # scenario as real HTTP requests or browser actions, then compute
    # a satisfaction score.
    #
    # Also performs the existing Rodney/Playwright UI check for general
    # page-load verification and screenshot artifacts.
    if dtu_url:
        logger.info(
            "Satisficer Stage 2: Booting app with DTU integration (%s)...", dtu_url
        )
    else:
        logger.info("Satisficer Stage 2: Booting app for scenario execution...")
    orchestrator = RunManifest(output_dir, dtu_url=dtu_url)
    ui_report = {"summary": "Execution check skipped (offline mode)"}
    screenshot_dir = os.path.join(output_dir, "demos", "screenshots")
    satisfaction_report = None

    try:
        orchestrator.boot()

        # Detect app URL
        app_port = _detect_app_port(orchestrator)
        app_url = f"http://localhost:{app_port}" if app_port else "http://localhost:3000"

        # 3a. Parse and execute scenarios against live app
        parsed_scenarios = parse_scenarios(scenarios)
        if parsed_scenarios:
            logger.info(
                "Executing %d parsed scenarios against %s...",
                len(parsed_scenarios), app_url,
            )
            scenario_results = await execute_all_scenarios(
                scenarios=parsed_scenarios,
                base_url=app_url,
                screenshot_dir=screenshot_dir,
                timeout=10.0,
            )

            # Compute satisfaction (with optional LLM for ambiguous assertions)
            satisfaction_report = await compute_satisfaction(
                scenarios=parsed_scenarios,
                results=scenario_results,
                llm_client=judge,
                llm_confidence_threshold=0.5,
                pass_threshold=0.6,
            )
            logger.info(
                "Satisfaction verdict: %s (%.1f%%)",
                satisfaction_report.verdict,
                satisfaction_report.overall_satisfaction * 100,
            )
        else:
            logger.warning("No parseable scenarios found -- skipping scenario execution.")

        # 3b. General UI Verification (Rodney -> Playwright fallback)
        if rodney_runner.is_available():
            logger.info("Using Rodney for general UI verification...")
            rodney_checks = [
                {"selector": "body", "action": "exists", "name": "body_exists"},
                {"selector": "h1", "action": "exists", "name": "h1_heading"},
            ]
            ui_report = rodney_runner.verify_webapp(
                url=app_url,
                screenshot_dir=screenshot_dir,
                checks=rodney_checks,
            )
            ui_report["tool"] = "rodney"

            if ui_report.get("success"):
                logger.info(
                    "Rodney UI check PASSED: title='%s', screenshots=%d",
                    ui_report.get("title", "?"),
                    len(ui_report.get("screenshots", [])),
                )
            elif ui_report.get("skipped"):
                logger.info("Rodney skipped: %s", ui_report.get("reason"))
            else:
                logger.warning(
                    "Rodney UI check had issues: %s",
                    ui_report.get("errors", []),
                )
        else:
            logger.info("Rodney not available, falling back to Playwright...")
            verifier = PlaywrightVerifier()
            ui_report = await verifier.verify_ui(scenarios)

        if ui_report.get("success"):
            logger.info("UI Verification Result: %s", ui_report.get("summary", "PASS"))
        else:
            logger.warning(
                "UI Verification encountered issues, but proceeding with audit."
            )

    except Exception as e:
        logger.error("Execution verification error: %s", e)
        ui_report["error"] = str(e)
    finally:
        orchestrator.terminate()

    # 3.5 DTU Log Verification
    dtu_logs = []
    if dtu_url:
        dtu_logs = await query_dtu_logs(dtu_url)
        if dtu_logs:
            logger.info(
                f"DTU Interaction Verified: Observed {len(dtu_logs)} service calls."
            )
        else:
            logger.warning(
                "DTU integrated but no service logs observed (possible failed interaction)."
            )

    # 4. Final Verdict
    screenshots_info = ""
    if ui_report.get("screenshots"):
        screenshots_info = f"\nScreenshots captured ({ui_report['tool']}): {', '.join(ui_report['screenshots'])}"

    # Build satisfaction summary for the prompt
    satisfaction_summary = "Scenario testing not performed."
    if satisfaction_report:
        satisfaction_summary = json.dumps(
            satisfaction_report.to_dict(), indent=2
        )

    prompt = f"""
    Review these scenarios and the ACTUAL state of the generated app in '{output_dir}'.
    
    SCENARIOS:
    {scenarios[:2000]}
    
    FILES GENERATED:
    {", ".join(files_present[:50])}
    
    AUDITOR REPORT:
    {audit_report}

    SCENARIO EXECUTION RESULTS (satisfaction-based testing):
    {satisfaction_summary}

    RUFFY LINT REPORT (ruff check, ruff format, mypy):
    {lint_report if lint_report else "Not available."}

    UI/EXECUTION REPORT:
    Tool: {ui_report.get('tool', 'none')}
    Title: {ui_report.get('title', 'N/A')}
    Success: {ui_report.get('success', False)}
    Checks Passed: {ui_report.get('checks_passed', 'N/A')}
    Checks Failed: {ui_report.get('checks_failed', 'N/A')}
    Errors: {ui_report.get('errors', [])}
    {screenshots_info}

    DTU INTERACTION LOGS:
    {json.dumps(dtu_logs[:20], indent=2) if dtu_logs else "No DTU logs observed."}
    
    IMPORTANT: The scenario execution results above show ACTUAL HTTP responses
    from the running application. These are objective, mechanical test results.
    Weight them heavily in your verdict.

    VERDICT: Does this app satisfy the user's materialistic requirements for a SOTA, HIGH-FIDELITY implementation?
    OUTPUT FORMAT: 
    VERDICT: [PASS/FAIL]
    SATISFACTION: [percentage from scenario testing, or N/A]
    CRITIQUE: [Multi-line technical critique for the workers]
    """

    logger.info("Synthesizing final verdict...")
    verdict = await judge.generate(
        prompt, system_prompt="You are a strict QA Lead. No gaslighting. No leniency."
    )

    logger.info("AUDIT VERDICT:\n%s", verdict)

    # 5. Showboat Audit Artifact -- persistent proof of the judge run
    _create_showboat_audit(output_dir, verdict, ui_report, files_present, dtu_logs)

    if "VERDICT: FAIL" in verdict.upper():
        with open("critique.md", "w", encoding="utf-8") as f:
            f.write(verdict)
        logger.error("Quality Gate Failed. Critique saved to critique.md")
        return False
    else:
        logger.info("Quality Gate Passed!")
        return True


def _detect_app_port(orchestrator: RunManifest) -> int:
    """Try to detect which port the generated app is listening on.

    Inspects RunManifest processes for port info. Falls back to 3000.
    """
    # Simple heuristic: check env vars set during boot
    import socket

    for candidate in [3000, 8000, 5173, 5174, 19300]:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                if s.connect_ex(("localhost", candidate)) == 0:
                    return candidate
        except Exception:
            continue
    return 3000


def _create_showboat_audit(
    output_dir: str,
    verdict: str,
    ui_report: dict,
    files_present: list,
    dtu_logs: list,
):
    """Create a Showboat audit artifact that records the judge run.

    This produces a demos/audit-report.md in the output directory with
    real command output embedded, not agent-reported output.
    """
    if not showboat_runner.is_available():
        logger.info("Showboat not installed -- skipping audit artifact.")
        return

    demos_dir = os.path.join(output_dir, "demos")
    os.makedirs(demos_dir, exist_ok=True)
    demo_path = os.path.join(demos_dir, "audit-report.md")

    try:
        showboat_runner.init(demo_path, "Quality Audit Report")

        showboat_runner.note(
            demo_path,
            f"Output directory: `{output_dir}`\n"
            f"Files generated: {len(files_present)}\n"
            f"Verification tool: {ui_report.get('tool', 'none')}\n"
            f"UI checks passed: {ui_report.get('checks_passed', 'N/A')}\n"
            f"UI checks failed: {ui_report.get('checks_failed', 'N/A')}",
        )

        # List files via real command
        if os.name == "nt":
            showboat_runner.exec_cmd(
                demo_path, "powershell",
                f"Get-ChildItem -Recurse -File '{output_dir}' | Measure-Object | Select-Object -ExpandProperty Count",
            )
        else:
            showboat_runner.exec_cmd(
                demo_path, "bash",
                f"find {output_dir} -type f | wc -l",
            )

        # Record screenshots if any
        screenshots = ui_report.get("screenshots", [])
        if screenshots:
            showboat_runner.note(demo_path, f"Screenshots captured: {len(screenshots)}")
            for shot in screenshots[:5]:
                if os.path.exists(shot):
                    showboat_runner.note(demo_path, f"![screenshot]({shot})")

        # Record DTU interaction count
        if dtu_logs:
            showboat_runner.note(
                demo_path,
                f"DTU service interactions observed: {len(dtu_logs)}",
            )

        # Record verdict (truncated)
        showboat_runner.note(demo_path, f"## Verdict\n\n{verdict[:2000]}")

        logger.info("Showboat audit artifact created: %s", demo_path)

    except Exception as e:
        logger.warning("Failed to create Showboat audit artifact: %s", e)


def main():
    parser = argparse.ArgumentParser(description="Dark App Factory Judge")
    subparsers = parser.add_subparsers(dest="command")

    judge_parser = subparsers.add_parser("judge", help="Run judgement on app")
    judge_parser.add_argument(
        "--scenarios", default="scenarios/scenarios.md", help="Path to scenarios file"
    )
    judge_parser.add_argument(
        "--output", default="output", help="Target output directory to judge"
    )
    judge_parser.add_argument(
        "--dtu-url",
        default=None,
        help="DTU base URL (e.g. http://localhost:8001). Injects DTU env vars into generated app.",
    )

    args = parser.parse_args()

    if args.command == "judge":
        import asyncio

        asyncio.run(run_judgement(args.scenarios, args.output, dtu_url=args.dtu_url))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
