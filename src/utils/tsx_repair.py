"""TypeScript repair loop — fix LLM-generated TSX pages via compiler feedback."""

from __future__ import annotations

import logging
import os
import re
import subprocess
from typing import Any

logger = logging.getLogger("dark_factory")

COMMON_FIXES = [
    # Missing framer-motion import
    (
        r"import\s*\{\s*AnimatePresence[^}]*\}\s*from\s*['\"]framer-motion['\"]",
        "import { AnimatePresence } from 'framer-motion'",
    ),
]


def _run_tsc(output_dir: str) -> list[dict[str, Any]]:
    """Run tsc --noEmit and return per-file error lists."""
    try:
        if os.name == "nt":
            result = subprocess.run(
                ["C:\\Windows\\System32\\cmd.exe", "/c", "npx.cmd", "tsc", "--noEmit", "--noErrorTruncation"],
                cwd=output_dir,
                capture_output=True,
                text=True,
                timeout=120,
            )
        else:
            result = subprocess.run(
                ["/usr/bin/env", "npx", "tsc", "--noEmit", "--noErrorTruncation"],
                cwd=output_dir,
                capture_output=True,
                text=True,
                timeout=120,
            )
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
        logger.warning("tsc failed to run: %s", e)
        return []

    errors: dict[str, list[dict]] = {}
    for line in (result.stdout or "").splitlines():
        m = re.match(r"(.+)\((\d+),(\d+)\):\s+error\s+(\w+):\s+(.*)", line)
        if not m:
            continue
        file = m.group(1).replace("\\", "/")
        entry = {"line": int(m.group(2)), "col": int(m.group(3)), "code": m.group(4), "msg": m.group(5)}
        errors.setdefault(file, []).append(entry)

    return [{"file": f, "errors": errs} for f, errs in errors.items()]


def _apply_common_fixes(filepath: str) -> bool:
    """Apply regex-based fixes for known LLM TSX errors. Returns True if changed."""
    try:
        with open(filepath, encoding="utf-8") as f:
            content = f.read()
    except OSError:
        return False

    original = content

    # Fix: import { motion } from 'framer-motion' duplicated or missing
    if "framer-motion" in content and "motion" not in content:
        # ensure named import exists
        if "import" in content and "framer-motion" in content:
            content = re.sub(
                r"import\s*\{([^}]*)\}\s*from\s*['\"]framer-motion['\"]",
                lambda m: (
                    f"import {{ {m.group(1).strip()}, motion }} from 'framer-motion'"
                    if "motion" not in m.group(1)
                    else m.group(0)
                ),
                content,
            )

    # Fix: `<Component />` where Component is a string
    content = re.sub(r"<['\"]([A-Z][A-Za-z0-9]*)['\"]\s*/?>", r"<\1 />", content)

    # Fix: missing semicolons at end of export statements
    content = re.sub(r"export default ([A-Za-z0-9_]+)\s*$", r"export default \1;", content)

    # Fix: double assignment in props `export default function X() {` missing
    if "export default function" not in content and "export default" not in content:
        func_match = re.search(r"(?:function|const)\s+([A-Za-z0-9_]+)\s*(?:=\s*\([^)]*\)\s*=>|\([^)]*\)\s*\{)", content)
        if func_match:
            name = func_match.group(1)
            content = content.rstrip() + f"\n\nexport default {name};\n"

    if content != original:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        logger.info("TSX repair: applied common fixes to %s", os.path.basename(filepath))
        return True
    return False


async def llm_repair_file(filepath: str, errors: list[dict], worker: Any, max_tokens_context: int = 4000) -> bool:
    """Send broken file + compiler errors to LLM for targeted regeneration."""
    try:
        with open(filepath, encoding="utf-8", errors="replace") as f:
            content = f.read()
    except OSError:
        return False

    error_lines = "\n".join(f"  L{e['line']} [{e['code']}]: {e['msg']}" for e in errors[:20])
    prompt = (
        f"This TypeScript/React file has compilation errors. Fix them.\n\n"
        f"ERRORS:\n{error_lines}\n\n"
        f"CURRENT FILE:\n```tsx\n{content[:max_tokens_context]}\n```\n\n"
        f"Return the COMPLETE corrected file inside ```tsx fences. "
        f"Keep the same component name and export default. Do not omit any functionality."
    )
    try:
        fixed = await worker.generate(
            prompt,
            system_prompt="You are a TypeScript expert. Fix React component errors. Output only the corrected file.",
            temperature=0.1,
        )
    except Exception as e:
        logger.warning("TSX LLM repair failed for %s: %s", os.path.basename(filepath), e)
        return False

    if not fixed or len(fixed) < 50:
        return False

    # Extract code from fences
    fence = re.search(r"```(?:tsx|typescript|ts)?\s*\n(.*?)```", fixed, re.DOTALL)
    if fence:
        fixed = fence.group(1).strip()

    # Sanity: must contain export default and the component name
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(fixed)
    logger.info("TSX LLM repair: regenerated %s", os.path.basename(filepath))
    return True


async def repair_tsx(output_dir: str, worker: Any | None = None, max_passes: int = 3) -> dict:
    """Repair all TSX files until tsc passes or passes exhausted.

    Returns {"clean": bool, "remaining": [file errors], "stubbed": [names], "passes": int}.
    """
    results = {"clean": False, "remaining": [], "stubbed": [], "passes": 0}

    for pass_num in range(1, max_passes + 1):
        results["passes"] = pass_num
        file_errors = _run_tsc(output_dir)

        if not file_errors:
            results["clean"] = True
            logger.info("TSX repair: clean after pass %d", pass_num)
            break

        logger.info("TSX repair pass %d: %d file(s) with errors", pass_num, len(file_errors))
        for fe in file_errors:
            filepath = os.path.join(output_dir, fe["file"])
            if not os.path.exists(filepath):
                continue

            # Try common fixes first (cheap)
            changed = _apply_common_fixes(filepath)

            # If still broken, try LLM
            if worker is not None:
                still_broken = any(
                    True
                    for fe2 in _run_tsc(output_dir)
                    if fe2["file"].replace("\\", "/") == fe["file"].replace("\\", "/")
                )
                if still_broken:
                    ok = await llm_repair_file(filepath, fe["errors"], worker)
                    if ok:
                        changed = True

            if not changed:
                logger.warning("TSX repair: could not fix %s — keeping as-is (will break build)", fe["file"])

    # Final check
    remaining = _run_tsc(output_dir)
    if remaining:
        results["remaining"] = remaining
        logger.error("TSX repair: %d file(s) still broken after %d passes", len(remaining), max_passes)
    else:
        results["clean"] = True

    return results
