import os
import subprocess
import json
import time
from utils.logger import logger


class RunManifest:
    """Orchestrator for booting generated components (Frontend, Backend, DTU)."""

    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        self.manifest_path = os.path.join(output_dir, "manifest.json")
        self.processes = []

    def _detect_stack(self):
        """Detect stack from output files when no manifest exists."""
        has_requirements = os.path.exists(os.path.join(self.output_dir, "requirements.txt"))
        has_main_py = os.path.exists(os.path.join(self.output_dir, "main.py"))
        has_package_json = os.path.exists(os.path.join(self.output_dir, "package.json"))
        has_server_js = os.path.exists(os.path.join(self.output_dir, "server.js"))

        is_python = has_requirements or has_main_py
        is_node = has_package_json or has_server_js

        return is_python, is_node

    def load_manifest(self):
        if not os.path.exists(self.manifest_path):
            logger.warning(
                f"No manifest.json found in {self.output_dir}. Detecting stack..."
            )
            is_python, is_node = self._detect_stack()
            components = []

            if is_python:
                components.append(
                    {"name": "backend", "command": "python main.py", "cwd": "."}
                )
                logger.info("Detected Python backend.")
            elif is_node:
                components.append(
                    {"name": "backend", "command": "npm start", "cwd": "."}
                )
                logger.info("Detected Node.js backend.")

            # If we have package.json AND python backend, it's a hybrid (React frontend)
            if is_python and os.path.exists(os.path.join(self.output_dir, "package.json")):
                components.append(
                    {"name": "frontend", "command": "npm run dev", "cwd": "."}
                )
                logger.info("Detected hybrid stack: Python backend + Node frontend.")
            elif not is_python and is_node:
                # Full Node stack -- dev script handles both
                components = [
                    {"name": "app", "command": "npm run dev", "cwd": "."}
                ]

            if not components:
                logger.error("Could not detect any bootable components.")
                components = [
                    {"name": "backend", "command": "npm start", "cwd": "."}
                ]

            return {"components": components}

        with open(self.manifest_path, "r") as f:
            return json.load(f)

    def boot(self):
        manifest = self.load_manifest()
        logger.info(f"Booting system manifest for {self.output_dir}...")

        for comp in manifest.get("components", []):
            name = comp.get("name")
            cmd = comp.get("command")
            cwd = os.path.join(self.output_dir, comp.get("cwd", ""))

            logger.info(f"Starting {name} (cmd: {cmd}) in {cwd}...")

            try:
                # Start process in the background
                p = subprocess.Popen(
                    cmd.split(),
                    cwd=cwd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    shell=True,
                )
                self.processes.append({"name": name, "process": p})
            except Exception as e:
                logger.error(f"Failed to start {name}: {e}")

        # Wait a few seconds for startup
        time.sleep(5)
        self.check_status()

    def check_status(self):
        for item in self.processes:
            name = item["name"]
            p = item["process"]
            if p.poll() is None:
                logger.success(f"{name} (PID: {p.pid}) is running.")
            else:
                logger.error(f"{name} has stopped (Exit code: {p.returncode}).")

    def terminate(self):
        logger.info("Terminating all processes...")
        for item in self.processes:
            p = item["process"]
            p.terminate()
            logger.debug(f"Terminated {item['name']}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Dark App Factory Run Manifest")
    parser.add_argument("output_dir", help="Directory of the app to boot")
    args = parser.parse_args()

    orchestrator = RunManifest(args.output_dir)
    try:
        orchestrator.boot()
        # Keep alive for demonstration or until keyboard interrupt
        input("Press Enter to stop all components...\n")
    finally:
        orchestrator.terminate()
