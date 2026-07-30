import asyncio
import json
import os
import subprocess
import time
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

import factory
from src.ghost_extractor import GhostExtractor
from src.llm_client import LLMClient
from src.specialists.council import get_council
from src.utils.logger import logger
from src.utils.progress import progress

app = FastAPI(title="Dark App Factory Dashboard")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:10738",
        "http://127.0.0.1:10738",
        "http://localhost:10739",
        "http://127.0.0.1:10739",
        "http://tauri.localhost",
        "https://tauri.localhost",
        "tauri://localhost",
    ],
    allow_origin_regex=r"https?://(?:[a-zA-Z0-9-]+\.ts\.net|.*?\.tail-[a-f0-9]+\.ts\.net|tauri\.localhost|localhost|127\.0\.0\.1|192\.168\.\d{1,3}\.\d{1,3}|10\.\d{1,3}\.\d{1,3}\.\d{1,3}|100\.\d{1,3}\.\d{1,3}\.\d{1,3})(?::\d+)?$|^tauri://localhost$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
ghost_extractor = GhostExtractor()

ROOT_DIR = Path(__file__).resolve().parent.parent
UI_DIR = Path(__file__).resolve().parent
LOG_FILE = ROOT_DIR / "logs" / "factory.log"
SETTINGS_FILE = ROOT_DIR / "web" / "settings.json"
DOCS_DIR = ROOT_DIR / "docs"
README_FILE = ROOT_DIR / "README.md"

DEFAULT_SETTINGS = {
    "provider": "ollama",
    "base_url": "http://localhost:11434/v1",
    "foreman_model": "llama3.1:latest",
    "worker_model": "qwen2.5-coder:latest",
    "api_key": "ollama",
    "context_length": 65536,
    "timeout_seconds": 180,
}


class BuildRequest(BaseModel):
    vibe_content: str
    output_dir: str = "output"
    ghost_blueprint_path: str | None = None


class RefineRequest(BaseModel):
    prompt: str
    history: list[str] = Field(default_factory=list)


class SuggestRequest(BaseModel):
    query: str


class GhostRequest(BaseModel):
    url: str


class FleetLaunchRequest(BaseModel):
    repo_path: str


class SettingsPayload(BaseModel):
    provider: str
    base_url: str
    foreman_model: str
    worker_model: str
    api_key: str = "ollama"
    context_length: int = 65536
    timeout_seconds: int = 180


state = {"active_builds": 0, "last_verdict": "No runs yet"}


def load_settings() -> dict:
    if not SETTINGS_FILE.exists():
        SETTINGS_FILE.write_text(
            json.dumps(DEFAULT_SETTINGS, indent=2), encoding="utf-8"
        )
        return dict(DEFAULT_SETTINGS)
    try:
        data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        logger.warning("Invalid web/settings.json, reverting to defaults.")
        data = {}
    merged = dict(DEFAULT_SETTINGS)
    merged.update(data)
    return merged


def save_settings(settings: dict) -> dict:
    normalized = dict(DEFAULT_SETTINGS)
    normalized.update(settings)
    SETTINGS_FILE.write_text(json.dumps(normalized, indent=2), encoding="utf-8")
    return normalized


def list_help_docs() -> list[dict]:
    help_docs = []
    for path in sorted(DOCS_DIR.glob("*.md")):
        help_docs.append(
            {"id": path.stem, "title": path.stem.replace("_", " "), "path": str(path)}
        )
    if README_FILE.exists():
        help_docs.insert(
            0, {"id": "README", "title": "README", "path": str(README_FILE)}
        )
    return help_docs


def read_log_lines(lines: int, search: str = "") -> list[str]:
    if not LOG_FILE.exists():
        return []
    log_lines = LOG_FILE.read_text(encoding="utf-8", errors="ignore").splitlines()
    if search:
        needle = search.lower()
        log_lines = [line for line in log_lines if needle in line.lower()]
    if lines > 0:
        log_lines = log_lines[-lines:]
    return log_lines


async def launch_factory(vibe: str, ghost_blueprint_path: str | None = None) -> None:
    try:
        state["active_builds"] += 1
        ghost_dna = None
        if ghost_blueprint_path and os.path.exists(ghost_blueprint_path):
            with open(ghost_blueprint_path, "r", encoding="utf-8") as file:
                ghost_dna = json.load(file)
        # Write vibe content to a temp file — main_flow expects a file path, not raw content
        vibe_path = ROOT_DIR / "outputs" / f"_vibe_{int(time.time())}.md"
        vibe_path.parent.mkdir(parents=True, exist_ok=True)
        vibe_path.write_text(vibe, encoding="utf-8")
        await factory.main_flow(vibe_path=str(vibe_path), ghost_dna=ghost_dna)
        state["last_verdict"] = "PASS"
    except Exception:
        logger.exception("Factory execution failed")
        state["last_verdict"] = "FAIL: see server log"
    finally:
        state["active_builds"] = max(0, state["active_builds"] - 1)


