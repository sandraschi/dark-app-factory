"""Block loader — detect, install, and wire blocks into generated output."""

from __future__ import annotations

import json
import os
import shutil

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


def match_blocks(specs: str) -> list[dict]:
    """Return blocks that match keywords found in specs text."""
    blocks = discover_blocks()
    specs_lower = specs.lower()
    matched = []
    for name, manifest in blocks.items():
        triggers = [t.lower() for t in manifest.get("triggers", [])]
        if any(t in specs_lower for t in triggers):
            matched.append({"name": name, "manifest": manifest})
    return matched


def install_block(block_name: str, output_dir: str) -> dict | None:
    """Copy block files into output_dir and return install metadata."""
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

    # Append glue code
    glue_dir = os.path.join(src, "glue")
    if os.path.isdir(glue_dir):
        for glue_file in os.listdir(glue_dir):
            if not glue_file.endswith(".append"):
                continue
            # Determine target file
            target = os.path.join(output_dir, glue_file.replace(".append", ""))
            glue_path = os.path.join(glue_dir, glue_file)
            if os.path.isfile(glue_path) and os.path.isfile(target):
                with open(glue_path, encoding="utf-8") as f:
                    snippet = f.read().strip()
                with open(target, "a", encoding="utf-8") as f:
                    f.write("\n" + snippet + "\n")

    # Collect dependencies to merge
    deps = manifest.get("dependencies", {})
    env_vars = manifest.get("env_vars", {})

    return {
        "name": block_name,
        "python_deps": deps.get("python", []),
        "node_deps": deps.get("node", []),
        "env_vars": list(env_vars.keys()),
    }


def merge_deps(output_dir: str, install_results: list[dict]):
    """Add block dependencies to package.json / requirements.txt."""
    for result in install_results:
        # Python deps
        req_path = os.path.join(output_dir, "requirements.txt")
        if result["python_deps"] and os.path.exists(req_path):
            with open(req_path, "r+", encoding="utf-8") as f:
                existing = f.read()
                for dep in result["python_deps"]:
                    if dep not in existing:
                        f.write(f"\n{dep}")
        # Node deps
        pkg_path = os.path.join(output_dir, "package.json")
        if result["node_deps"] and os.path.exists(pkg_path):
            try:
                with open(pkg_path, encoding="utf-8") as f:
                    pkg = json.load(f)
                deps_dict = pkg.setdefault("dependencies", {})
                for dep in result["node_deps"]:
                    name = dep.split("@")[0] if dep.startswith("@") else dep.split(">=")[0].split("=")[0].split("^")[0]
                    version = dep[len(name):] if dep.startswith("@") else "latest"
                    if name not in deps_dict:
                        deps_dict[name] = version or "latest"
                with open(pkg_path, "w", encoding="utf-8") as f:
                    json.dump(pkg, f, indent=2)
            except (json.JSONDecodeError, OSError):
                pass
