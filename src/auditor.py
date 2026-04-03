import asyncio
import json
import logging
import os
import sys

logger = logging.getLogger("dark_factory")


async def audit_app(url, timeout=30000):
    """Runs a Playwright-based audit against a URL. Returns a structured report."""
    report = {
        "url": url,
        "success": False,
        "errors": [],
        "console_logs": [],
        "screenshot_path": None,
    }

    try:
        from playwright.async_api import async_playwright
    except ImportError:
        report["errors"].append(
            "playwright not installed. Run: pip install playwright && playwright install"
        )
        return report

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # Capture console logs
        page.on(
            "console",
            lambda msg: report["console_logs"].append(f"[{msg.type}] {msg.text}"),
        )
        page.on(
            "pageerror",
            lambda err: report["errors"].append(f"Page Error: {err.message}"),
        )

        try:
            logger.info("Audit starting: %s", url)
            await page.goto(url, wait_until="networkidle", timeout=timeout)

            # Check for Vite Error Overlay
            vite_error = await page.query_selector(".vite-error-overlay")
            if vite_error:
                error_text = await vite_error.inner_text()
                report["errors"].append(f"Vite Error Overlay detected: {error_text}")

            # Check if page is empty
            content = await page.content()
            if len(content) < 500:
                report["errors"].append(
                    "Page content suspiciously small (possible failed render)."
                )

            # Check for common error strings in text
            body_text = await page.inner_text("body")
            if "Failed to resolve import" in body_text:
                report["errors"].append(
                    "Vite 'Failed to resolve import' found in body."
                )
            if "404" in body_text and len(body_text) < 200:
                report["errors"].append("Possible 404 page detected.")

            # Take screenshot
            os.makedirs("audit_results", exist_ok=True)
            screenshot_path = os.path.abspath(
                f"audit_results/screenshot_{int(asyncio.get_running_loop().time())}.png"
            )
            await page.screenshot(path=screenshot_path)
            report["screenshot_path"] = screenshot_path

            if not report["errors"]:
                report["success"] = True

        except Exception as e:
            report["errors"].append(f"Automation Error: {str(e)}")
        finally:
            await browser.close()

    return report


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.stderr.write("Usage: python auditor.py <url>\n")
        sys.exit(1)

    target_url = sys.argv[1]
    result = asyncio.run(audit_app(target_url))
    # JSON output to stdout is intentional -- consumed by factory.py subprocess
    sys.stdout.write(json.dumps(result, indent=2))
