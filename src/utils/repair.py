"""Repair loop — detect syntax errors, feed back to specialists, regenerate."""

from __future__ import annotations

import ast
import logging
import os
import subprocess
import sys
from typing import Any

logger = logging.getLogger("dark_factory")

STDLIB_MODULES = {
    "os", "sys", "json", "re", "math", "time", "datetime", "uuid", "hashlib",
    "typing", "pathlib", "abc", "enum", "dataclasses", "collections", "itertools",
    "functools", "random", "decimal", "io", "base64", "html", "urllib", "xml",
    "csv", "string", "struct", "textwrap", "pprint", "copy", "inspect", "types",
    "logging", "warnings", "traceback", "threading", "asyncio", "concurrent",
    "multiprocessing", "socket", "ssl", "email", "smtplib", "http", "ftplib",
}

THIRD_PARTY_PREFIXES = {
    "fastapi", "pydantic", "sqlalchemy", "uvicorn", "alembic", "httpx", "requests",
    "stripe", "boto3", "PIL", "numpy", "pandas", "jose", "passlib", "dotenv",
    "cryptography", "markdown", "feedgen", "sendgrid", "qrcode", "weasyprint",
    "pytest", "ruff", "mypy", "pre_commit", "langchain", "chromadb", "sentence_transformers",
    "slowapi", "python_multipart", "python_dateutil", "pyjwt", "bcrypt",
}


def _is_shadowing_stdlib(filepath: str) -> bool:
    """Check if a generated .py file shadows a stdlib module."""
    name = os.path.splitext(os.path.basename(filepath))[0]
    return name in STDLIB_MODULES or name.startswith("_") or name in {"typing_extensions"}


def _is_third_party_import(module_name: str) -> bool:
    """Check if an import refers to a known third-party package."""
    top = module_name.split(".")[0]
    return top in STDLIB_MODULES or top in THIRD_PARTY_PREFIXES


def _remove_shadowing_files(output_dir: str) -> list[str]:
    """Delete generated files that shadow stdlib modules. Returns removed paths."""
    removed = []
    for root, _, files in os.walk(output_dir):
        for f in files:
            if f.endswith(".py") and _is_shadowing_stdlib(os.path.join(root, f)):
                path = os.path.join(root, f)
                os.remove(path)
                removed.append(path)
                logger.warning("Repair: removed shadowing file %s", path)
    return removed


def check_syntax(output_dir: str) -> list[dict[str, Any]]:
    """Run syntax checks on all generated Python files. Returns list of {file, error, lineno}."""
    errors = []

    # Phase 1: Remove shadowing stdlib files
    _remove_shadowing_files(output_dir)

    # Phase 2: Check remaining .py files
    for root, _, files in os.walk(output_dir):
        for f in files:
            if not f.endswith(".py"):
                continue
            path = os.path.join(root, f)
            rel = os.path.relpath(path, output_dir)

            # Skip files in .factory-logs, node_modules, .git
            if any(part.startswith(".") for part in rel.split(os.sep)):
                continue

            try:
                with open(path, encoding="utf-8", errors="replace") as fh:
                    source = fh.read()
                ast.parse(source)
            except SyntaxError as e:
                errors.append({
                    "file": rel,
                    "path": path,
                    "error": str(e),
                    "lineno": e.lineno or 1,
                    "msg": e.msg,
                })
            except UnicodeDecodeError:
                errors.append({"file": rel, "path": path, "error": "Binary or non-UTF8 file", "lineno": 0, "msg": "encoding error"})

    return errors


def analyze_imports(output_dir: str) -> list[str]:
    """Find generated files that import shadowed or missing modules. Returns issues."""
    issues = []
    for root, _, files in os.walk(output_dir):
        for f in files:
            if not f.endswith(".py"):
                continue
            path = os.path.join(root, f)
            rel = os.path.relpath(path, output_dir)
            if any(part.startswith(".") for part in rel.split(os.sep)):
                continue
            try:
                with open(path, encoding="utf-8") as fh:
                    source = fh.read()
                tree = ast.parse(source)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            if _is_third_party_import(alias.name):
                                continue
                            # Check if local module exists
                            mod_path = os.path.join(output_dir, alias.name.replace(".", "/") + ".py")
                            if not os.path.exists(mod_path):
                                issues.append(f"{rel}: imports '{alias.name}' which doesn't exist as local file")
                    elif isinstance(node, ast.ImportFrom) and node.module:
                        if not _is_third_party_import(node.module):
                            mod_path = os.path.join(output_dir, node.module.replace(".", "/") + ".py")
                            if not os.path.exists(mod_path):
                                issues.append(f"{rel}: imports from '{node.module}' which doesn't exist as local file")
            except SyntaxError:
                continue
    return issues


def repair_file(path: str, error_msg: str, lineno: int, worker: Any | None = None, context: str = "") -> bool:
    """Attempt to repair a single file with syntax errors.

    For simple errors (wrong import name, missing import), fix directly.
    For complex errors, delegate to LLM regeneration if worker is available.
    """
    if not os.path.exists(path):
        return False

    rel = os.path.relpath(path, os.path.join(os.path.dirname(__file__), "..", ".."))
    
    # Strategy 1: Fix common import typos directly
    fixes = {
        "load_contents": "load_dotenv",
        "CryptContext(10,": "CryptContext(schemes=['bcrypt'])",
        "OAuth2PasswordBearer(auto_error=False)": "OAuth2PasswordBearer",
    }
    
    with open(path, encoding="utf-8") as f:
        content = content_original = f.read()
    
    changed = False
    for wrong, right in fixes.items():
        if wrong in content:
            content = content.replace(wrong, right)
            changed = True
            logger.info("Repair: fixed '%s' in %s", wrong, rel)

    # Strategy 2: Fix Column(Type(default=...)) pattern
    import re
    col_fix = re.sub(r'Column\((\w+)\(default=func\.now\(\)\)\)', r'Column(\1, default=func.now())', content)
    if col_fix != content:
        content = col_fix
        changed = True
        logger.info("Repair: fixed Column(default=func.now()) pattern in %s", rel)

    if changed:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        logger.info("Repair: wrote fixes to %s", rel)
        return True

    # Strategy 3: LLM-powered repair if worker is available
    if worker is not None:
        prompt = (
            f"The following file has a syntax error at line {lineno}: {error_msg}\n\n"
            f"File: {rel}\n\n"
            f"```python\n{content_original[:3000]}\n```\n\n"
            f"Fix the error. Output ONLY the corrected code, no explanations."
        )
        try:
            import asyncio
            fixed = asyncio.run(worker.generate(prompt, system_prompt="Fix syntax errors. Output only fixed code.", temperature=0.1))
            if fixed and len(fixed) > 10:
                # Extract code from markdown fences if present
                if "```" in fixed:
                    fixed = fixed.split("```")[1]
                    if fixed.startswith("python\n"):
                        fixed = fixed[7:]
                with open(path, "w", encoding="utf-8") as f:
                    f.write(fixed.strip())
                logger.info("Repair: LLM regenerated %s", rel)
                return True
        except Exception as e:
            logger.warning("Repair: LLM fix failed for %s: %s", rel, e)

    return False
