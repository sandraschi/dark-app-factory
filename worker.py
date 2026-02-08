import os
import argparse
import sys
import asyncio
import re
from utils.logger import logger

# Add src to path if needed or structure correctly
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))
from llm_client import LLMClient
from utils.git_manager import GitManager
from utils.stack_profile import (
    extract_from_specs,
    describe_stack,
    is_python_backend,
    is_node_backend,
    has_frontend,
    is_react_frontend,
)


def clean_code(code: str) -> str:
    """Strips markdown code fences from LLM output."""
    # Regex to match ```language ... ``` blocks
    match = re.search(r"^```(?:\w+)?\s*\n(.*?)\n```", code, re.DOTALL | re.MULTILINE)
    if match:
        return match.group(1).strip()
    return code.strip()


def read_file(path: str) -> str:
    if not os.path.exists(path):
        logger.error(f"File not found at {path}")
        return ""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


async def generate_specialist_files(
    specialist, file_paths, specs, shared_context, worker, output_dir, generated_files
):
    """Generates files for a single specialist, potentially in parallel.

    Includes runt detection (byte count) and specialist-specific validation
    hooks. Failed validation triggers retry with error context injected.
    """
    if specialist.name == "Generalist":
        owned_files = [f for f in file_paths if f not in generated_files]
    else:
        owned_files = [
            f
            for f in file_paths
            if specialist.can_handle(f) and f not in generated_files
        ]

    if not owned_files:
        return {}

    logger.info(
        f"Specialist Floor: {specialist.name} taking the floor ({len(owned_files)} files)..."
    )

    specialist_results = {}
    for file_path in owned_files:
        logger.info(f"{specialist.name} working on: {file_path}")
        attempts, max_attempts, code = 0, 3, ""
        current_specs = specs

        while attempts < max_attempts:
            raw_code = await specialist.generate(
                file_path, current_specs, shared_context, worker
            )
            code = clean_code(raw_code)

            # --- Gate 1: Runt detection (byte count) ---
            threshold = _get_runt_threshold(file_path)
            is_runt_candidate = (
                file_path.endswith(".tsx")
                or file_path.endswith(".py")
                or file_path.endswith(".js")
                or file_path.endswith("README.md")
            )

            if (
                is_runt_candidate
                and len(code) < threshold
                and attempts < max_attempts - 1
            ):
                logger.warning(
                    f"Runt detected ({len(code)} bytes) for {file_path}. Retrying..."
                )
                current_specs += f"\n\n[RETRY WARNING]: The previous attempt for {file_path} was too short ({len(code)} bytes, need {threshold}+). DO NOT USE PLACEHOLDERS."
                attempts += 1
                continue

            # --- Gate 2: Specialist validation hook ---
            is_valid, validation_error = specialist.validate(file_path, code, specs)
            if not is_valid and attempts < max_attempts - 1:
                logger.warning(
                    f"Validation failed for {file_path}: {validation_error}. Retrying..."
                )
                current_specs += f"\n\n[VALIDATION ERROR]: {validation_error}. Fix this in your next attempt."
                attempts += 1
                continue

            # Passed both gates (or last attempt)
            generated_files.add(file_path)
            specialist_results[file_path] = code
            full_path = os.path.join(output_dir, file_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(code)
            break

    return specialist_results


def _get_runt_threshold(file_path: str) -> int:
    """Return minimum acceptable byte count for a generated file."""
    if file_path.endswith("README.md"):
        return 2500
    # Backend entry points (any stack)
    if file_path in ("server.js", "main.py", "app.py"):
        return 3000
    # Frontend components
    if file_path.endswith(".tsx") or file_path.endswith(".jsx"):
        return 500
    # Python modules
    if file_path.endswith(".py"):
        return 400
    return 500


async def run_factory(specs_path: str = "specs/specs.md", output_dir: str = "output"):
    logger.info(f"Factory Floor Initialized (Target: {output_dir})")
    specs = read_file(specs_path)
    if not specs:
        return

    # Extract stack profile from specs (embedded by Foreman)
    stack_profile = extract_from_specs(specs)
    stack_desc = describe_stack(stack_profile)
    logger.info("Stack: %s", stack_desc)

    worker = LLMClient(role="worker")

    # 1. Planning -- stack-aware file list
    file_list_prompt = (
        f"Read these specs and list ALL files needed for a STUNNING, SOTA, HIGH-FIDELITY implementation.\n"
        f"Tech stack: {stack_desc}\n"
        f"Output a FLAT structure (no nested frontend/backend folders). One file path per line.\n"
        f"Specs: {specs[:3000]}"
    )
    logger.info("Planning file structure...")
    files_response = await worker.generate(
        file_list_prompt,
        system_prompt="You are a senior architect. Output only file paths, one per line.",
    )

    file_paths = []
    for line in files_response.strip().split("\n"):
        line = line.strip().strip("-").strip("*").strip("`").strip()
        if "." in line or "/" in line:
            file_paths.append(line)

    if not file_paths:
        logger.error("Architect failed to plan files.")
        return

    # Basic cleaning
    file_paths = [
        f.replace("frontend/", "").replace("backend/", "") for f in file_paths
    ]

    # Stack-aware mandatory files
    mandatory = ["skills/expertise.md", "README.md"]

    if is_python_backend(stack_profile):
        mandatory.extend(["requirements.txt", "main.py"])
    if is_node_backend(stack_profile):
        mandatory.append("package.json")
    if is_react_frontend(stack_profile):
        mandatory.extend(["index.html", "src/main.tsx", "src/App.tsx"])
    if has_frontend(stack_profile) and is_node_backend(stack_profile):
        mandatory.append("vite.config.ts")

    for m in mandatory:
        if m not in file_paths:
            file_paths.append(m)

    # Deduplicate preserving order
    file_paths = list(dict.fromkeys(file_paths))

    logger.info(f"LLM-planned files: {len(file_paths)}")

    # 2. Assign Specialists
    from src.specialists.council import (
        Plumber,
        Sculptor,
        Librarian,
        Registrar,
        Generalist,
        Maestro,
        WebFinder,
        Archivist,
        Raggy,
        Nervos,
        Auditor,
        Professor,
        Picasso,
        Shakespeare,
        Propagandist,
        Houdini,
        Morpheus,
        Tesla,
        Amodei,
    )

    council = {
        "Plumber": Plumber(),
        "Sculptor": Sculptor(),
        "Librarian": Librarian(),
        "Registrar": Registrar(),
        "Maestro": Maestro(),
        "WebFinder": WebFinder(),
        "Archivist": Archivist(),
        "Raggy": Raggy(),
        "Nervos": Nervos(),
        "Auditor": Auditor(),
        "Professor": Professor(),
        "Picasso": Picasso(),
        "Shakespeare": Shakespeare(),
        "Propagandist": Propagandist(),
        "Houdini": Houdini(),
        "Morpheus": Morpheus(),
        "Tesla": Tesla(),
        "Amodei": Amodei(),
        "Generalist": Generalist(),
    }

    # 2b. Self-Declaration: let specialists inject files they need
    declared_count = 0
    for name, spec in council.items():
        declared = spec.declare_files(specs, stack_profile)
        for df in declared:
            if df not in file_paths:
                file_paths.append(df)
                declared_count += 1
    if declared_count:
        logger.info(f"Specialists declared {declared_count} additional files.")
    file_paths = list(dict.fromkeys(file_paths))

    logger.success(f"Total files to generate: {len(file_paths)}")

    shared_context = {
        "file_paths": file_paths,
        "outputs": {},
        "worker": worker,
        "stack_profile": stack_profile,
    }
    generated_files = set()

    # 3. Dependency-Aware Parallel Execution
    levels = []
    remaining = set(council.keys())
    completed = set()

    def _resolve_req_name(req) -> str:
        """Extract dependency name from string or dict."""
        if isinstance(req, str):
            return req
        if isinstance(req, dict):
            return req.get("name", "")
        return str(req)

    while remaining:
        level = []
        for name in list(remaining):
            spec = council[name]
            if all(_resolve_req_name(req) in completed for req in spec.requires):
                level.append(name)

        if not level:
            logger.error("Cyclic dependencies or missing requirements!")
            break

        levels.append(level)
        for name in level:
            remaining.remove(name)
            completed.add(name)

    # 4. Generate in Parallel Levels
    for level_names in levels:
        tasks = []
        for name in level_names:
            tasks.append(
                generate_specialist_files(
                    council[name],
                    file_paths,
                    specs,
                    shared_context,
                    worker,
                    output_dir,
                    generated_files,
                )
            )

        results = await asyncio.gather(*tasks)
        for name, result in zip(level_names, results):
            shared_context[name] = result
            shared_context["outputs"].update(result)

    # 5. Deep-Crawl (Bounded) -- stack-aware
    logger.info("Deep-Crawl: Scanning for missing components...")
    max_crawl_depth, current_depth = 3, 0
    scanned_pages = set()
    sculptor = council["Sculptor"]
    plumber = council["Plumber"]

    # Determine entry points based on stack
    pages_to_scan = []
    if is_react_frontend(stack_profile):
        pages_to_scan.append("src/App.tsx")
    if is_python_backend(stack_profile):
        pages_to_scan.append("main.py")
    elif is_node_backend(stack_profile):
        pages_to_scan.append("server.js")

    # React blacklist (common framework components not needing generation)
    tsx_blacklist = {
        "Navbar",
        "Router",
        "Route",
        "Routes",
        "AnimatePresence",
        "BrowserRouter",
        "Link",
        "Navigate",
        "Outlet",
        "Suspense",
    }

    # Python stdlib modules (never generate these)
    py_stdlib = {
        "os",
        "sys",
        "json",
        "re",
        "logging",
        "typing",
        "pathlib",
        "datetime",
        "asyncio",
        "hashlib",
        "uuid",
        "collections",
        "functools",
        "itertools",
        "abc",
        "dataclasses",
        "enum",
    }

    while pages_to_scan and current_depth < max_crawl_depth:
        current_depth += 1
        next_crawl_batch = []

        logger.debug(
            f"Crawl Depth {current_depth}/{max_crawl_depth}: Scanning {len(pages_to_scan)} files..."
        )

        for scan_path in pages_to_scan:
            if scan_path in scanned_pages:
                continue
            scanned_pages.add(scan_path)

            full_scan_path = os.path.join(output_dir, scan_path)
            if not os.path.exists(full_scan_path):
                continue

            with open(full_scan_path, "r", encoding="utf-8") as f:
                content = f.read()

            # --- TSX/JSX import scanning ---
            if scan_path.endswith((".tsx", ".jsx", ".ts", ".js")):
                found_refs = re.findall(
                    r"from\s+['\"](?:\./)?(?:pages|components)/([^'\"]+)['\"]", content
                )
                found_elements = re.findall(r"<([A-Z][a-zA-Z0-9]*)\s*/?>", content)
                all_detected = list(set(found_refs + found_elements))

                for item in all_detected:
                    if item in tsx_blacklist:
                        continue
                    for folder in ["pages", "components"]:
                        target_path = f"src/{folder}/{item}.tsx"
                        if target_path not in generated_files:
                            logger.info(f"Deep-Crawl discovered (tsx): {target_path}")
                            raw_code = await sculptor.generate(
                                target_path, specs, shared_context, worker
                            )
                            code = clean_code(raw_code)
                            full_save_path = os.path.join(output_dir, target_path)
                            os.makedirs(os.path.dirname(full_save_path), exist_ok=True)
                            with open(full_save_path, "w", encoding="utf-8") as f:
                                f.write(code)
                            logger.debug(f"   -> Saved to {full_save_path}")
                            generated_files.add(target_path)
                            next_crawl_batch.append(target_path)

            # --- Python import scanning ---
            elif scan_path.endswith(".py"):
                # from routers.patients import router
                py_from_imports = re.findall(r"from\s+([\w.]+)\s+import", content)
                # import models.patient
                py_direct_imports = re.findall(
                    r"^import\s+([\w.]+)", content, re.MULTILINE
                )
                all_py = list(set(py_from_imports + py_direct_imports))

                for mod in all_py:
                    top_module = mod.split(".")[0]
                    if top_module in py_stdlib:
                        continue
                    # Skip third-party packages (fastapi, pydantic, sqlalchemy, etc.)
                    if top_module in {
                        "fastapi",
                        "pydantic",
                        "sqlalchemy",
                        "uvicorn",
                        "flask",
                        "django",
                        "starlette",
                        "httpx",
                        "requests",
                        "dotenv",
                        "bcrypt",
                        "jose",
                        "passlib",
                        "alembic",
                    }:
                        continue

                    # Convert module path to file path
                    target_path = mod.replace(".", "/") + ".py"
                    if target_path not in generated_files:
                        logger.info(f"Deep-Crawl discovered (py): {target_path}")
                        raw_code = await plumber.generate(
                            target_path, specs, shared_context, worker
                        )
                        code = clean_code(raw_code)
                        full_save_path = os.path.join(output_dir, target_path)
                        os.makedirs(os.path.dirname(full_save_path), exist_ok=True)
                        with open(full_save_path, "w", encoding="utf-8") as f:
                            f.write(code)
                        logger.debug(f"   -> Saved to {full_save_path}")
                        generated_files.add(target_path)
                        next_crawl_batch.append(target_path)

        pages_to_scan = next_crawl_batch
        if not pages_to_scan:
            break

    # 6. Git Initialization (SOTA Surge: Automated Versioning)
    git = GitManager(output_dir)
    git.initialize()


def main():
    parser = argparse.ArgumentParser(description="Dark App Factory Worker")
    subparsers = parser.add_subparsers(dest="command")

    build_parser = subparsers.add_parser("build", help="Build app from specs")
    build_parser.add_argument(
        "--specs", default="specs/specs.md", help="Path to specs file"
    )
    build_parser.add_argument(
        "--output", default="output", help="Target output directory"
    )

    args = parser.parse_args()

    if args.command == "build":
        asyncio.run(run_factory(args.specs, args.output))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
