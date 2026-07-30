"""Block loader — detect pre-generation, integrate post-generation."""

from __future__ import annotations

import json
import logging
import os
import shutil

logger = logging.getLogger("dark_factory")

BLOCKS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "blocks")


def discover_blocks() -> dict[str, dict]:
    """Scan blocks/ directory and return all registered block manifests keyed by name."""
    blocks = {}
    if not os.path.isdir(BLOCKS_DIR):
        return blocks
    for name in os.listdir(BLOCKS_DIR):
        manifest_path = os.path.join(BLOCKS_DIR, name, "block.json")
        if os.path.isfile(manifest_path):
            try:
                with open(manifest_path, encoding="utf-8") as f:
                    manifest = json.load(f)
                manifest["_path"] = os.path.join(BLOCKS_DIR, name)
                blocks[name] = manifest
            except (json.JSONDecodeError, OSError):
                continue
    return blocks


import re


def match_blocks(specs: str, max_blocks: int = 6) -> list[dict]:
    """Return blocks that match keywords found in specs text.

    Uses word-boundary matching (\\b) to prevent over-matching
    (e.g. ``pay`` does not match ``payload``). Caps at ``max_blocks``.
    """
    blocks = discover_blocks()
    specs_lower = specs.lower()
    matched = []
    for name, manifest in blocks.items():
        if manifest.get("status") == "stub":
            logger.info("Block %s is stub — skipping", name)
            continue
        triggers = [t.lower() for t in manifest.get("triggers", [])]
        for t in triggers:
            pattern = re.compile(r"\b" + re.escape(t) + r"\b")
            if pattern.search(specs_lower):
                matched.append({"name": name, "manifest": manifest})
                break
        if len(matched) >= max_blocks:
            overflow = [n for n, _ in [(m["name"], m) for m in list(blocks.values()) if m.get("name") != name]]
            if overflow:
                logger.warning("Block match cap reached (%d). Discarding: %s", max_blocks, overflow)
            break
    return matched


def build_block_context(matched: list[dict]) -> str:
    """Build a prompt context string describing installed blocks."""
    parts = []
    for m in matched:
        manifest = m["manifest"]
        routes = manifest.get("backend_routes", [])
        pages = manifest.get("frontend_pages", [])
        specialists = manifest.get("specialists", {})
        imports = []
        for s_data in specialists.values():
            imports.extend(s_data.get("imports", []))
        name = manifest.get("name", m["name"])
        desc = manifest.get("description", "")
        ctx = f"- **{name}**: {desc}"
        if routes:
            ctx += f"\n  Routes: {', '.join(routes)}"
        if pages:
            ctx += f"\n  Pages: {', '.join(pages)}"
        if imports:
            ctx += f"\n  Components provided: {', '.join(imports)}"
        parts.append(ctx)
    return "\n\n".join(parts)


def integrate_blocks(output_dir: str, matched: list[dict]) -> list[dict]:
    """Post-generation integration: copy files, mount routers, merge deps.

    Runs AFTER specialist generation so target files (main.py, requirements.txt) exist.
    """
    results = []
    os.makedirs(output_dir, exist_ok=True)

    for m in matched:
        result = _install_block_files(m["name"], output_dir)
        if result:
            results.append(result)

    if results:
        _merge_deps(output_dir, results)
        _write_router_init(output_dir, results)
        _patch_main_py(output_dir, results)

    return results


def _install_block_files(block_name: str, output_dir: str) -> dict | None:
    """Copy block source files into output_dir."""
    blocks = discover_blocks()
    manifest = blocks.get(block_name)
    if not manifest:
        return None

    src = manifest["_path"]

    # Copy backend files
    backend_src = os.path.join(src, "backend")
    backend_dst = os.path.join(output_dir, "backend", "blocks", block_name)
    if os.path.isdir(backend_src):
        shutil.copytree(backend_src, backend_dst, dirs_exist_ok=True)

    # Copy frontend files
    frontend_src = os.path.join(src, "frontend")
    frontend_dst = os.path.join(output_dir, "src", "components", "blocks", block_name)
    if os.path.isdir(frontend_src):
        shutil.copytree(frontend_src, frontend_dst, dirs_exist_ok=True)

    deps = manifest.get("dependencies", {})
    env_vars = manifest.get("env_vars", {})
    requires = manifest.get("requires_blocks", [])

    return {
        "name": block_name,
        "python_deps": deps.get("python", []),
        "node_deps": deps.get("node", {}),
        "env_vars": list(env_vars.keys()),
        "requires": requires,
    }