class RunRequest(BaseModel):
    vibe: str
    output_name: str | None = None
    foreman_model: str | None = None
    worker_model: str | None = None


class StopRequest(BaseModel):
    run_id: str


class LaunchOutputRequest(BaseModel):
    output_dir: str
    port: int | None = None


# In-memory run registry
_runs: dict = {}


@app.post("/api/run")
async def start_run(req: RunRequest):
    """Start a factory generation run as a background subprocess."""
    import uuid, time, sys
    from pathlib import Path as P

    run_id = str(uuid.uuid4())[:8]
    work_dir = ROOT_DIR / "outputs" / f"_run_{run_id}"
    work_dir.mkdir(parents=True, exist_ok=True)
    vibe_path = work_dir / "vibe.md"
    vibe_path.write_text(req.vibe, encoding="utf-8")

    # Next output_NNN
    outputs_dir = ROOT_DIR / "outputs"
    if req.output_name:
        output_dir = str(outputs_dir / req.output_name)
    else:
        i = 1
        while (outputs_dir / f"output_{i:03d}").exists():
            i += 1
        output_dir = str(outputs_dir / f"output_{i:03d}")

    foreman_arg = f", foreman_model='{req.foreman_model}'" if req.foreman_model else ""
    worker_arg = f", worker_model='{req.worker_model}'" if req.worker_model else ""

    cmd = [
        sys.executable, "-c",
        (
            "import asyncio, sys; sys.path.insert(0, r'{repo}'); "
            "from factory import main_flow; "
            "asyncio.run(main_flow("
            "vibe_path=r'{vibe}', output_dir=r'{out}', work_dir=r'{work}'"
            "{fm}{wm}))"
        ).format(
            repo=str(ROOT_DIR),
            vibe=str(vibe_path),
            out=output_dir,
            work=str(work_dir),
            fm=foreman_arg,
            wm=worker_arg,
        ),
    ]

    log_path = work_dir / "run.log"
    with open(log_path, "w", encoding="utf-8") as lf:
        proc = subprocess.Popen(
            cmd, cwd=str(ROOT_DIR),
            stdout=lf, stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
        )

    _runs[run_id] = {
        "run_id": run_id, "pid": proc.pid, "proc": proc,
        "output_dir": output_dir, "work_dir": str(work_dir),
        "log_path": str(log_path),
        "vibe_snippet": req.vibe[:200],
        "started_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "status": "running",
    }
    return {
        "success": True, "run_id": run_id, "pid": proc.pid,
        "output_dir": output_dir, "log_path": str(log_path),
    }


@app.get("/api/run/{run_id}")
async def poll_run(run_id: str, log_tail: int = 40):
    if run_id not in _runs:
        raise HTTPException(status_code=404, detail=f"Unknown run_id: {run_id}")
    rec = _runs[run_id]
    proc = rec["proc"]
    exit_code = proc.poll()
    if exit_code is None:
        status = "running"
    elif exit_code == 0:
        status = "completed"
    else:
        status = "failed"
    rec["status"] = status

    result: dict = {
        "run_id": run_id, "status": status, "exit_code": exit_code,
        "pid": rec["pid"], "started_at": rec["started_at"],
        "output_dir": rec["output_dir"], "vibe_snippet": rec["vibe_snippet"],
    }
    from pathlib import Path as P
    op = P(rec["output_dir"])
    if status == "completed" and op.exists():
        result["file_count"] = sum(1 for _ in op.rglob("*") if _.is_file())
    lp = P(rec["log_path"])
    if log_tail > 0 and lp.exists():
        lines = lp.read_text(encoding="utf-8", errors="replace").splitlines()
        result["log_tail"] = lines[-log_tail:]
    return result


@app.get("/api/runs")
async def list_runs():
    summary = []
    for rec in _runs.values():
        code = rec["proc"].poll()
        summary.append({
            "run_id": rec["run_id"],
            "status": "running" if code is None else ("completed" if code == 0 else "failed"),
            "exit_code": code,
            "started_at": rec["started_at"],
            "output_dir": rec["output_dir"],
            "vibe_snippet": rec["vibe_snippet"],
        })
    return {"runs": list(reversed(summary))}


