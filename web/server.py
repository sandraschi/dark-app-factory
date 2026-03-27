import os
import json
import asyncio
from typing import List, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import subprocess
from pathlib import Path

from src.utils.logger import logger
from src.llm_client import LLMClient
from src.ghost_extractor import GhostExtractor
from src.utils.progress import progress
import factory
from src.specialists.council import get_council

app = FastAPI(title="Dark App Factory Dashboard")
llm = LLMClient()
ghost_extractor = GhostExtractor()


# Models
class BuildRequest(BaseModel):
    vibe_content: str
    output_dir: Optional[str] = "output"
    ghost_blueprint_path: Optional[str] = None


class RefineRequest(BaseModel):
    prompt: str
    history: List[str] = []


class SuggestRequest(BaseModel):
    query: str


class GhostRequest(BaseModel):
    url: str

    last_verdict: Optional[str] = None


class FleetLaunchRequest(BaseModel):
    repo_path: str


# In-memory state tracking
state = {"active_builds": 0, "last_verdict": "No runs yet"}


@app.get("/api/status")
async def get_status():
    return {"status": "operational", "factory_mode": "SOTA", "build_queue": 0}


@app.get("/api/progress")
async def get_progress():
    """Returns the current build progress."""
    return progress.get_state()


@app.get("/api/specialists")
async def list_specialists():
    """Returns a list of all factory specialists and their metadata."""
    try:
        council = get_council()
        specialists_data = []
        for name, spec in council.items():
            specialists_data.append(
                {
                    "name": spec.name,
                    "owned_patterns": spec.owned_patterns,
                    "requires": spec.requires,
                    "temperature": spec.temperature,
                    "docs": spec.get_docs(),
                }
            )
        return {"success": True, "specialists": specialists_data}
    except Exception as e:
        logger.error(f"Error listing specialists: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/suggest-exemplars")
async def suggest_exemplars(req: SuggestRequest):
    try:
        suggestions = await ghost_extractor.suggest_exemplars(req.query)
        return {"success": True, "suggestions": suggestions}
    except Exception as e:
        logger.error(f"Discovery error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ghost")
async def ghost_site(req: GhostRequest):
    try:
        result = await ghost_extractor.extract_ghost(req.url)
        return {"success": True, **result}
    except Exception as e:
        logger.error(f"Ghosting error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/refine")
async def refine_prompt(request: RefineRequest):
    """Uses LLM to improve user prompt and suggest corrections for bloopers."""
    client = LLMClient(role="foreman")

    system_prompt = """
    You are the Prompt Architect for a Dark App Factory.
    Your goal is to take a user's rough 'vibe' or 'idea' and turn it into a detailed, consistent technical blueprint.
    
    CRITICAL INSTRUCTIONS:
    1. Identify 'bloopers': If the user enters something nonsensical (e.g., 'beekeeper in north greenland' for a code app), gently point out the absurdity and suggest a pivot or a more relevant technical direction.
    2. Flesh out details: Add technical constraints, aesthetic choices (Materialist/Reductionist Vienna style), and expected user flows.
    3. Keep it professional but industrial/direct.
    4. Provide the improved prompt in a clean markdown format.
    
    User history is provided if this is a subsequent refinement.
    """

    context = ""
    if request.history:
        context = "Previous versions:\n" + "\n---\n".join(request.history) + "\n\n"

    improved = await client.generate(
        prompt=f"{context}Current User Prompt: {request.prompt}",
        system_prompt=system_prompt,
        temperature=0.8,
    )

    return {"improved": improved}


@app.post("/api/build")
async def trigger_build(request: BuildRequest):
    if state["active_builds"] > 0:
        raise HTTPException(status_code=429, detail="A build is already in progress.")

    # Run factory in background
    asyncio.create_task(run_factory_task(request.vibe_content, request.output_dir))
    return {"message": "Build started", "output_dir": request.output_dir}


async def run_factory_task(vibe_content: str, output_dir: str):
    state["active_builds"] += 1


async def launch_factory(vibe: str, ghost_blueprint_path: str = None):
    try:
        state["active_builds"] += 1
        ghost_dna = None
        if ghost_blueprint_path and os.path.exists(ghost_blueprint_path):
            with open(ghost_blueprint_path, "r") as f:
                ghost_dna = json.load(f)

        await factory.main_flow(vibe, ghost_dna=ghost_dna)
        state["last_verdict"] = "Build Successful"
    except Exception as e:
        logger.error(f"Factory execution failed: {str(e)}")
        state["last_verdict"] = f"Failed: {str(e)}"
    finally:
        state["active_builds"] -= 1


@app.get("/api/v1/health")
async def health_v1():
    """Standardized health check for fleet discovery."""
    return {"status": "ok", "server": "dark-app-factory-sota", "version": "2026.2.17"}


@app.post("/api/v1/fleet/launch")
@app.post("/api/fleet/launch")
async def fleet_launch(request: FleetLaunchRequest):
    """Launch another MCP app via its start.ps1 script."""
    path = Path(request.repo_path)
    if not path.exists():
        raise HTTPException(
            status_code=404, detail=f"Path {request.repo_path} does not exist"
        )

    # Security check: Ensure path is within D:/Dev/repos
    # Normalizing paths for reliable comparison
    try:
        allowed_base = Path("D:/Dev/repos").resolve()
        target_path = path.resolve()
        target_path.relative_to(allowed_base)
    except ValueError:
        raise HTTPException(status_code=403, detail="Access denied")

    # Look for start.ps1 in web_sota or web
    start_script = path / "web_sota" / "start.ps1"
    if not start_script.exists():
        start_script = path / "web" / "start.ps1"
        if not start_script.exists():
            # Try root start.ps1 as last resort
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
        return {"success": True, "message": f"Launched {path.name}"}
    except Exception as e:
        logger.error(f"Launch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/launch")
@app.post("/api/build")
async def launch(req: BuildRequest, background_tasks: BackgroundTasks):
    if state["active_builds"] > 0:
        raise HTTPException(status_code=429, detail="A build is already in progress.")
    background_tasks.add_task(
        launch_factory, req.vibe_content, req.ghost_blueprint_path
    )
    return {"success": True, "message": "Factory launched in background"}


# Mount static files for the frontend
UI_DIR = os.path.join(os.path.dirname(__file__))
if os.path.exists(os.path.join(UI_DIR, "index.html")):
    app.mount("/", StaticFiles(directory=UI_DIR, html=True), name="static")

if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", "10738"))
    uvicorn.run(app, host="0.0.0.0", port=port)
