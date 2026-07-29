"""
Ruffy -- Post-Worker lint step (ruff check, ruff format, mypy).

Runs ruff and mypy on the generated output directory, writes a report
to demos/lint-report.txt, and returns the report content for the Judge.
No LLM calls; pure subprocess execution.
"""

import logging
import os
import subprocess

logger = logging.getLogger("dark_factory")


def _has_python_files(output_dir: str) -> bool:
    """Check if output dir contains any Python files."""
    for _root, _, files in os.walk(output_dir):
        for f in files:
            if f.endswith(".py"):
                return True
    return False


def _run_cmd(cmd: list, cwd: str, timeout: int = 60) -> tuple[int, str, str]:
    """Run a command, return (returncode, stdout, stderr)."""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=False,
        )
        return (
            result.returncode,
            result.stdout or "",
            result.stderr or "",
        )
    except subprocess.TimeoutExpired:
        return (-1, "", f"Command timed out after {timeout}s")
    except FileNotFoundError:
        return (-1, "", f"Command not found: {cmd[0]}")
    except Exception as e:
        return (-1, "", str(e))


def run_ruffy(output_dir: str) -> tuple[str, str]:
    """Run ruff check, ruff format --check, and mypy on output_dir.

    Writes demos/lint-report.txt and returns (report_text, report_path).
    If no Python files exist, returns a short note and the path.

    Returns:
        (report_text, report_path) -- report_path may be empty if write failed.
    """
    demos_dir = os.path.join(output_dir, "demos")
    os.makedirs(demos_dir, exist_ok=True)
    report_path = os.path.join(demos_dir, "lint-report.txt")

    lines = ["# Ruffy Lint Report", ""]

    if not _has_python_files(output_dir):
        lines.append("No Python files in output. Running Node.js syntax check instead.")
        lines.append("")
        lines.append("## node --check")
        lines.append("")
        # Check all .js files for syntax errors using node --check
        js_errors = []
        for root, _, files in os.walk(output_dir):
            for fname in files:
                if fname.endswith(".js") and not fname.endswith(".min.js"):
                    fpath = os.path.join(root, fname)
                    code, out, err = _run_cmd(["node", "--check", fpath], cwd=output_dir)
                    if code != 0:
                        rel = os.path.relpath(fpath, output_dir)
                        js_errors.append(f"{rel}: {(err or out).strip()[:200]}")
        if js_errors:
            lines.extend(js_errors[:20])  # cap at 20 errors
        else:
            lines.append("OK (no syntax errors in .js files)")
        lines.append("")
        report_text = "\n".join(lines)
        try:
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(report_text)
        except OSError:
            pass
        return report_text, report_path

    # 1. Ruff check
    lines.append("## ruff check")
    lines.append("")
    code, out, err = _run_cmd(
        ["ruff", "check", ".", "--output-format=concise"],
        cwd=output_dir,
    )
    if code == 0:
        lines.append("OK (no issues)")
    else:
        lines.append(out.strip() or err.strip() or f"Exit code: {code}")
    lines.append("")

    # 2. Ruff format --check
    lines.append("## ruff format --check")
    lines.append("")
    code, out, err = _run_cmd(
        ["ruff", "format", "--check", "."],
        cwd=output_dir,
    )
    if code == 0:
        lines.append("OK (formatted)")
    else:
        lines.append(out.strip() or err.strip() or f"Exit code: {code}")
    lines.append("")

    # 3. Mypy (optional; may not be installed)
    lines.append("## mypy")
    lines.append("")
    code, out, err = _run_cmd(
        ["mypy", ".", "--no-error-summary", "--ignore-missing-imports"],
        cwd=output_dir,
        timeout=90,
    )
    if code == -1 and "not found" in (out + err).lower():
        lines.append("mypy not installed (skipped)")
    elif code == 0:
        lines.append("OK (no type errors)")
    else:
        combined = (out + "\n" + err).strip()
        lines.append(combined[:4000] if len(combined) > 4000 else combined)
    lines.append("")

    report_text = "\n".join(lines)

    try:
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_text)
        logger.info("Ruffy lint report written -> %s", report_path)
    except OSError as e:
        logger.warning("Failed to write lint report: %s", e)
        report_path = ""

    return report_text, report_path
