"""Dark App Factory MCP server — fleet control + factory operations.

Tools
-----
factory_fleet   — dashboard health, log tail, settings (read-only ops)
factory_run     — start a generation run (writes vibe, spawns subprocess)
factory_status  — poll run status / progress
factory_stop    — cancel a running build
factory_launch  — start the generated app from an output directory
factory_assess  — static analysis + Prefab UI card + dashboard push
factory_outputs — list completed output directories
"""

from __future__ import annotations

import ast
import json
import os
import re
import signal
import subprocess
import sys
import time
import uuid
from enum import Enum
from pathlib import Path
from typing import Any, Optional

import httpx
from fastmcp import FastMCP
from fastmcp.tools import ToolResult
from prefab_ui.app import PrefabApp
from prefab_ui.components import (
    Badge,
    Card,
    CardContent,
    Column,
    DataTable,
    DataTableColumn,
    Grid,
    Heading,
    Muted,
    Row,
    Separator,
    Text,
)
from pydantic import BaseModel, ConfigDict, Field

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
REPO_ROOT: Path = Path(__file__).resolve().parents[3]
LOG_FILE      = REPO_ROOT / "logs" / "factory.log"
SETTINGS_FILE = REPO_ROOT / "web" / "settings.json"
WEB_START     = REPO_ROOT / "web" / "start.ps1"
OUTPUTS_DIR   = REPO_ROOT / "outputs"
PYTHON        = sys.executable

_RUNS: dict[str, dict[str, Any]] = {}

# ---------------------------------------------------------------------------
# Server
# ---------------------------------------------------------------------------
mcp = FastMCP(
    name="dark-app-factory-mcp",
    instructions=(
        "Control Dark App Factory. Use factory_run to generate an app, "
        "factory_status to poll, factory_assess to analyse output (renders a UI card), "
        "factory_launch to start the app, factory_outputs to list builds, "
        "factory_fleet for dashboard/log ops."
    ),
)

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------
def _web_base() -> str:
    return os.getenv("DAF_WEB_BASE", "http://127.0.0.1:10738").rstrip("/")


async def _http_json(url: str, method: str = "GET") -> dict[str, Any]:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.request(method, url)
            try:
                body: Any = r.json()
            except Exception:
                body = {"raw": r.text[:2000]}
            return {"success": r.is_success, "status_code": r.status_code, "url": url, "body": body}
    except httpx.RequestError as exc:
        return {"success": False, "error": str(exc), "url": url}


def _tail_log(lines: int = 80, search: str = "") -> list[str]:
    if not LOG_FILE.exists():
        return []
    text = LOG_FILE.read_text(encoding="utf-8", errors="replace").splitlines()
    if search.strip():
        needle = search.lower()
        text = [ln for ln in text if needle in ln.lower()]
    return text[-lines:]


def _list_outputs() -> list[dict[str, Any]]:
    if not OUTPUTS_DIR.exists():
        return []
    results = []
    for d in sorted(OUTPUTS_DIR.iterdir(), reverse=True):
        if not d.is_dir() or d.name.startswith("_run_"):
            continue
        manifest: dict = {}
        mp = d / "manifest.json"
        if mp.exists():
            try:
                manifest = json.loads(mp.read_text(encoding="utf-8"))
            except Exception:
                pass
        readme_snippet = ""
        rp = d / "README.md"
        if rp.exists():
            readme_snippet = rp.read_text(encoding="utf-8", errors="replace")[:300]
        results.append({
            "name": d.name,
            "path": str(d),
            "mtime": d.stat().st_mtime,
            "mtime_human": time.strftime("%Y-%m-%d %H:%M", time.localtime(d.stat().st_mtime)),
            "stack": manifest.get("stack", "unknown"),
            "project_name": manifest.get("project_name", ""),
            "file_count": len(manifest.get("files", [])) or None,
            "readme_snippet": readme_snippet,
        })
    return results


# ---------------------------------------------------------------------------
# Tool: factory_fleet
# ---------------------------------------------------------------------------
class FleetOp(str, Enum):
    ping             = "ping"
    web_health       = "web_health"
    web_status       = "web_status"
    dashboard_url    = "dashboard_url"
    launch_dashboard = "launch_dashboard"
    tail_log         = "tail_log"
    read_settings    = "read_settings"


class FleetInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    operation: FleetOp = Field(description="ping|web_health|web_status|dashboard_url|launch_dashboard|tail_log|read_settings")
    lines:     int     = Field(default=80,  ge=1, le=2000, description="tail_log: lines from end")
    log_search: str    = Field(default="",  description="tail_log: substring filter")


@mcp.tool(name="factory_fleet", annotations={"title": "Dark App Factory Fleet Control",
          "readOnlyHint": False, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True})
async def factory_fleet(params: FleetInput) -> str:
    """Dashboard health, log tailing, settings and launch for the Dark App Factory web UI."""
    op, base = params.operation, _web_base()
    if op == FleetOp.ping:
        return json.dumps({"success": True, "repo_root": str(REPO_ROOT), "web_base": base})
    if op == FleetOp.dashboard_url:
        return json.dumps({"success": True, "url": f"{base}/"})
    if op == FleetOp.web_health:
        return json.dumps(await _http_json(f"{base}/api/v1/health"))
    if op == FleetOp.web_status:
        return json.dumps(await _http_json(f"{base}/api/status"))
    if op == FleetOp.launch_dashboard:
        if not WEB_START.exists():
            return json.dumps({"success": False, "error": "web/start.ps1 not found"})
        try:
            subprocess.Popen(["powershell.exe", "-ExecutionPolicy", "Bypass", "-File", str(WEB_START)],
                             cwd=str(REPO_ROOT), creationflags=subprocess.CREATE_NEW_CONSOLE)
            return json.dumps({"success": True, "message": "Dashboard launched."})
        except OSError as exc:
            return json.dumps({"success": False, "error": str(exc)})
    if op == FleetOp.tail_log:
        if not LOG_FILE.exists():
            return json.dumps({"success": False, "error": "Log file not found."})
        tail = _tail_log(params.lines, params.log_search)
        return json.dumps({"success": True, "lines": tail, "count": len(tail)})
    if op == FleetOp.read_settings:
        if not SETTINGS_FILE.exists():
            return json.dumps({"success": True, "settings": None})
        try:
            return json.dumps({"success": True, "settings": json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))})
        except json.JSONDecodeError as exc:
            return json.dumps({"success": False, "error": str(exc)})
    return json.dumps({"success": False, "error": "unhandled operation"})


# ---------------------------------------------------------------------------
# Tool: factory_run
# ---------------------------------------------------------------------------
class RunInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    vibe: str = Field(..., min_length=10, max_length=8000,
        description="Plain-language description of what to build. Can include '## Tech Stack' section.")
    output_name:    Optional[str] = Field(default=None, description="Directory name under outputs/. Auto-generated if omitted.")
    foreman_model:  Optional[str] = Field(default=None, description="Ollama model for planning.")
    worker_model:   Optional[str] = Field(default=None, description="Ollama model for code generation.")


@mcp.tool(name="factory_run", annotations={"title": "Start a generation run",
          "readOnlyHint": False, "destructiveHint": False, "idempotentHint": False, "openWorldHint": False})
