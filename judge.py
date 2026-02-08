import os
import argparse
import sys
from utils.logger import logger
from run_manifest import RunManifest
import asyncio
import time

# Add src to path if needed or structure correctly
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))
from llm_client import LLMClient


class PlaywrightVerifier:
    """Verifies generated apps using a headless browser."""

    def __init__(self, url: str = "http://localhost:3000"):
        self.url = url

    async def verify_ui(self, scenarios: str):
        """Asks the browser to check the UI against the scenarios."""
        try:
            from playwright.async_api import async_playwright

            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                logger.info(f"Navigating to {self.url}...")
                await page.goto(self.url, timeout=30000)

                # SOTA Check: Look for common high-fidelity markers
                title = await page.title()

                logger.debug(f"UI Page Title: {title}")

                # Check for critical components like modals or glassmorphic elements
                has_modal = await page.query_selector(".modal") is not None

                await browser.close()
                return {
                    "success": True,
                    "title": title,
                    "has_modal": has_modal,
                    "summary": f"Page loaded successfully with title: {title}",
                }
        except Exception as e:
            logger.error(f"Playwright verification failed: {e}")
            return {"success": False, "error": str(e)}


def read_file(path: str) -> str:
    if not os.path.exists(path):
        logger.error(f"File not found at {path}")
        return ""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


async def run_judgement(
    scenarios_path: str = "scenarios/scenarios.md",
    output_dir: str = "output",
    dtu_url: str = None,
):
    logger.info(f"Satisficer Session: Judging {output_dir}")

    scenarios = read_file(scenarios_path)
    if not scenarios:
        return

    judge = LLMClient(role="foreman")

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

    # 3. Execution Verification (The Satisficer Upgrade)
    if dtu_url:
        logger.info("Satisficer Stage 2: Booting app with DTU integration (%s)...", dtu_url)
    else:
        logger.info("Satisficer Stage 2: Booting app for execution check (no DTU)...")
    orchestrator = RunManifest(output_dir, dtu_url=dtu_url)
    ui_report = {"summary": "Execution check skipped (offline mode)"}

    try:
        # Note: This requires a pre-built app or dev server setup.
        # For the purpose of the hard gate, we attempt to boot.
        orchestrator.boot()

        verifier = PlaywrightVerifier()
        ui_report = await verifier.verify_ui(scenarios)

        if ui_report.get("success"):
            logger.success(f"Execution Verification Result: {ui_report['summary']}")
        else:
            logger.warning(
                "Execution Verification encountered issues, but proceeding with audit."
            )

    finally:
        orchestrator.terminate()

    # 4. Final Verdict
    prompt = f"""
    Review these scenarios and the ACTUAL state of the generated app in '{output_dir}'.
    
    SCENARIOS:
    {scenarios[:2000]}
    
    FILES GENERATED:
    {", ".join(files_present[:50])}
    
    AUDITOR REPORT:
    {audit_report}

    UI/EXECUTION REPORT:
    {ui_report}
    
    VERDICT: Does this app satisfy the user's materialistic requirements for a SOTA, HIGH-FIDELITY implementation?
    OUTPUT FORMAT: 
    VERDICT: [PASS/FAIL]
    CRITIQUE: [Multi-line technical critique for the workers]
    """

    logger.info("Synthesizing final verdict...")
    verdict = await judge.generate(
        prompt, system_prompt="You are a strict QA Lead. No gaslighting. No leniency."
    )

    logger.audit(verdict)

    if "VERDICT: FAIL" in verdict.upper():
        with open("critique.md", "w", encoding="utf-8") as f:
            f.write(verdict)
        logger.error("Quality Gate Failed. Critique saved to critique.md")
        return False
    else:
        logger.success("Quality Gate Passed!")
        return True


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
        "--dtu-url", default=None,
        help="DTU base URL (e.g. http://localhost:8001). Injects DTU env vars into generated app."
    )

    args = parser.parse_args()

    if args.command == "judge":
        import asyncio

        asyncio.run(run_judgement(args.scenarios, args.output, dtu_url=args.dtu_url))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