def _merge_deps(output_dir: str, results: list[dict]):
    """Add block dependencies to requirements.txt and package.json."""
    all_py = []
    all_node: dict[str, str] = {}

    for r in results:
        all_py.extend(r["python_deps"])
        for name, version in r.get("node_deps", {}).items():
            if name not in all_node:
                all_node[name] = version

    # Python — create requirements.txt if blocks have deps and file doesn't exist
    if all_py:
        req_path = os.path.join(output_dir, "requirements.txt")
        existing = ""
        if os.path.exists(req_path):
            with open(req_path, encoding="utf-8") as f:
                existing = f.read()
        missing = [d for d in all_py if d not in existing]
        if missing:
            with open(req_path, "a", encoding="utf-8") as f:
                f.write("\n" + "\n".join(missing) + "\n")
            logger.info("Added %d Python dep(s) to requirements.txt", len(missing))

    # Node — merge into package.json if exists
    if all_node:
        pkg_path = os.path.join(output_dir, "package.json")
        if os.path.exists(pkg_path):
            try:
                with open(pkg_path, encoding="utf-8") as f:
                    pkg = json.load(f)
                deps_dict = pkg.setdefault("dependencies", {})
                for name, version in all_node.items():
                    if name not in deps_dict:
                        deps_dict[name] = version
                with open(pkg_path, "w", encoding="utf-8") as f:
                    json.dump(pkg, f, indent=2)
                logger.info("Merged %d Node dep(s) into package.json", len(all_node))
            except (json.JSONDecodeError, OSError) as e:
                logger.warning("Could not merge node deps: %s", e)
        else:
            logger.warning(
                "Blocks require node deps (%s) but no package.json exists — skipping merge. "
                "Deps needed: %s",
                ", ".join(all_node.keys()),
                json.dumps(all_node),
            )


def _write_router_init(output_dir: str, results: list[dict]):
    """Write backend/blocks/__init__.py with all_routers list for deterministic mounting."""
    lines = [
        "# Auto-generated by dark-app-factory block loader.",
        "# Import all block routers for deterministic mounting.",
        "from __future__ import annotations",
        "",
    ]
    router_vars = []
    for r in results:
        name = r["name"]
        var = f"{name}_router"
        lines.append(f"from backend.blocks.{name}.routes import router as {var}")
        router_vars.append(var)

    lines.append("")
    lines.append("all_routers = [" + ", ".join(router_vars) + "]")
    lines.append("")

    init_dir = os.path.join(output_dir, "backend", "blocks")
    os.makedirs(init_dir, exist_ok=True)
    with open(os.path.join(init_dir, "__init__.py"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def _patch_main_py(output_dir: str, results: list[dict]):
    """Post-generation: add router mount loop to main.py if not already present."""
    main_py = os.path.join(output_dir, "main.py")
    if not os.path.exists(main_py):
        alt = os.path.join(output_dir, "app.py")
        if os.path.exists(alt):
            main_py = alt
        else:
            logger.warning("No main.py or app.py found — cannot mount block routers")
            return

    with open(main_py, encoding="utf-8") as f:
        content = f.read()

    if "all_routers" in content:
        return  # already mounted

    # Append import + mount loop
    patch = """
# Block router mounting (dark-app-factory)
from backend.blocks import all_routers
for _router in all_routers:
    app.include_router(_router)
"""
    with open(main_py, "a", encoding="utf-8") as f:
        f.write(patch)
    logger.info("Patched router mount into %s", os.path.basename(main_py))