@app.post("/api/run/{run_id}/stop")
async def stop_run(run_id: str):
    if run_id not in _runs:
        raise HTTPException(status_code=404, detail=f"Unknown run_id: {run_id}")
    rec = _runs[run_id]
    proc = rec["proc"]
    if proc.poll() is not None:
        return {"success": False, "detail": "Process already finished."}
    proc.terminate()
    rec["status"] = "stopped"
    return {"success": True, "message": f"Run {run_id} terminated."}


@app.get("/api/outputs")
async def list_outputs(limit: int = 20):
    import time as _time
    outputs_dir = ROOT_DIR / "outputs"
    if not outputs_dir.exists():
        return {"outputs": []}
    dirs = sorted(
        [d for d in outputs_dir.iterdir() if d.is_dir() and not d.name.startswith("_run_")],
        reverse=True,
    )[:limit]
    result = []
    for d in dirs:
        manifest = {}
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
        result.append({
            "name": d.name,
            "path": str(d),
            "mtime": d.stat().st_mtime,
            "mtime_human": _time.strftime("%Y-%m-%d %H:%M", _time.localtime(d.stat().st_mtime)),
            "stack": manifest.get("stack", ""),
            "project_name": manifest.get("project_name", ""),
            "file_count": len(manifest.get("files", [])) or None,
            "readme_snippet": readme_snippet,
        })
    return {"outputs": result}


@app.post("/api/outputs/launch")
async def launch_output(req: LaunchOutputRequest):
    import sys
    from pathlib import Path as P
    target = P(req.output_dir)
    if not target.exists():
        raise HTTPException(status_code=404, detail=f"Directory not found: {req.output_dir}")

    has_pj = (target / "package.json").exists()
    has_sj = (target / "server.js").exists()
    has_mp = (target / "main.py").exists()
    has_req = (target / "requirements.txt").exists()
    is_python = has_mp or has_req
    is_node = has_pj or has_sj

    if not is_python and not is_node:
        raise HTTPException(status_code=400, detail="Cannot detect stack in output directory.")

    env = os.environ.copy()
    launched = []

    if is_python:
        port = req.port or 8000
        env["PORT"] = str(port)
        entry = "main.py" if has_mp else "app.py"
        cmd = f"pip install -r requirements.txt & python {entry}"
        subprocess.Popen(
            ["cmd", "/k", cmd], cwd=str(target), env=env,
            creationflags=subprocess.CREATE_NEW_CONSOLE,
        )
        launched.append({"type": "python", "port": port, "url": f"http://localhost:{port}"})
        if has_pj:
            vp = (req.port or 5173)
            env2 = env.copy(); env2["VITE_PORT"] = str(vp)
            subprocess.Popen(
                ["cmd", "/k", "npm.cmd install --legacy-peer-deps & npm.cmd run dev"],
                cwd=str(target), env=env2,
                creationflags=subprocess.CREATE_NEW_CONSOLE,
            )
            launched.append({"type": "vite", "port": vp, "url": f"http://localhost:{vp}"})
    else:
        bp = req.port or 3000; vp = bp + 1
        env["PORT"] = str(bp); env["VITE_PORT"] = str(vp)
        subprocess.Popen(
            ["cmd", "/k", "npm.cmd install --legacy-peer-deps & npm.cmd run dev"],
            cwd=str(target), env=env,
            creationflags=subprocess.CREATE_NEW_CONSOLE,
        )
        launched.append({"type": "node", "backend_port": bp, "frontend_port": vp,
                         "url": f"http://localhost:{vp}"})

    return {"success": True, "launched": launched}



class AssessmentResult(BaseModel):
    output_dir: str
    project_name: str
    stack: str
    generated_at: str
    file_stats: dict
    language_breakdown: dict
    structure_score: int       # 0-100
    completeness_issues: list[str]
    syntax_errors: list[str]
    strengths: list[str]
    grade: str                 # A/B/C/D/F
    summary: str


_assessments: dict[str, AssessmentResult] = {}


@app.post("/api/assess")
async def store_assessment(result: AssessmentResult):
    """Store an assessment result from the MCP tool."""
    _assessments[result.output_dir] = result
    return {"success": True, "output_dir": result.output_dir}


@app.get("/api/assess")
async def list_assessments():
    return {"assessments": [a.model_dump() for a in _assessments.values()]}


