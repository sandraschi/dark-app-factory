"""
Showboat Runner -- drives the `showboat` CLI to produce verifiable demo artifacts.

Showboat creates executable Markdown documents that capture real command output.
These serve as proof-of-work for the Dark App Factory build pipeline.

Reference: https://github.com/simonw/showboat
Install:   uvx showboat   (or: uv tool install showboat)

CLI Surface Used:
  showboat init <file> <title>
  showboat note <file> <text>
  showboat exec <file> <lang> <code>
  showboat image <file> <script>
  showboat verify <file>
"""

import logging
import os
import shutil
import subprocess
from typing import Optional

logger = logging.getLogger("dark_factory")

# Prefer uvx for zero-install execution; fall back to bare binary
_SHOWBOAT_CMD: Optional[list] = None


def _get_showboat_cmd() -> list:
    """Resolve the showboat command. Cached after first call."""
    global _SHOWBOAT_CMD
    if _SHOWBOAT_CMD is not None:
        return list(_SHOWBOAT_CMD)

    # 1. Check if showboat binary is on PATH
    if shutil.which("showboat"):
        _SHOWBOAT_CMD = ["showboat"]
        return list(_SHOWBOAT_CMD)

    # 2. Try uvx (PyPI wrapper around Go binary)
    if shutil.which("uvx"):
        _SHOWBOAT_CMD = ["uvx", "showboat"]
        return list(_SHOWBOAT_CMD)

    # 3. Not available
    logger.warning("showboat not found. Install with: uv tool install showboat")
    _SHOWBOAT_CMD = []
    return []


def is_available() -> bool:
    """Check if showboat CLI is reachable."""
    cmd = _get_showboat_cmd()
    if not cmd:
        return False
    try:
        result = subprocess.run(
            cmd + ["--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.returncode == 0
    except Exception:
        return False


def _run(args: list, workdir: Optional[str] = None) -> subprocess.CompletedProcess:
    """Execute a showboat subcommand. Returns CompletedProcess."""
    cmd = _get_showboat_cmd()
    if not cmd:
        raise RuntimeError("showboat CLI is not installed")

    full_cmd = cmd + args
    logger.debug("showboat: %s", " ".join(full_cmd))

    return subprocess.run(
        full_cmd,
        capture_output=True,
        text=True,
        timeout=120,
        cwd=workdir,
    )


def init(demo_path: str, title: str, workdir: Optional[str] = None) -> bool:
    """Create a new demo document.

    Args:
        demo_path: Path to the .md file to create.
        title: H1 title for the document.
        workdir: Working directory for command execution.
    """
    result = _run(["init", demo_path, title], workdir=workdir)
    if result.returncode != 0:
        logger.error("showboat init failed: %s", result.stderr)
        return False
    return True


def note(demo_path: str, text: str, workdir: Optional[str] = None) -> bool:
    """Append a commentary note to the demo document."""
    result = _run(["note", demo_path, text], workdir=workdir)
    if result.returncode != 0:
        logger.error("showboat note failed: %s", result.stderr)
        return False
    return True


def exec_cmd(
    demo_path: str,
    lang: str,
    code: str,
    workdir: Optional[str] = None,
) -> tuple:
    """Run a command, capture output into the demo document.

    Returns:
        (success: bool, stdout: str)
    """
    result = _run(["exec", demo_path, lang, code], workdir=workdir)
    if result.returncode != 0:
        logger.warning("showboat exec exited %d: %s", result.returncode, result.stderr)
    # showboat prints the captured output to stdout regardless of exit code
    return (result.returncode == 0, result.stdout)


def image(demo_path: str, script: str, workdir: Optional[str] = None) -> bool:
    """Run a script expected to produce an image, embed in demo document."""
    result = _run(["image", demo_path, script], workdir=workdir)
    if result.returncode != 0:
        logger.error("showboat image failed: %s", result.stderr)
        return False
    return True


def pop(demo_path: str, workdir: Optional[str] = None) -> bool:
    """Remove the most recent entry from a demo document."""
    result = _run(["pop", demo_path], workdir=workdir)
    return result.returncode == 0


def verify(demo_path: str, workdir: Optional[str] = None) -> tuple:
    """Re-run all code blocks and diff against recorded output.

    Returns:
        (passed: bool, diff_output: str)
    """
    result = _run(["verify", demo_path], workdir=workdir)
    passed = result.returncode == 0
    output = result.stdout + result.stderr
    if not passed:
        logger.warning("showboat verify FAILED for %s:\n%s", demo_path, output)
    else:
        logger.info("showboat verify PASSED for %s", demo_path)
    return (passed, output)


def create_build_demo(
    output_dir: str,
    demo_dir: str,
    project_name: str = "Dark App",
    files_generated: int = 0,
    stack_desc: str = "",
) -> Optional[str]:
    """Create a full build demo artifact for a factory run.

    This is the high-level function used by the factory pipeline.
    It creates a Showboat document that proves the build produced
    real files and the generated app boots.

    Args:
        output_dir: The generated app directory.
        demo_dir: Where to write the demo (e.g. demos/).
        project_name: Name for the demo title.
        files_generated: Count of files the worker produced.
        stack_desc: Human-readable stack description.

    Returns:
        Path to the demo file, or None if showboat is unavailable.
    """
    if not is_available():
        logger.info("Showboat not installed -- skipping demo artifact generation.")
        return None

    os.makedirs(demo_dir, exist_ok=True)
    demo_path = os.path.join(demo_dir, "build-report.md")

    # Use the output_dir as workdir so relative paths resolve

    if not init(demo_path, f"Build Report: {project_name}", workdir=None):
        return None

    note(demo_path, f"Stack: {stack_desc}")
    note(demo_path, f"Files generated: {files_generated}")
    note(demo_path, f"Output directory: `{output_dir}`")

    # Prove files exist by listing them
    if os.name == "nt":
        list_cmd = f"Get-ChildItem -Recurse -File '{output_dir}' | Select-Object -ExpandProperty FullName"
        exec_cmd(demo_path, "powershell", list_cmd)
    else:
        exec_cmd(demo_path, "bash", f"find {output_dir} -type f | head -50")

    # Check for manifest.json
    manifest_path = os.path.join(output_dir, "manifest.json")
    if os.path.exists(manifest_path):
        note(demo_path, "manifest.json contents:")
        if os.name == "nt":
            exec_cmd(demo_path, "powershell", f"Get-Content '{manifest_path}'")
        else:
            exec_cmd(demo_path, "bash", f"cat {manifest_path}")

    # Check for requirements.txt / package.json
    for dep_file in ["requirements.txt", "package.json"]:
        dep_path = os.path.join(output_dir, dep_file)
        if os.path.exists(dep_path):
            note(demo_path, f"{dep_file} contents:")
            if os.name == "nt":
                exec_cmd(demo_path, "powershell", f"Get-Content '{dep_path}'")
            else:
                exec_cmd(demo_path, "bash", f"cat {dep_path}")

    logger.info("Showboat demo artifact created: %s", demo_path)
    return demo_path