async def factory_run(params: RunInput) -> str:
    """Start a full factory generation run from a vibe/prompt. Returns run_id for polling."""
    run_id   = str(uuid.uuid4())[:8]
    work_dir = REPO_ROOT / "outputs" / f"_run_{run_id}"
    work_dir.mkdir(parents=True, exist_ok=True)
    vibe_path = work_dir / "vibe.md"
    vibe_path.write_text(params.vibe, encoding="utf-8")

    if params.output_name:
        output_dir = str(OUTPUTS_DIR / params.output_name)
    else:
        i = 1
        while (OUTPUTS_DIR / f"output_{i:03d}").exists():
            i += 1
        output_dir = str(OUTPUTS_DIR / f"output_{i:03d}")

    fm = f", foreman_model='{params.foreman_model}'" if params.foreman_model else ""
    wm = f", worker_model='{params.worker_model}'"   if params.worker_model  else ""
    cmd = [PYTHON, "-c",
           f"import asyncio,sys; sys.path.insert(0,r'{REPO_ROOT}'); "
           f"from factory import main_flow; "
           f"asyncio.run(main_flow(vibe_path=r'{vibe_path}', output_dir=r'{output_dir}', "
           f"work_dir=r'{work_dir}'{fm}{wm}))"]

    log_path = work_dir / "run.log"
    try:
        with open(log_path, "w", encoding="utf-8") as lf:
            proc = subprocess.Popen(cmd, cwd=str(REPO_ROOT), stdout=lf,
                                    stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL)
    except Exception as exc:
        return json.dumps({"success": False, "error": str(exc), "run_id": run_id})

    _RUNS[run_id] = {"run_id": run_id, "pid": proc.pid, "proc": proc,
                     "output_dir": output_dir, "work_dir": str(work_dir),
                     "log_path": str(log_path), "vibe_snippet": params.vibe[:200],
                     "started_at": time.strftime("%Y-%m-%d %H:%M:%S"), "status": "running"}
    return json.dumps({"success": True, "run_id": run_id, "pid": proc.pid,
                       "output_dir": output_dir, "log_path": str(log_path),
                       "message": f"Started. Poll with factory_status(run_id='{run_id}')."})


# ---------------------------------------------------------------------------
# Tool: factory_status
# ---------------------------------------------------------------------------
class StatusInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    run_id:   Optional[str] = Field(default=None, description="run_id from factory_run. Omit to list all runs.")
    log_tail: int           = Field(default=30, ge=0, le=500, description="Log lines to include.")


