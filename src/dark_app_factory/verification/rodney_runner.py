"""
Rodney Runner -- drives the `rodney` CLI for headless Chrome browser automation.

Rodney launches a persistent headless Chrome instance and provides CLI commands
for navigation, interaction, screenshots, and accessibility testing. Each CLI
invocation is a short-lived process; Chrome runs independently between commands.

Reference: https://github.com/simonw/rodney
Install:   uvx rodney   (or: uv tool install rodney)

CLI Surface Used:
  rodney start            -- launch headless Chrome
  rodney open <url>       -- navigate to URL
  rodney waitstable       -- wait for DOM stability
  rodney waitidle         -- wait for network idle
  rodney screenshot <f>   -- take a full-page screenshot
  rodney screenshot-el <selector> <f>  -- screenshot a specific element
  rodney title            -- get page title
  rodney js <expr>        -- evaluate JavaScript expression
  rodney exists <sel>     -- check element exists (exit code 0/1)
  rodney count <sel>      -- count matching elements
  rodney text <sel>       -- get text content of element
  rodney click <sel>      -- click an element
  rodney stop             -- shut down Chrome
"""

import logging
import os
import shutil
import subprocess
import time

logger = logging.getLogger("dark_factory")

_RODNEY_CMD: list | None = None


def _get_rodney_cmd() -> list:
    """Resolve the rodney command. Cached after first call."""
    global _RODNEY_CMD
    if _RODNEY_CMD is not None:
        return list(_RODNEY_CMD)

    if shutil.which("rodney"):
        _RODNEY_CMD = ["rodney"]
        return list(_RODNEY_CMD)

    if shutil.which("uvx"):
        _RODNEY_CMD = ["uvx", "rodney"]
        return list(_RODNEY_CMD)

    logger.warning("rodney not found. Install with: uv tool install rodney")
    _RODNEY_CMD = []
    return []