@app.get("/api/assess/{output_name}")
async def get_assessment(output_name: str):
    # Match by directory name or full path
    for key, val in _assessments.items():
        if key.endswith(output_name) or output_name in key:
            return val.model_dump()
    raise HTTPException(status_code=404, detail=f"No assessment for '{output_name}'")


@app.get("/api/outputs/{output_name}/report")
async def get_output_report(output_name: str):
    """Serve the best available report for an output directory.
    Tries: audit-report.md → build-report.md → lint-report.txt → index.html."""
    candidates = [
        f"demos{os.sep}audit-report.md",
        f"demos{os.sep}build-report.md",
        f"demos{os.sep}lint-report.txt",
        "www/index.html",
        "critique.md",
    ]
    out_dir = ROOT_DIR / "outputs" / output_name
    if not out_dir.exists():
        raise HTTPException(status_code=404, detail=f"Output not found: {output_name}")
    for rel in candidates:
        path = out_dir / rel
        if path.exists():
            return FileResponse(str(path))
    raise HTTPException(status_code=404, detail="No reports found for this output")


    return {
        "active_builds": state["active_builds"],
        "last_verdict": state["last_verdict"],
        "settings_provider": load_settings()["provider"],
    }


@app.get("/api/models")
async def get_models():
    """Discover models from local providers (Ollama, LM Studio) using standard urllib."""
    import urllib.request

    models = []
    providers = [
        {"name": "ollama", "url": "http://localhost:11434/v1/models"},
        {"name": "lmstudio", "url": "http://localhost:1234/v1/models"},
    ]

    def probe(url, provider_name):
        try:
            with urllib.request.urlopen(url, timeout=2.0) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    found = []
                    # OpenAI format: {"data": [{"id": "..."}]}
                    for m in data.get("data", []):
                        found.append({"id": m.get("id", ""), "provider": provider_name})
                    # Ollama format: {"models": [{"name": "..."}]}
                    for m in data.get("models", []):
                        found.append({"id": m.get("name", ""), "provider": provider_name})
                    return found
        except Exception:  # noqa: BLE001
            pass
        # Fallback: try Ollama's /api/tags endpoint
        if provider_name == "ollama":
            try:
                fallback = url.replace("/v1/models", "/api/tags")
                with urllib.request.urlopen(fallback, timeout=2.0) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    return [{"id": m["name"], "provider": "ollama"} for m in data.get("models", []) if "name" in m]
            except Exception:  # noqa: BLE001
                pass
        return []

    results = await asyncio.gather(
        *(asyncio.to_thread(probe, p["url"], p["name"]) for p in providers)
    )
    for res in results:
        models.extend(res)

    return {"success": True, "models": models}


@app.get("/api/progress")
async def get_progress():
    return progress.get_state()


@app.get("/api/settings")
async def get_settings():
    return {"success": True, "settings": load_settings()}


@app.put("/api/settings")
async def update_settings(payload: SettingsPayload):
    settings = save_settings(payload.model_dump())
    return {"success": True, "settings": settings}


@app.get("/api/help")
async def get_help_index():
    return {"success": True, "docs": list_help_docs()}


@app.get("/api/help/{doc_id}")
async def get_help_doc(doc_id: str):
    docs = {entry["id"]: Path(entry["path"]) for entry in list_help_docs()}
    path = docs.get(doc_id)
    if path is None or not path.exists():
        raise HTTPException(status_code=404, detail="Help document not found.")
    return {
        "success": True,
        "id": doc_id,
        "content": path.read_text(encoding="utf-8", errors="ignore"),
    }


@app.get("/api/logs")
async def get_logs(lines: int = 200, search: str = ""):
    safe_lines = max(1, min(lines, 2000))
    return {
        "success": True,
        "lines": read_log_lines(safe_lines, search),
        "file": str(LOG_FILE),
    }


@app.get("/api/logs/download")
async def download_logs():
    if not LOG_FILE.exists():
        raise HTTPException(status_code=404, detail="No log file found.")
    return FileResponse(str(LOG_FILE), filename="factory.log")


@app.get("/api/specialists")
async def list_specialists():
    try:
        specialists = []
        for _, specialist in get_council().items():
            specialists.append(
                {
                    "name": specialist.name,
                    "owned_patterns": specialist.owned_patterns,
                    "requires": specialist.requires,
                    "temperature": specialist.temperature,
                    "docs": specialist.get_docs(),
                }
            )
        return {"success": True, "specialists": specialists}
    except Exception as error:  # noqa: BLE001
        logger.error(f"Error listing specialists: {error}")
        raise HTTPException(status_code=500, detail=str(error))


