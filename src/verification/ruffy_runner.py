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


def _check_import_closure(output_dir: str) -> list[str]:
    """Cross-check imported packages against declared dependencies.

    Parses JS/TS/Python import statements from generated files and reports
    any package that is imported but missing from package.json or requirements.txt.
    """
    import json
    import re

    errors: list[str] = []
    pkg_path = os.path.join(output_dir, "package.json")
    req_path = os.path.join(output_dir, "requirements.txt")

    declared_node: set[str] = set()
    declared_py: set[str] = set()

    if os.path.exists(pkg_path):
        try:
            pkg = json.loads(open(pkg_path, encoding="utf-8").read())
            declared_node = set(pkg.get("dependencies", {})) | set(pkg.get("devDependencies", {}))
        except (json.JSONDecodeError, OSError):
            pass

    if os.path.exists(req_path):
        try:
            for line in open(req_path, encoding="utf-8").read().splitlines():
                stripped = line.strip()
                if stripped and not stripped.startswith("#"):
                    pkg_name = re.split(r"[=<>!~]", stripped)[0].strip()
                    declared_py.add(pkg_name.lower())
        except OSError:
            pass

    has_node = bool(declared_node)
    has_py = bool(declared_py)

    # Collect all imports from generated files
    for root, _, files in os.walk(output_dir):
        # Skip node_modules and .factory-logs
        if "node_modules" in root.split(os.sep) or ".factory-logs" in root.split(os.sep):
            continue
        for fname in files:
            fpath = os.path.join(root, fname)
            try:
                content = open(fpath, encoding="utf-8", errors="replace").read()
            except OSError:
                continue
            rel = os.path.relpath(fpath, output_dir)

            if fname.endswith((".ts", ".tsx", ".js", ".jsx")):
                # Named imports: import { X } from "package"
                for m in re.finditer(r"from\s+['\"]([^'\"\.][^'\"]*)['\"]", content):
                    spec = m.group(1)
                    top = spec.split("/")[0]
                    if top.startswith("@") and "/" in spec:
                        top = f"@{spec.split('/')[1]}"
                    if top not in declared_node and has_node:
                        errors.append(f"{rel}: imports '{top}' but not in package.json")
                # require("package")
                for m in re.finditer(r"require\s*\(\s*['\"]([^'\"\.][^'\"]*)['\"]\s*\)", content):
                    spec = m.group(1)
                    top = spec.split("/")[0]
                    if top.startswith("@") and "/" in spec:
                        top = f"@{spec.split('/')[1]}"
                    if top not in declared_node and has_node:
                        errors.append(f"{rel}: require('{top}') but not in package.json")

            elif fname.endswith(".py"):
                py_stdlib = {"os", "sys", "typing", "__future__", "abc", "enum", "re"}
                for m in re.finditer(r"^(?:import|from)\s+(\w+)", content, re.MULTILINE):
                    top = m.group(1)
                    if top in py_stdlib:
                        continue
                    if top.lower() not in declared_py and has_py:
                        errors.append(f"{rel}: imports '{top}' but not in requirements.txt")

    return errors


def _run_js_ts_gates(output_dir: str) -> list[str]:
    """Run JS/TS static gates: tsc --noEmit, vite build, node --check."""
    errors: list[str] = []

    has_tsconfig = os.path.exists(os.path.join(output_dir, "tsconfig.json"))
    has_vite = os.path.exists(os.path.join(output_dir, "vite.config.ts"))
    has_tsconfig or os.path.exists(os.path.join(output_dir, "tsconfig.json"))

    # node --check on all .js files
    js_errors = []
    for root, _, files in os.walk(output_dir):
        if "node_modules" in root.split(os.sep):
            continue
        for fname in files:
            if fname.endswith(".js") and not fname.endswith(".min.js"):
                fpath = os.path.join(root, fname)
                code, out, err = _run_cmd(["node", "--check", fpath], cwd=output_dir)
                if code != 0:
                    rel = os.path.relpath(fpath, output_dir)
                    js_errors.append(f"{rel}: {(err or out).strip()[:200]}")
    if js_errors:
        errors.append(f"node --check: {len(js_errors)} file(s) with syntax errors")
        errors.extend(js_errors[:10])

    # tsc --noEmit when tsconfig.json exists
    if has_tsconfig:
        code, out, err = _run_cmd(
            ["npx", "tsc", "--noEmit", "--noErrorTruncation"],
            cwd=output_dir,
            timeout=120,
        )
        if code != 0:
            lines = (err or out).strip().splitlines()
            truncated = lines[:30]
            errors.append(f"tsc --noEmit: {len(lines)} error(s)")
            errors.extend(truncated)

    # vite build --logLevel error when vite.config.ts exists
    if has_vite:
        code, out, err = _run_cmd(
            ["npx", "vite", "build", "--logLevel", "error"],
            cwd=output_dir,
            timeout=120,
        )
        if code != 0:
            summary = (err or out).strip().splitlines()[-5:]
            errors.append("vite build failed")
            errors.extend(summary)

    return errors


def run_ruffy(output_dir: str) -> tuple[str, str]:
    """Run static analysis gates on output_dir: Python lint, JS/TS gates,
    import-to-dependency closure check.

    Writes demos/lint-report.txt and returns (report_text, report_path).
    """
    demos_dir = os.path.join(output_dir, "demos")
    os.makedirs(demos_dir, exist_ok=True)
    report_path = os.path.join(demos_dir, "lint-report.txt")

    lines = ["# Ruffy Lint Report", ""]

    if _has_python_files(output_dir):
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

    # 4. JS/TS static gates (always run when relevant files exist)
    js_errors = _run_js_ts_gates(output_dir)
    if js_errors:
        lines.append("## JS/TS gates")
        lines.append("")
        lines.extend(js_errors)
        lines.append("")

    # 5. Import-to-dependency closure check
    closure_errors = _check_import_closure(output_dir)
    if closure_errors:
        lines.append("## Import closure check")
        lines.append("")
        for err in closure_errors:
            lines.append(f"- {err}")
        lines.append("")

    # 6. Legacy: node --check on JS-only outputs (if no Python files)
    if not _has_python_files(output_dir):
        has_js_gate = any("## JS/TS gates" in line for line in lines)
        if not has_js_gate:
            js_syntax_errors = [e for e in js_errors if "node --check" in e]
            if not js_syntax_errors:
                lines.append("No Python files. JS/TS syntax OK.")

    report_text = "\n".join(lines)

    try:
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_text)
        logger.info("Ruffy lint report written -> %s", report_path)
    except OSError as e:
        logger.warning("Failed to write lint report: %s", e)
        report_path = ""

    return report_text, report_path