def is_available() -> bool:
    """Check if rodney CLI is reachable."""
    cmd = _get_rodney_cmd()
    if not cmd:
        return False
    try:
        result = subprocess.run(
            [*cmd, "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.returncode == 0
    except Exception:
        return False


def _run(args: list, timeout: int = 30) -> subprocess.CompletedProcess:
    """Execute a rodney subcommand."""
    cmd = _get_rodney_cmd()
    if not cmd:
        raise RuntimeError("rodney CLI is not installed")

    full_cmd = cmd + args
    logger.debug("rodney: %s", " ".join(full_cmd))

    return subprocess.run(
        full_cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


# =====================================================================
# Lifecycle
# =====================================================================


def start() -> bool:
    """Launch headless Chrome. Returns True if started successfully."""
    result = _run(["start"], timeout=30)
    if result.returncode != 0:
        logger.error("rodney start failed: %s", result.stderr)
        return False
    logger.info("Rodney: Chrome started.")
    return True


def stop() -> bool:
    """Shut down Chrome instance."""
    result = _run(["stop"], timeout=15)
    if result.returncode != 0:
        logger.warning("rodney stop failed: %s", result.stderr)
        return False
    logger.info("Rodney: Chrome stopped.")
    return True


def status() -> str | None:
    """Get browser status info."""
    result = _run(["status"], timeout=10)
    if result.returncode != 0:
        return None
    return result.stdout.strip()


# =====================================================================
# Navigation
# =====================================================================


def open_url(url: str) -> bool:
    """Navigate to a URL."""
    result = _run(["open", url], timeout=30)
    if result.returncode != 0:
        logger.error("rodney open failed for %s: %s", url, result.stderr)
        return False
    return True


def wait_stable() -> bool:
    """Wait for DOM to stop changing."""
    result = _run(["waitstable"], timeout=30)
    return result.returncode == 0


def wait_idle() -> bool:
    """Wait for network to be idle."""
    result = _run(["waitidle"], timeout=30)
    return result.returncode == 0


def wait_load() -> bool:
    """Wait for page load event."""
    result = _run(["waitload"], timeout=30)
    return result.returncode == 0


# =====================================================================
# Information extraction
# =====================================================================


def title() -> str | None:
    """Get the page title."""
    result = _run(["title"], timeout=10)
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def js(expression: str) -> str | None:
    """Evaluate a JavaScript expression and return the result."""
    result = _run(["js", expression], timeout=15)
    if result.returncode != 0:
        logger.warning("rodney js failed: %s", result.stderr)
        return None
    return result.stdout.strip()


def text(selector: str) -> str | None:
    """Get text content of an element."""
    result = _run(["text", selector], timeout=10)
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def exists(selector: str) -> bool:
    """Check if an element exists on the page."""
    result = _run(["exists", selector], timeout=10)
    return result.returncode == 0


def count(selector: str) -> int:
    """Count matching elements on the page."""
    result = _run(["count", selector], timeout=10)
    if result.returncode != 0:
        return 0
    try:
        return int(result.stdout.strip())
    except ValueError:
        return 0


# =====================================================================
# Interaction
# =====================================================================


def click(selector: str) -> bool:
    """Click an element."""
    result = _run(["click", selector], timeout=15)
    return result.returncode == 0


def input_text(selector: str, value: str) -> bool:
    """Type text into an input field."""
    result = _run(["input", selector, value], timeout=15)
    return result.returncode == 0


# =====================================================================
# Screenshots
# =====================================================================


def screenshot(filepath: str) -> bool:
    """Take a full-page screenshot."""
    result = _run(["screenshot", filepath], timeout=15)
    if result.returncode != 0:
        logger.error("rodney screenshot failed: %s", result.stderr)
        return False
    logger.info("Rodney: Screenshot saved to %s", filepath)
    return True


def screenshot_element(selector: str, filepath: str) -> bool:
    """Screenshot a specific element."""
    result = _run(["screenshot-el", selector, filepath], timeout=15)
    if result.returncode != 0:
        logger.error("rodney screenshot-el failed: %s", result.stderr)
        return False
    return True


# =====================================================================
# High-level verification workflow
# =====================================================================


def verify_webapp(
    url: str,
    screenshot_dir: str,
    checks: list[dict] | None = None,
) -> dict:
    """Run a full browser-based verification of a generated webapp.

    This is the high-level function used by the factory judge pipeline.

    Args:
        url: The URL to verify (e.g. http://localhost:19300).
        screenshot_dir: Directory to save screenshots.
        checks: Optional list of check dicts, each with:
            - selector: CSS selector to check
            - action: "exists" | "click" | "screenshot" | "count"
            - expected: expected value (for count)
            - name: human label for the check

    Returns:
        Dict with keys: success, title, screenshots, checks_passed, checks_failed, errors
    """
    if not is_available():
        logger.info("Rodney not installed -- skipping browser verification.")
        return {
            "success": False,
            "skipped": True,
            "reason": "rodney not installed",
        }

    os.makedirs(screenshot_dir, exist_ok=True)
    report = {
        "success": False,
        "title": None,
        "screenshots": [],
        "checks_passed": 0,
        "checks_failed": 0,
        "errors": [],
    }

    if not start():
        report["errors"].append("Failed to start Chrome via rodney")
        return report

    try:
        # Navigate and wait
        if not open_url(url):
            report["errors"].append(f"Failed to open {url}")
            return report

        # Give the page a moment, then wait for stability
        time.sleep(2)
        wait_stable()
        wait_idle()

        # Capture title
        page_title = title()
        report["title"] = page_title
        logger.info("Rodney: Page title = '%s'", page_title)

        # Full-page screenshot
        main_shot = os.path.join(screenshot_dir, "homepage.png")
        if screenshot(main_shot):
            report["screenshots"].append(main_shot)

        # Run optional checks
        if checks:
            for check in checks:
                check_name = check.get("name", check.get("selector", "unknown"))
                action = check.get("action", "exists")
                selector = check.get("selector", "")

                try:
                    if action == "exists":
                        if exists(selector):
                            report["checks_passed"] += 1
                            logger.info("CHECK PASS: %s exists", check_name)
                        else:
                            report["checks_failed"] += 1
                            logger.warning("CHECK FAIL: %s not found", check_name)

                    elif action == "count":
                        actual = count(selector)
                        expected = check.get("expected", 1)
                        if actual >= expected:
                            report["checks_passed"] += 1
                        else:
                            report["checks_failed"] += 1
                            logger.warning(
                                "CHECK FAIL: %s count=%d expected>=%d",
                                check_name,
                                actual,
                                expected,
                            )

                    elif action == "click":
                        if click(selector):
                            time.sleep(1)
                            wait_stable()
                            shot_name = check_name.replace(" ", "_") + ".png"
                            shot_path = os.path.join(screenshot_dir, shot_name)
                            screenshot(shot_path)
                            report["screenshots"].append(shot_path)
                            report["checks_passed"] += 1
                        else:
                            report["checks_failed"] += 1

                    elif action == "screenshot":
                        shot_name = check_name.replace(" ", "_") + ".png"
                        shot_path = os.path.join(screenshot_dir, shot_name)
                        if screenshot_element(selector, shot_path):
                            report["screenshots"].append(shot_path)
                            report["checks_passed"] += 1
                        else:
                            report["checks_failed"] += 1

                except Exception as e:
                    report["errors"].append(f"Check '{check_name}' error: {e}")
                    report["checks_failed"] += 1

        report["success"] = report["checks_failed"] == 0 and len(report["errors"]) == 0

    except Exception as e:
        report["errors"].append(str(e))
    finally:
        stop()

    return report