@app.post("/api/suggest-exemplars")
async def suggest_exemplars(req: SuggestRequest):
    try:
        suggestions = await ghost_extractor.suggest_exemplars(req.query)
        return {"success": True, "suggestions": suggestions}
    except Exception as error:  # noqa: BLE001
        logger.error(f"Discovery error: {error}")
        raise HTTPException(status_code=500, detail=str(error))


@app.post("/api/ghost")
async def ghost_site(req: GhostRequest):
    try:
        result = await ghost_extractor.extract_ghost(req.url)
        return {"success": True, **result}
    except Exception as error:  # noqa: BLE001
        logger.error(f"Ghost extraction error: {error}")
        raise HTTPException(status_code=500, detail=str(error))


@app.post("/api/refine")
async def refine_prompt(request: RefineRequest):
    client = LLMClient(role="foreman")
    context = ""
    if request.history:
        context = "Previous versions:\n" + "\n---\n".join(request.history) + "\n\n"
    improved = await client.generate(
        prompt=f"{context}Current User Prompt: {request.prompt}",
        system_prompt=(
            "Rewrite the user request as a clear implementation brief. "
            "Keep constraints practical and remove vague language."
        ),
        temperature=0.6,
    )
    return {"improved": improved}


@app.post("/api/build")
@app.post("/api/launch")
async def launch(req: BuildRequest):
    if state["active_builds"] > 0:
        raise HTTPException(status_code=429, detail="A build is already in progress.")
    async def _safe_launch():
        try:
            await launch_factory(req.vibe_content, req.ghost_blueprint_path)
        except SystemExit:
            logger.error("Build task attempted sys.exit — blocked")
        except Exception as exc:
            logger.exception("Build task failed: %s", exc)
    asyncio.create_task(_safe_launch())
    return {"success": True, "message": "Build launched."}


@app.get("/api/v1/health")
async def health_v1():
    return {"status": "ok", "server": "dark-app-factory", "version": "2026.3"}


@app.post("/api/v1/fleet/launch")
@app.post("/api/fleet/launch")
async def fleet_launch(request: FleetLaunchRequest):
    path = Path(request.repo_path)
    if not path.exists():
        raise HTTPException(
            status_code=404, detail=f"Path {request.repo_path} does not exist"
        )
    try:
        allowed_base = Path("D:/Dev/repos").resolve()
        path.resolve().relative_to(allowed_base)
    except ValueError as error:
        raise HTTPException(status_code=403, detail="Access denied") from error

    start_script = path / "web_sota" / "start.ps1"
    if not start_script.exists():
        start_script = path / "web" / "start.ps1"
    if not start_script.exists():
        start_script = path / "start.ps1"
    if not start_script.exists():
        raise HTTPException(status_code=400, detail="No start.ps1 found")

    try:
        subprocess.Popen(
            [
                "powershell.exe",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(start_script),
            ],
            cwd=str(path),
            creationflags=subprocess.CREATE_NEW_CONSOLE,
        )
    except Exception as error:  # noqa: BLE001
        logger.error(f"Launch failed: {error}")
        raise HTTPException(status_code=500, detail=str(error))
    return {"success": True, "message": f"Launched {path.name}"}


@app.get("/api/progress/stream")
async def progress_sse():
    """Server-Sent Events endpoint for real-time build progress (polling-based)."""
    from src.utils.progress import progress as _p

    async def event_stream():
        last_id = 0
        yield f"data: {json.dumps({'type': 'state', ** _p.get_state()})}\n\n"
        while True:
            try:
                events = await asyncio.to_thread(_p.get_events_since, last_id)
                for ev in events:
                    last_id = ev["id"]
                    yield f"data: {json.dumps(ev)}\n\n"
                if not events:
                    await asyncio.sleep(0.5)
            except asyncio.CancelledError:
                break
            except Exception:
                break

    from fastapi.responses import StreamingResponse

    return StreamingResponse(event_stream(), media_type="text/event-stream")


SOTA_DIR = ROOT_DIR / "web_sota" / "dist"
if SOTA_DIR.exists() and (SOTA_DIR / "index.html").exists():
    app.mount("/", StaticFiles(directory=str(SOTA_DIR), html=True), name="sota")
elif os.path.exists(UI_DIR / "index.html"):
    app.mount("/", StaticFiles(directory=str(UI_DIR), html=True), name="static")


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", "10738"))
    uvicorn.run(app, host="0.0.0.0", port=port)
