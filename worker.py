# ruff: noqa: E402
import os
import argparse
import sys
import asyncio
import re

# Normalize import paths: ensure project root is on sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
if os.path.join(BASE_DIR, "src") not in sys.path:
    sys.path.insert(1, os.path.join(BASE_DIR, "src"))

from src.utils.logger import logger
from src.llm_client import LLMClient
from src.utils.git_manager import GitManager
from src.utils.progress import progress
from src.utils.stack_profile import (
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
    total_files = len(owned_files)
    for idx, file_path in enumerate(owned_files):
        logger.info(f"{specialist.name} working on: {file_path}")
        # Sub-status update without changing overall percentage
        current_state = progress.get_state()
        progress.update(
            current_state["percentage"],
            f"{specialist.name}: {file_path} ({idx + 1}/{total_files})...",
        )
        progress.add_file(file_path)

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
            # Normalize path: strip leading slashes to prevent absolute path resolution on Windows
            relative_path = file_path.lstrip("/\\")
            full_path = os.path.join(output_dir, relative_path)
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


async def run_factory(
    specs_path: str = "specs/specs.md",
    output_dir: str = "output",
    worker: LLMClient = None,
):
    logger.info(f"Factory Floor Initialized (Target: {output_dir})")
    specs = read_file(specs_path)
    if not specs:
        return

    # Extract stack profile from specs (embedded by Foreman)
    stack_profile = extract_from_specs(specs)
    stack_desc = describe_stack(stack_profile)
    logger.info("Stack: %s", stack_desc)

    if not worker:
        worker = LLMClient(role="worker")

    # 0b. Block installation — match and install blocks from specs keywords
    try:
        from blocks.loader import match_blocks, install_block, merge_deps

        matched = match_blocks(specs)
        if matched:
            logger.info("Matched %d block(s): %s", len(matched), [m["name"] for m in matched])
            progress.update(23, f"Installing blocks: {', '.join(m['name'] for m in matched)}")
            os.makedirs(output_dir, exist_ok=True)
            results = []
            for m in matched:
                result = install_block(m["name"], output_dir)
                if result:
                    results.append(result)
                    logger.info("Installed block: %s", m["name"])
            if results:
                merge_deps(output_dir, results)
    except ImportError:
        pass  # blocks/ not available
    except Exception as e:
        logger.warning("Block installation failed (non-fatal): %s", e)

    # 1. Planning -- stack-aware file list
    progress.update(25, "Architect: Planning file structure...")
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
        # Strip ASCII tree-drawing prefixes (│ ├── └── ─) that LLMs emit
        # instead of plain file lists. Extract the last token — the actual path.
        if any(c in line for c in ("│", "├", "└", "─")):
            tokens = line.split()
            line = tokens[-1] if tokens else ""
        line = line.strip()
        if not line:
            continue
        # Safety: reject path traversal, absolute paths, Windows drive letters
        if ".." in line:
            continue
        if line.startswith(("/", "\\")) or (len(line) > 1 and line[1] == ":"):
            continue
        if ("." in line or "/" in line) and not line.endswith(("/", "\\")):
            file_paths.append(line)

    if not file_paths:
        logger.error("Architect failed to plan files.")
        return

    # Basic cleaning: only strip top-level frontend/ or backend/ prefixes,
    # not occurrences mid-path (e.g. src/services/backend/foo.js must stay intact)
    def _strip_top_prefix(p: str) -> str:
        for prefix in ("frontend/", "backend/"):
            if p.startswith(prefix):
                return p[len(prefix):]
        return p

    file_paths = [_strip_top_prefix(f) for f in file_paths]

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
        Hawks,
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
        "Hawks": Hawks(),
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
        "file_paths": file_paths,  # planned file list — used by Sculptor for grounded App.tsx
        "outputs": {},
        "worker": worker,
        "stack_profile": stack_profile,
    }
    generated_files = set()

    # 3. Dependency-Aware Parallel Execution
    progress.update(30, "Architect: Resolving specialist dependencies...")
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
    num_levels = len(levels)
    level_inc = (70 - 30) / max(1, num_levels)

    for i, level_names in enumerate(levels):
        current_pct = 30 + int(i * level_inc)
        step_name = f"Level {i + 1}: {', '.join(level_names)}"
        progress.add_step(step_name, f"Level {i + 1} specialists ({len(level_names)} workers)")
        progress.update(
            current_pct, f"Specialists: Executing Level {i + 1}/{num_levels}..."
        )

        # Mark each specialist as running
        for name in level_names:
            progress.specialist_status(name, "running")

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
            has_files = bool(result)
            progress.specialist_status(name, "done" if has_files else "skipped")

        progress.complete_step(step_name)

    # 5a. App.tsx Reconciliation Pass (React only)
    # After all specialists have run, read the ACTUAL generated file tree and
    # regenerate App.tsx so its imports and routes match reality exactly.
    # This eliminates the #1 cause of Vite startup crashes.
    if is_react_frontend(stack_profile):
        app_tsx_path = os.path.join(output_dir, "src", "App.tsx")
        if os.path.exists(app_tsx_path):
            progress.update(72, "Reconciler: Aligning App.tsx with generated file tree...")
            logger.info("Reconciler: Rebuilding App.tsx from actual file tree...")

            # Collect all generated TSX pages and components
            pages_dir = os.path.join(output_dir, "src", "pages")
            components_dir = os.path.join(output_dir, "src", "components")
            actual_pages: list[str] = []
            actual_components: list[str] = []

            if os.path.isdir(pages_dir):
                for fname in sorted(os.listdir(pages_dir)):
                    if fname.endswith(".tsx"):
                        actual_pages.append(fname[:-4])  # strip .tsx

            if os.path.isdir(components_dir):
                for fname in sorted(os.listdir(components_dir)):
                    if fname.endswith(".tsx"):
                        actual_components.append(fname[:-4])

            # Build reconciliation prompt grounded in the real file tree
            pages_list = "\n".join(
                f"  - {p}  (route: /{p.lower().replace('page', '').replace('view', '')})"
                for p in actual_pages
            ) or "  (none generated)"
            components_list = "\n".join(f"  - {c}" for c in actual_components) or "  (none generated)"

            reconcile_prompt = f"""
Regenerate src/App.tsx for a React + Vite + react-router-dom application.

CRITICAL: Use ONLY the files that ACTUALLY EXIST listed below. Do NOT invent any component names.

EXISTING PAGES (in src/pages/):
{pages_list}

EXISTING COMPONENTS (in src/components/):
{components_list}

RULES:
- Import ONLY components from the EXISTING lists above. Never import a component not listed.
- import {{ AnimatePresence, motion }} from 'framer-motion'  (named imports, never default)
- Use <AnimatePresence mode="wait"> for page transitions (NOT exitBeforeEnter, deprecated)
- Add a Navbar if Navbar exists in EXISTING COMPONENTS, otherwise skip it
- Route each page: <Route path="/pagename" element={{<PageName />}} />
- Default route "/" maps to the first page in the list
- Dark glassmorphism layout: bg-gray-950 text-white min-h-screen
- Include a functional Navbar inline in this file if no Navbar component exists
- Export default App

Output ONLY the complete src/App.tsx file. No markdown fences.
"""
            sculptor = council["Sculptor"]
            raw_reconciled = await sculptor.generate(
                "src/App.tsx", reconcile_prompt, shared_context, worker
            )
            reconciled_code = clean_code(raw_reconciled)

            # Validate: no default framer-motion import, has export default
            is_valid, val_err = sculptor.validate("src/App.tsx", reconciled_code, specs)
            if not is_valid:
                logger.warning(f"Reconciler validation failed ({val_err}), retrying once...")
                reconcile_prompt += f"\n\n[FIX REQUIRED]: {val_err}"
                raw_reconciled = await sculptor.generate(
                    "src/App.tsx", reconcile_prompt, shared_context, worker
                )
                reconciled_code = clean_code(raw_reconciled)

            with open(app_tsx_path, "w", encoding="utf-8") as f:
                f.write(reconciled_code)
            generated_files.add("src/App.tsx")
            shared_context.setdefault("Sculptor", {})["src/App.tsx"] = reconciled_code
            logger.success(
                f"Reconciler: App.tsx rebuilt ({len(actual_pages)} pages, {len(actual_components)} components)"
            )

    # 5b. Deep-Crawl (Bounded) -- scan App.tsx AFTER reconciliation
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
        "StrictMode",
        "Fragment",
        "Provider",
        "motion",
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
                # Pattern 1: explicit import paths  from './pages/Foo' or from './components/Bar'
                explicit_imports = re.findall(
                    r"from\s+['\"](?:\./|\.\./)?((?:pages|components)/[^'\"]+)['\"]",
                    content,
                )
                # Pattern 1b: named imports from bare package specifiers
                # e.g. import { FaTooth } from "react-icons/fa"
                # Also catches default+namespace: import Motion from "framer-motion"
                named_imports = re.findall(
                    r"import\s+\{([^}]+)\}\s+from\s+['\"](?!\.)[^'\"]+['\"]",
                    content,
                )
                default_imports = re.findall(
                    r"import\s+(\w+)\s+from\s+['\"](?!\.)[^'\"]+['\"]",
                    content,
                )
                # Collect all identifiers from named imports into a set
                bare_package_identifiers: set[str] = set()
                for block in named_imports:
                    for ident in block.split(","):
                        bare = ident.strip().split(" as ")[0].strip()
                        if bare:
                            bare_package_identifiers.add(bare)
                for ident in default_imports:
                    bare_package_identifiers.add(ident)
                # Pattern 2: JSX element usage  <FooBar />  or  <FooBar>
                found_elements = re.findall(r"<([A-Z][a-zA-Z0-9]*)[\s/>]", content)

                # Build a map: component_name -> already-known folder from explicit imports
                known_folder: dict[str, str] = {}
                for imp_path in explicit_imports:
                    parts = imp_path.split("/")
                    if len(parts) >= 2:
                        folder = parts[0]  # "pages" or "components"
                        name = parts[-1].replace(".tsx", "").replace(".ts", "")
                        known_folder[name] = folder

                # Process explicit imports first (highest confidence)
                for imp_path in explicit_imports:
                    parts = imp_path.split("/")
                    if len(parts) < 2:
                        continue
                    folder = parts[0]
                    name = parts[-1].replace(".tsx", "").replace(".ts", "")
                    target_path = f"src/{folder}/{name}.tsx"
                    if target_path not in generated_files and name not in tsx_blacklist:
                        logger.info(f"Deep-Crawl discovered (explicit import): {target_path}")
                        raw_code = await sculptor.generate(
                            target_path, specs, shared_context, worker
                        )
                        code = clean_code(raw_code)
                        full_save_path = os.path.join(output_dir, target_path)
                        os.makedirs(os.path.dirname(full_save_path), exist_ok=True)
                        with open(full_save_path, "w", encoding="utf-8") as f:
                            f.write(code)
                        generated_files.add(target_path)
                        next_crawl_batch.append(target_path)

                # Process JSX elements not covered by explicit imports
                for item in found_elements:
                    if item in tsx_blacklist:
                        continue
                    # Skip if already generated via explicit import
                    if item in known_folder:
                        continue
                    # Skip if the identifier comes from a bare package import
                    # (catches icon libraries, UI kits, etc.)
                    if item in bare_package_identifiers:
                        continue
                    # Heuristic: if a matching file already exists in pages/ or components/, skip
                    already_pages = f"src/pages/{item}.tsx" in generated_files
                    already_comp = f"src/components/{item}.tsx" in generated_files
                    if already_pages or already_comp:
                        continue
                    # Folder heuristic: check if a file was explicitly imported with this name
                    # from a known folder; otherwise default to components/
                    folder = "pages" if (
                        item.endswith("Page") or item.endswith("View") or item.endswith("Screen")
                    ) else "components"
                    target_path = f"src/{folder}/{item}.tsx"
                    if target_path not in generated_files:
                        logger.info(f"Deep-Crawl discovered (jsx element): {target_path}")
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
                        "bcryptjs",
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
                        target_path = target_path.lstrip("/\\")
                        full_save_path = os.path.join(output_dir, target_path)
                        os.makedirs(os.path.dirname(full_save_path), exist_ok=True)
                        with open(full_save_path, "w", encoding="utf-8") as f:
                            f.write(code)
                        logger.debug(f"   -> Saved to {full_save_path}")
                        generated_files.add(target_path)
                        next_crawl_batch.append(target_path)

        progress.update(
            75 + int(current_depth * (8 / max_crawl_depth)),
            f"Deep-Crawl: Scanning depth {current_depth}...",
        )
        pages_to_scan = next_crawl_batch
        if not pages_to_scan:
            break

    # 6. Generate manifest.json
    import json

    manifest = {
        "project_name": stack_profile.get("project_name", "Dark App"),
        "stack": stack_desc,
        "entry_points": {
            "backend": "main.py"
            if is_python_backend(stack_profile)
            else ("server.js" if is_node_backend(stack_profile) else None),
            "frontend": "index.html" if has_frontend(stack_profile) else None,
            "react_entry": "src/App.tsx" if is_react_frontend(stack_profile) else None,
        },
        "files": list(generated_files),
    }
    manifest_path = os.path.join(output_dir, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=4)
    logger.success(f"Manifest generated: {manifest_path}")

    # 7. Git Initialization (SOTA Surge: Automated Versioning)
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
