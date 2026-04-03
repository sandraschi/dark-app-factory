"""Tests for run_manifest.py -- manifest loading and component detection."""

import json
import os

from run_manifest import RunManifest


class TestManifestToComponents:
    def test_python_backend_entry(self, tmp_output_dir):
        rm = RunManifest(tmp_output_dir)
        manifest = {
            "entry_points": {
                "backend": "main.py",
                "frontend": None,
                "react_entry": None,
            }
        }
        result = rm._manifest_to_components(manifest)
        assert len(result["components"]) == 1
        assert result["components"][0]["command"] == "python main.py"

    def test_node_backend_entry(self, tmp_output_dir):
        rm = RunManifest(tmp_output_dir)
        manifest = {
            "entry_points": {
                "backend": "server.js",
                "frontend": None,
                "react_entry": None,
            }
        }
        result = rm._manifest_to_components(manifest)
        assert result["components"][0]["command"] == "node server.js"

    def test_hybrid_stack(self, tmp_output_dir):
        rm = RunManifest(tmp_output_dir)
        manifest = {
            "entry_points": {
                "backend": "main.py",
                "frontend": "index.html",
                "react_entry": "src/App.tsx",
            }
        }
        result = rm._manifest_to_components(manifest)
        assert len(result["components"]) == 2
        names = {c["name"] for c in result["components"]}
        assert "backend" in names
        assert "frontend" in names

    def test_empty_entry_points(self, tmp_output_dir):
        rm = RunManifest(tmp_output_dir)
        manifest = {
            "entry_points": {"backend": None, "frontend": None, "react_entry": None}
        }
        result = rm._manifest_to_components(manifest)
        assert result is None or len(result.get("components", [])) == 0


class TestLoadManifest:
    def test_load_worker_manifest(self, tmp_output_dir):
        manifest_data = {
            "project_name": "TestApp",
            "stack": "Python + React",
            "entry_points": {
                "backend": "main.py",
                "frontend": "index.html",
                "react_entry": "src/App.tsx",
            },
            "files": ["main.py", "index.html", "src/App.tsx"],
        }
        manifest_path = os.path.join(tmp_output_dir, "manifest.json")
        with open(manifest_path, "w") as f:
            json.dump(manifest_data, f)

        rm = RunManifest(tmp_output_dir)
        loaded = rm.load_manifest()
        assert "components" in loaded
        assert len(loaded["components"]) >= 1

    def test_load_legacy_manifest(self, tmp_output_dir):
        legacy = {
            "components": [{"name": "backend", "command": "python app.py", "cwd": "."}]
        }
        manifest_path = os.path.join(tmp_output_dir, "manifest.json")
        with open(manifest_path, "w") as f:
            json.dump(legacy, f)

        rm = RunManifest(tmp_output_dir)
        loaded = rm.load_manifest()
        assert loaded["components"][0]["command"] == "python app.py"

    def test_fallback_detection_python(self, tmp_output_dir):
        # Create marker files for Python stack detection
        with open(os.path.join(tmp_output_dir, "main.py"), "w") as f:
            f.write("print('hello')")
        with open(os.path.join(tmp_output_dir, "requirements.txt"), "w") as f:
            f.write("fastapi")

        rm = RunManifest(tmp_output_dir)
        loaded = rm.load_manifest()
        assert any("python" in c["command"] for c in loaded["components"])


class TestDtuEnvInjection:
    def test_no_dtu(self, tmp_output_dir):
        rm = RunManifest(tmp_output_dir, dtu_url=None)
        env = rm._build_env()
        assert "DTU_URL" not in env

    def test_with_dtu(self, tmp_output_dir):
        rm = RunManifest(tmp_output_dir, dtu_url="http://localhost:8001")
        env = rm._build_env()
        assert env["DTU_URL"] == "http://localhost:8001"
        assert env["STRIPE_API_URL"] == "http://localhost:8001/stripe"
        assert env["AUTH_API_URL"] == "http://localhost:8001/auth"