@mcp.tool(name="factory_status", annotations={"title": "Poll run status",
          "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False})
async def factory_status(params: StatusInput) -> str:
    """Poll a factory_run or list all runs."""
    if not params.run_id:
        summary = []
        for rec in _RUNS.values():
            code = rec["proc"].poll()
            summary.append({"run_id": rec["run_id"],
                            "status": "running" if code is None else ("completed" if code == 0 else "failed"),
                            "exit_code": code, "started_at": rec["started_at"],
                            "output_dir": rec["output_dir"], "vibe_snippet": rec["vibe_snippet"]})
        return json.dumps({"success": True, "runs": summary})

    if params.run_id not in _RUNS:
        return json.dumps({"success": False, "error": f"Unknown run_id '{params.run_id}'."})

    rec  = _RUNS[params.run_id]
    code = rec["proc"].poll()
    status = "running" if code is None else ("completed" if code == 0 else "failed")
    rec["status"] = status

    result: dict[str, Any] = {"success": True, "run_id": params.run_id, "status": status,
                               "exit_code": code, "pid": rec["pid"],
                               "started_at": rec["started_at"], "output_dir": rec["output_dir"]}

    op = Path(rec["output_dir"])
    if status == "completed" and op.exists():
        result["file_count"] = sum(1 for _ in op.rglob("*") if _.is_file())
        result["message"] = (f"Complete. Use factory_assess() then factory_launch(output_dir='{rec['output_dir']}').")

    lp = Path(rec["log_path"])
    if params.log_tail > 0 and lp.exists():
        result["log_tail"] = lp.read_text(encoding="utf-8", errors="replace").splitlines()[-params.log_tail:]

    return json.dumps(result)


# ---------------------------------------------------------------------------
# Tool: factory_stop
# ---------------------------------------------------------------------------
class StopInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    run_id: str = Field(..., description="run_id to cancel.")


@mcp.tool(name="factory_stop", annotations={"title": "Stop a running build",
          "readOnlyHint": False, "destructiveHint": True, "idempotentHint": False, "openWorldHint": False})
async def factory_stop(params: StopInput) -> str:
    """Cancel a running factory build."""
    if params.run_id not in _RUNS:
        return json.dumps({"success": False, "error": f"Unknown run_id '{params.run_id}'."})
    rec  = _RUNS[params.run_id]
    proc = rec["proc"]
    if proc.poll() is not None:
        return json.dumps({"success": False, "error": "Already finished.", "exit_code": proc.returncode})
    try:
        proc.terminate() if sys.platform == "win32" else os.kill(proc.pid, signal.SIGTERM)
        rec["status"] = "stopped"
        return json.dumps({"success": True, "message": f"Run {params.run_id} terminated."})
    except Exception as exc:
        return json.dumps({"success": False, "error": str(exc)})


# ---------------------------------------------------------------------------
# Tool: factory_launch
# ---------------------------------------------------------------------------
class LaunchInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    output_dir: Optional[str] = Field(default=None, description="Path or name of output. Omit for most recent.")
    port:       Optional[int] = Field(default=None, ge=1024, le=65535, description="Override PORT.")


@mcp.tool(name="factory_launch", annotations={"title": "Launch a generated app",
          "readOnlyHint": False, "destructiveHint": False, "idempotentHint": False, "openWorldHint": False})
async def factory_launch(params: LaunchInput) -> str:
    """Launch the generated app (npm run dev or python main.py) in a new console."""
    if params.output_dir:
        target = Path(params.output_dir)
        if not target.is_absolute():
            target = OUTPUTS_DIR / params.output_dir
    else:
        outputs = _list_outputs()
        if not outputs:
            return json.dumps({"success": False, "error": "No output directories found."})
        target = Path(outputs[0]["path"])

    if not target.exists():
        return json.dumps({"success": False, "error": f"Not found: {target}"})

    has_pkg   = (target / "package.json").exists()
    has_sjs   = (target / "server.js").exists()
    has_mpy   = (target / "main.py").exists()
    has_req   = (target / "requirements.txt").exists()
    is_python = has_mpy or has_req
    is_node   = has_pkg or has_sjs

    if not (is_python or is_node):
        return json.dumps({"success": False, "error": "Cannot detect stack.", "dir": str(target)})

    env      = os.environ.copy()
    launched = []

    def _popen(cmd: str, extra_env: dict | None = None) -> None:
        e = {**env, **(extra_env or {})}
        if sys.platform == "win32":
            subprocess.Popen(["cmd", "/k", cmd], cwd=str(target), env=e,
                             creationflags=subprocess.CREATE_NEW_CONSOLE)
        else:
            subprocess.Popen(["bash", "-c", cmd], cwd=str(target), env=e)

    if is_python:
        bp  = params.port or 8000
        entry = "main.py" if has_mpy else "app.py"
        _popen(f"pip install -r requirements.txt & python {entry}", {"PORT": str(bp)})
        launched.append({"type": "python", "port": bp, "url": f"http://localhost:{bp}"})
        if has_pkg:
            vp = (params.port or 5173)
            npm = "npm.cmd" if sys.platform == "win32" else "npm"
            _popen(f"{npm} install --legacy-peer-deps & {npm} run dev", {"VITE_PORT": str(vp), "PORT": str(bp)})
            launched.append({"type": "vite", "port": vp, "url": f"http://localhost:{vp}"})
    else:
        bp = params.port or 3000
        vp = bp + 1
        npm = "npm.cmd" if sys.platform == "win32" else "npm"
        _popen(f"{npm} install --legacy-peer-deps & {npm} run dev", {"PORT": str(bp), "VITE_PORT": str(vp)})
        launched.append({"type": "node", "backend_port": bp, "frontend_port": vp,
                         "urls": [f"http://localhost:{bp}", f"http://localhost:{vp}"]})

    return json.dumps({"success": True, "output_dir": str(target), "launched": launched,
                       "message": "Allow ~15s for startup."})


# ---------------------------------------------------------------------------
# Tool: factory_assess  (Prefab UI card)
# ---------------------------------------------------------------------------
@mcp.tool(
    name="factory_assess",
    app=True,
    annotations={"title": "Assess generated output — renders interactive card",
                 "readOnlyHint": True, "destructiveHint": False,
                 "idempotentHint": True, "openWorldHint": False},
)
async def factory_assess(
    output_dir: Optional[str] = None,
    push_to_webapp: bool = True,
) -> ToolResult:
    """Analyse a generated app and render an interactive Prefab assessment card.

    Static analysis only (no LLM): file counts, entry point detection, missing
    files, JS/Python syntax errors, framer-motion import correctness, runt/stub
    detection, tree-character filenames. Scores 0-100, letter grade A-F.

    The result is shown as a Prefab UI card (stats grid + issue table + language
    breakdown) in supporting MCP clients, and as a text summary in all others.
    Also POSTs the full JSON to the web dashboard if reachable.

    Args:
        output_dir: Path or bare name (e.g. 'output_008'). Omit for most recent.
        push_to_webapp: POST result to DAF_WEB_BASE/api/assess (default True).

    Returns:
        ToolResult with Prefab card (structured_content) + text summary (content).
    """
    # -----------------------------------------------------------------------
    # 1. Resolve directory
    # -----------------------------------------------------------------------
    if output_dir:
        target = Path(output_dir)
        if not target.is_absolute():
            target = OUTPUTS_DIR / output_dir
    else:
        outputs = _list_outputs()
        if not outputs:
            return ToolResult(content="Error: No output directories found.")
        target = Path(outputs[0]["path"])

    if not target.exists():
        return ToolResult(content=f"Error: Directory not found: {target}")

    # -----------------------------------------------------------------------
    # 2. Manifest
    # -----------------------------------------------------------------------
    manifest: dict = {}
    manifest_path = target / "manifest.json"
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    project_name = manifest.get("project_name", target.name)
    stack        = manifest.get("stack", "unknown")

    # -----------------------------------------------------------------------
    # 3. Walk files
    # -----------------------------------------------------------------------
    SKIP_DIRS   = {".git", "node_modules", "__pycache__", ".venv", "venv"}
    SKIP_EXT    = {".pyc", ".pyo", ".map"}
    RUNT_THRESH = {".tsx": 500, ".jsx": 500, ".py": 400, ".js": 300}
    TREE_CHARS  = {"│", "├", "└", "─"}

    all_files: list[Path] = [
        f for f in target.rglob("*")
        if f.is_file()
        and not any(p in SKIP_DIRS for p in f.parts)
        and f.suffix not in SKIP_EXT
    ]

    total_files = len(all_files)
    total_size  = sum(f.stat().st_size for f in all_files)

    lang_counts: dict[str, int] = {}
    for f in all_files:
        ext = f.suffix.lower() or "(no ext)"
        lang_counts[ext] = lang_counts.get(ext, 0) + 1
    lang_counts = dict(sorted(lang_counts.items(), key=lambda x: -x[1]))

    # -----------------------------------------------------------------------
    # 4. Checks
    # -----------------------------------------------------------------------
    issues:        list[str] = []
    strengths:     list[str] = []
    syntax_errors: list[str] = []

    def ok(msg: str)  -> None: strengths.append(msg)
    def bad(msg: str) -> None: issues.append(msg)

    has_server_js = (target / "server.js").exists()
    has_main_py   = (target / "main.py").exists()
    has_app_py    = (target / "app.py").exists()
    has_pkg_json  = (target / "package.json").exists()
    has_req       = (target / "requirements.txt").exists()
    has_vite      = (target / "vite.config.ts").exists()
    has_app_tsx   = (target / "src" / "App.tsx").exists()
    has_readme    = (target / "README.md").exists()
    has_git       = (target / ".git").exists()
    has_demos     = (target / "demos").exists()
    has_www       = (target / "www" / "index.html").exists()

    is_node   = has_pkg_json or has_server_js
    is_python = has_main_py or has_app_py or has_req

    if not (is_node or is_python):
        bad("CRITICAL: No entry point (no server.js, main.py, or package.json)")
    else:
        if is_node:
            ok("server.js present") if has_server_js else bad("package.json present but server.js missing — won't start")
        if is_python:
            if has_main_py or has_app_py:
                ok(f"Python entry point: {'main.py' if has_main_py else 'app.py'}")
            else:
                bad("requirements.txt present but no main.py or app.py")

    if is_node and has_pkg_json:
        try:
            pkg      = json.loads((target / "package.json").read_text(encoding="utf-8"))
            all_deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
            ok("npm run dev present") if "dev" in pkg.get("scripts", {}) else bad("package.json missing 'dev' script")
            bloat = [d for d in all_deps if d in {
                "three", "@react-three/fiber", "langchain", "@langchain/core",
                "@pinecone-database/pinecone", "midi-writer-js", "wavesurfer.js",
                "video.js", "tone", "howler", "moment",
            }]
            if bloat:
                bad(f"Unjustified kitchen-sink deps: {', '.join(bloat)}")
        except Exception:
            bad("package.json is not valid JSON")

    (ok("vite.config.ts present") if has_vite
     else bad("vite.config.ts missing — frontend won't start") if (is_node and has_pkg_json) else None)
    ok("Git repo initialised")  if has_git    else bad("No .git directory")
    ok("demos/ artifacts")      if has_demos  else None
    ok("www/index.html present") if has_www   else None
    ok("manifest.json present") if (target / "manifest.json").exists() else None

    if has_readme:
        size = (target / "README.md").stat().st_size
        ok("README.md present")   if size >= 500 else bad(f"README.md stub ({size} bytes)")
    else:
        bad("README.md missing")

    if has_app_tsx:
        tsx = (target / "src" / "App.tsx").read_text(encoding="utf-8", errors="replace")
        if "import FramerMotion from" in tsx:
            bad("src/App.tsx: default framer-motion import (crashes at runtime)")
        elif "exitBeforeEnter" in tsx:
            bad("src/App.tsx: deprecated exitBeforeEnter prop")
        else:
            ok("framer-motion import correct")
        for _, comp in re.findall(r"from\s+['\"](?:\./)?(?:pages|components)/([^'\"]+)['\"]", tsx):
            comp = comp.replace(".tsx", "").replace(".jsx", "")
            if not any((target / "src" / d / f"{comp}.tsx").exists() for d in ["pages", "components"]):
                bad(f"Missing component: src/*/{comp}.tsx")

    tree_names = [str(f.relative_to(target)) for f in all_files
                  if any(c in f.name for c in TREE_CHARS)]
    if tree_names:
        bad(f"Tree-char filenames ({len(tree_names)}): " + ", ".join(tree_names[:4])
            + (" …" if len(tree_names) > 4 else ""))

    runts = [f"{f.relative_to(target)} ({f.stat().st_size}B)"
             for f in all_files
             if (t := RUNT_THRESH.get(f.suffix.lower())) and f.stat().st_size < t]
    bad(f"Runt/stub files: {', '.join(runts[:5])}") if runts else ok("No runt/stub files")

    js_files = [f for f in all_files if f.suffix == ".js" and not f.name.endswith(".min.js")]
    for jf in js_files[:20]:
        try:
            r = subprocess.run(["node", "--check", str(jf)],
                               capture_output=True, text=True, timeout=10)
            if r.returncode != 0:
                syntax_errors.append(f"{jf.relative_to(target)}: "
                                     + (r.stderr or r.stdout).strip().splitlines()[0][:100])
        except Exception:
            pass
    ok(f"No JS syntax errors ({len(js_files)} checked)") if not syntax_errors and js_files else None

    py_files = [f for f in all_files if f.suffix == ".py"]
    for pf in py_files[:20]:
        try:
            ast.parse(pf.read_text(encoding="utf-8", errors="replace"))
        except SyntaxError as e:
            syntax_errors.append(f"{pf.relative_to(target)} line {e.lineno}: {e.msg}")
    ok(f"No Python syntax errors ({len(py_files)} checked)") if not syntax_errors and py_files else None

    # -----------------------------------------------------------------------
    # 5. Score + grade
    # -----------------------------------------------------------------------
    score = 100
    PENALTIES = {"CRITICAL": 40, "won't start": 25, "won't work": 20, "missing": 10,
                 "not valid JSON": 15, "stub": 8, "runt": 10, "tree-char": 15,
                 "crash": 20, "syntax": 12, "kitchen-sink": 5, "deprecated": 8}
    for issue in issues:
        il = issue.lower()
        for kw, pen in PENALTIES.items():
            if kw in il:
                score -= pen
                break
    score -= len(syntax_errors) * 8
    score = max(0, min(100, score))
    grade = "A" if score >= 85 else "B" if score >= 70 else "C" if score >= 55 else "D" if score >= 40 else "F"

    # -----------------------------------------------------------------------
    # 6. Payload
    # -----------------------------------------------------------------------
    summary_text = (f"{project_name} — {stack}. {total_files} files, {total_size // 1024}KB. "
                    f"{len(issues)} issues, {len(syntax_errors)} syntax errors. Grade: {grade} ({score}/100).")
    payload = {
        "output_dir": str(target), "project_name": project_name, "stack": stack,
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "file_stats": {"total_files": total_files, "total_size_kb": total_size // 1024,
                       "js_files": len(js_files), "py_files": len(py_files),
                       "tsx_files": lang_counts.get(".tsx", 0), "md_files": lang_counts.get(".md", 0)},
        "language_breakdown": lang_counts, "structure_score": score,
        "completeness_issues": issues, "syntax_errors": syntax_errors,
        "strengths": strengths, "grade": grade, "summary": summary_text,
    }

    # -----------------------------------------------------------------------
    # 7. Push to webapp
    # -----------------------------------------------------------------------
    push_note = ""
    if push_to_webapp:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                r = await client.post(f"{_web_base()}/api/assess", json=payload)
            push_note = "✓ dashboard" if r.is_success else f"dashboard HTTP {r.status_code}"
        except httpx.RequestError:
            push_note = "dashboard unreachable"

    # -----------------------------------------------------------------------
    # 8. Prefab UI card
    # -----------------------------------------------------------------------
    GRADE_VARIANT = {"A": "success", "B": "secondary", "C": "warning", "D": "destructive", "F": "destructive"}
    GRADE_LABEL   = {"A": "A — Excellent", "B": "B — Good", "C": "C — Needs Work", "D": "D — Poor", "F": "F — Broken"}

    problem_rows = [{"kind": "Issue",  "detail": i} for i in issues] + \
                   [{"kind": "Syntax", "detail": e} for e in syntax_errors]
    lang_rows    = [{"ext": ext, "count": cnt} for ext, cnt in list(lang_counts.items())[:10]]

    with Column(gap=6, css_class="p-6 max-w-3xl") as view:

        with Row(gap=4, align="center"):
            Heading(f"Assessment: {project_name}")
            Badge(GRADE_LABEL[grade], variant=GRADE_VARIANT[grade])

        Muted(f"{stack}  ·  {target.name}")
        Separator()

        # Stat cards
        with Grid(columns=4, gap=3):
            for label, value in [("Score", f"{score}/100"), ("Files", str(total_files)),
                                  ("Size", f"{total_size // 1024} KB"),
                                  ("Issues", str(len(issues) + len(syntax_errors)))]:
                with Card():
                    with CardContent(css_class="pt-4"):
                        Muted(label)
                        Heading(value)

        # Language table
        Heading("Language Breakdown", css_class="text-base font-semibold mt-2")
        DataTable(
            columns=[DataTableColumn(key="ext",   header="Extension", sortable=True),
                     DataTableColumn(key="count", header="Files",     sortable=True)],
            rows=lang_rows,
        )

        # Strengths
        if strengths:
            Heading("Strengths", css_class="text-base font-semibold mt-2")
            with Column(gap=1):
                for s in strengths:
                    with Row(gap=2, align="center"):
                        Badge("✓", variant="success")
                        Text(s, css_class="text-sm")

        # Issues & errors
        Heading("Issues & Errors", css_class="text-base font-semibold mt-2")
        if problem_rows:
            DataTable(
                columns=[DataTableColumn(key="kind",   header="Type",   sortable=True),
                         DataTableColumn(key="detail", header="Detail", sortable=False)],
                rows=problem_rows,
                searchable=True,
            )
        else:
            Badge("No issues found", variant="success")

        if push_note:
            Muted(push_note, css_class="text-xs mt-2")

    return ToolResult(
        content=summary_text,
        structured_content=PrefabApp(view=view),
    )


# ---------------------------------------------------------------------------
# Tool: factory_outputs
# ---------------------------------------------------------------------------
class OutputsInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    limit: int = Field(default=10, ge=1, le=50, description="Max results.")


@mcp.tool(name="factory_outputs", annotations={"title": "List output directories",
          "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False})
async def factory_outputs(params: OutputsInput) -> str:
    """List completed generation outputs, newest first."""
    outputs = _list_outputs()[:params.limit]
    return json.dumps({"success": True, "count": len(outputs), "outputs": outputs})
