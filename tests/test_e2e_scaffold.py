import pytest
import os
import logging
from factory import main_flow
from tests.utils.model_discovery import get_best_model

# Setup logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("dark_factory_e2e")

# Always resolve relative to this file, not the cwd pytest was invoked from
E2E_CASES_DIR = os.path.join(os.path.dirname(__file__), "data", "e2e_cases")


@pytest.mark.asyncio
@pytest.mark.parametrize("level, case_name", [
    (1, "simple"),
    (2, "crud"),
    (3, "complex_dtu"),
])
async def test_factory_e2e_pipeline(level, case_name, tmp_path):
    """
    Parametrised E2E test for Dark App Factory levels 1-3.

    Each test run gets its own tmp_path from pytest, so:
    - specs/, scenarios/, feedback.md, critique.md land in tmp_path/work/
    - generated app lands in tmp_path/output_levelN_casename/
    - the repo root is never touched by test runs
    """
    logger.info("--- STARTING E2E TEST: Level %d (%s) ---", level, case_name)

    # 1. Discover real models from Ollama
    foreman_model = get_best_model(
        provider="ollama", preferred_keywords=["llama3", "mistral"]
    )
    worker_model = get_best_model(
        provider="ollama", preferred_keywords=["coder", "qwen2.5"]
    )
    logger.info("Using models: Foreman=%s, Worker=%s", foreman_model, worker_model)

    # 2. Setup paths — all absolute so chdir in main_flow doesn't break them
    level_dir = os.path.join(E2E_CASES_DIR, f"level{level}")
    vibe_path = os.path.abspath(os.path.join(level_dir, "vibe.md"))
    assert os.path.exists(vibe_path), f"Vibe not found at {vibe_path}"

    # work_dir: isolated scratch space for specs/, scenarios/, feedback.md, critique.md
    # output_dir: where the generated app lands — also inside tmp_path, never repo root
    work_dir = str(tmp_path / "work")
    output_dir = str(tmp_path / f"output_level{level}_{case_name}")

    # 3. Run the factory
    # scenarios_path=None -> factory generates its own scenarios from the vibe.
    # The test's scenarios.md (if it exists) is only for post-build manual inspection.
    success = await main_flow(
        vibe_path=vibe_path,
        output_dir=output_dir,
        scenarios_path=None,
        foreman_model=foreman_model,
        worker_model=worker_model,
        work_dir=work_dir,
    )

    # 4. Assertions
    assert success is True, f"Factory main_flow failed for Level {level}"
    assert os.path.exists(output_dir), "Output directory was not created"

    demos_dir = os.path.join(output_dir, "demos")
    assert os.path.exists(demos_dir), "Showboat demos directory not created"

    www_index = os.path.join(output_dir, "www", "index.html")
    assert os.path.exists(www_index), "Landing page (www/index.html) not created"

    manifest_json = os.path.join(output_dir, "www", "manifest.json")
    assert os.path.exists(manifest_json), "PWA manifest.json not created"

    logger.info("--- COMPLETED E2E TEST: Level %d (SUCCESS) ---", level)
