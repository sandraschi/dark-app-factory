# ruff: noqa: E402
import json
import os
import shutil
import subprocess
import sys
import time

# Normalize import paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
if os.path.join(BASE_DIR, "src") not in sys.path:
    sys.path.insert(1, os.path.join(BASE_DIR, "src"))

from src.utils.logger import logger
from src.utils.ports import (
    is_port_listening,
    kill_pid_tree,
    popen_kwargs,
)


def _env_flag(name: str, default: bool = False) -> bool:
    """Read a boolean environment variable."""
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


def write_manifest_from_output(output_dir: str) -> str | None:
    """Write manifest.json into output_dir based on detected stack.

    Call after worker build completes so RunManifest finds it instead of
    falling back to heuristic detection. Uses entry_points format for
    compatibility with _manifest_to_components.

    Returns the manifest path if written, else None.
    """
    manifest_path = os.path.join(output_dir, "manifest.json")
    has_requirements = os.path.exists(os.path.join(output_dir, "requirements.txt"))
    has_main_py = os.path.exists(os.path.join(output_dir, "main.py"))
    has_app_py = os.path.exists(os.path.join(output_dir, "app.py"))
    has_package_json = os.path.exists(os.path.join(output_dir, "package.json"))
    has_server_js = os.path.exists(os.path.join(output_dir, "server.js"))

    is_python = has_requirements or has_main_py or has_app_py
    is_node = has_package_json or has_server_js

    entry_points = {}

    if is_python:
        backend = "main.py" if has_main_py else ("app.py" if has_app_py else "main.py")
        entry_points["backend"] = backend

    if is_node and not is_python:
        entry_points["backend"] = "server.js" if has_server_js else "npm start"

    if is_python and has_package_json:
        entry_points["react_entry"] = "index.html"

    if not entry_points:
        logger.warning("No bootable components detected; writing minimal manifest.")
        entry_points = {"backend": "main.py"}

    manifest_data = {
        "entry_points": entry_points,
        "generated_by": "Dark App Factory",
    }

    try:
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest_data, f, indent=2)
        logger.info("Wrote manifest.json -> %s", manifest_path)
        return manifest_path
    except OSError as e:
        logger.warning("Failed to write manifest.json: %s", e)
        return None


# DTU service registry: env var -> DTU endpoint mapping.
# When dtu_url is provided, these env vars are injected so the
# generated app talks to the DTU instead of real external APIs.
DTU_ENV_VARS = {
    "STRIPE_API_URL": "/stripe",
    "AUTH_API_URL": "/auth",
    "EMAIL_API_URL": "/email",
    "SMS_API_URL": "/sms",
    "STORAGE_API_URL": "/storage",
    "DISCORD_WEBHOOK_URL": "/discord",
    "SLACK_WEBHOOK_URL": "/slack",
    "WEATHER_API_URL": "/weather",
    "WEBHOOK_URL": "/webhook",
    "OPENAI_BASE_URL": "/llm",
    "GOOGLE_CALENDAR_API_URL": "/calendar",
    "GOOGLE_MAPS_API_URL": "/maps",
    "ANALYTICS_API_URL": "/analytics",
    "PUZZLE_API_URL": "/puzzles",
    "TIKTOK_API_URL": "/tiktok",
    "YOUTUBE_API_URL": "/youtube",
}


class RunManifest:
    """Orchestrator for booting generated components (Frontend, Backend, DTU)."""

    def __init__(
        self,
        output_dir: str,
        dtu_url: str | None = None,
        backend_port: int | None = None,
        frontend_port: int | None = None,
        install_deps: bool | None = None,
        install_timeout: int | None = None,
    ):
        """
        Args:
            output_dir: Path to the generated app directory.
            dtu_url: Base URL of the DTU server (e.g. http://localhost:8001).
                     If provided, DTU env vars are injected into child processes.
            backend_port: Port to force the backend onto (exported as PORT).
                     When None, the child picks its own and startup detection
                     falls back to the legacy probe.
            frontend_port: Port to force the Vite dev server onto (exported as
                     VITE_PORT).
            install_deps: Install npm/pip dependencies before booting. Generated
                     apps ship source only, so without this every boot fails
                     with "Cannot find module".
            install_timeout: Seconds allowed for each install command.
        """
        self.output_dir = output_dir
        self.manifest_path = os.path.join(output_dir, "manifest.json")
        self.dtu_url = dtu_url
        self.backend_port = backend_port
        self.frontend_port = frontend_port
        self.install_deps = _env_flag("SKIP_APP_INSTALL", False) is False if install_deps is None else install_deps
        self.install_timeout = (
            int(os.environ.get("APP_INSTALL_TIMEOUT", "600")) if install_timeout is None else install_timeout
        )
        self.processes = []
        self.log_dir = os.path.join(output_dir, ".factory-logs")

        # Populated by boot(). Consumed by the judge so the verdict is based
        # on what actually happened rather than on a hopeful port probe.
        self.boot_report = {
            "install_ran": False,
            "install_ok": None,
            "install_errors": [],
            "app_url": None,
            "listening_port": None,
            "is_live": False,
            "process_status": [],
            "log_excerpts": {},
        }

    @property
    def is_live(self) -> bool:
        """True only if the app was observed listening on an assigned port."""
        return bool(self.boot_report.get("is_live"))

    @property
    def app_url(self) -> str | None:
        return self.boot_report.get("app_url")

    def _expected_ports(self) -> list:
        """Ports we explicitly assigned to children, most user-facing first."""
        ports = []
        if self.frontend_port:
            ports.append(self.frontend_port)
        if self.backend_port:
            ports.append(self.backend_port)
        return ports

    def _build_env(self) -> dict[str, str]:
        """Build environment dict for child processes.

        Injects DTU vars when available, and pins the app's ports so startup
        detection watches a port we own rather than guessing from a shared
        list of common dev-server ports.
        """
        env = os.environ.copy()

        if self.dtu_url:
            base = self.dtu_url.rstrip("/")
            for var_name, path_suffix in DTU_ENV_VARS.items():
                env[var_name] = f"{base}{path_suffix}"
            env["DTU_URL"] = base
            logger.info("DTU env vars injected (base: %s)", base)

        if self.backend_port:
            env["PORT"] = str(self.backend_port)
            env["BACKEND_PORT"] = str(self.backend_port)
        if self.frontend_port:
            env["VITE_PORT"] = str(self.frontend_port)

        return env

    def _detect_stack(self):
        """Detect stack from output files when no manifest exists."""
        has_requirements = os.path.exists(os.path.join(self.output_dir, "requirements.txt"))
        has_main_py = os.path.exists(os.path.join(self.output_dir, "main.py"))
        has_app_py = os.path.exists(os.path.join(self.output_dir, "app.py"))
        has_package_json = os.path.exists(os.path.join(self.output_dir, "package.json"))
        has_server_js = os.path.exists(os.path.join(self.output_dir, "server.js"))

        is_python = has_requirements or has_main_py or has_app_py
        is_node = has_package_json or has_server_js

        return is_python, is_node

    def _manifest_to_components(self, manifest_data: dict) -> dict:
        """Convert worker-generated manifest.json (entry_points format)
        into the components format RunManifest expects.

        Worker writes: {"entry_points": {"backend": "main.py", "frontend": "index.html"}, ...}
        RunManifest needs: {"components": [{"name": "backend", "command": "python main.py", "cwd": "."}]}
        """
        entry_points = manifest_data.get("entry_points", {})
        components = []

        backend_entry = entry_points.get("backend")
        if backend_entry:
            if backend_entry.endswith(".py"):
                components.append(
                    {
                        "name": "backend",
                        "command": f"python {backend_entry}",
                        "cwd": ".",
                    }
                )
            elif backend_entry.endswith(".js"):
                components.append({"name": "backend", "command": f"node {backend_entry}", "cwd": "."})
            else:
                components.append({"name": "backend", "command": "npm start", "cwd": "."})
            logger.info("Manifest: backend entry -> %s", backend_entry)

        react_entry = entry_points.get("react_entry")
        if react_entry:
            components.append({"name": "frontend", "command": "npm run dev", "cwd": "."})
            logger.info("Manifest: React frontend detected -> %s", react_entry)

        return {"components": components} if components else None

    def load_manifest(self):
        if os.path.exists(self.manifest_path):
            with open(self.manifest_path, encoding="utf-8") as f:
                manifest_data = json.load(f)

            # Worker-generated manifest has "entry_points" key; convert it
            if "entry_points" in manifest_data:
                converted = self._manifest_to_components(manifest_data)
                if converted and converted["components"]:
                    logger.info(
                        "Loaded manifest.json from %s (%d components).",
                        self.output_dir,
                        len(converted["components"]),
                    )
                    return converted
                logger.warning("manifest.json found but no bootable entry_points. Falling back to detection.")

            # Legacy format with "components" key -- use directly
            if "components" in manifest_data:
                logger.info("Loaded legacy manifest.json from %s.", self.output_dir)
                return manifest_data

        # Fallback: auto-detect stack from files
        logger.warning("No usable manifest.json in %s. Detecting stack...", self.output_dir)
        is_python, is_node = self._detect_stack()
        components = []

        if is_python:
            entry = "main.py"
            if not os.path.exists(os.path.join(self.output_dir, "main.py")):
                if os.path.exists(os.path.join(self.output_dir, "app.py")):
                    entry = "app.py"
            components.append({"name": "backend", "command": f"python {entry}", "cwd": "."})
            logger.info("Detected Python backend (entry: %s).", entry)
        elif is_node:
            components.append({"name": "backend", "command": "npm start", "cwd": "."})
            logger.info("Detected Node.js backend.")

        # Hybrid: Python backend + React frontend
        if is_python and os.path.exists(os.path.join(self.output_dir, "package.json")):
            components.append({"name": "frontend", "command": "npm run dev", "cwd": "."})
            logger.info("Detected hybrid stack: Python backend + Node frontend.")
        elif not is_python and is_node:
            components = [{"name": "app", "command": "npm run dev", "cwd": "."}]

        if not components:
            logger.error("Could not detect any bootable components.")
            components = [{"name": "backend", "command": "npm start", "cwd": "."}]

        return {"components": components}

    # ------------------------------------------------------------------
    # Dependency installation
    # ------------------------------------------------------------------

    @staticmethod
    def _node_installer() -> list:
        """Pick the fastest available Node package manager."""
        if shutil.which("bun"):
            return ["bun", "install"]
        if shutil.which("pnpm"):
            return ["pnpm", "install"]
        npm = "npm.cmd" if os.name == "nt" else "npm"
        return [npm, "install", "--legacy-peer-deps", "--no-audit", "--no-fund"]

    def _run_install(self, label: str, cmd: list) -> bool:
        """Run one install command, log its output, return success."""
        os.makedirs(self.log_dir, exist_ok=True)
        log_path = os.path.join(self.log_dir, f"install-{label}.log")
        logger.info("Installing %s dependencies: %s", label, " ".join(cmd))
        try:
            with open(log_path, "w", encoding="utf-8", errors="replace") as log:
                result = subprocess.run(
                    cmd,
                    cwd=self.output_dir,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    timeout=self.install_timeout,
                )
        except subprocess.TimeoutExpired:
            msg = f"{label} install timed out after {self.install_timeout}s"
            logger.error(msg)
            self.boot_report["install_errors"].append(msg)
            return False
        except FileNotFoundError as e:
            msg = f"{label} install tool not found: {e}"
            logger.error(msg)
            self.boot_report["install_errors"].append(msg)
            return False
        except Exception as e:
            msg = f"{label} install failed to launch: {e}"
            logger.error(msg)
            self.boot_report["install_errors"].append(msg)
            return False

        if result.returncode != 0:
            tail = self._read_tail(log_path, 30)
            msg = f"{label} install exited {result.returncode}"
            logger.error("%s. Log tail:\n%s", msg, tail)
            self.boot_report["install_errors"].append(msg)
            self.boot_report["log_excerpts"][f"install-{label}"] = tail
            return False

        logger.info("%s dependencies installed.", label.capitalize())
        return True

    @staticmethod
    def _read_tail(path: str, lines: int = 30) -> str:
        try:
            with open(path, encoding="utf-8", errors="replace") as f:
                content = f.read().splitlines()
            return "\n".join(content[-lines:])
        except OSError:
            return ""

    def install_dependencies(self) -> bool:
        """Install the generated app's dependencies before booting it.

        The factory emits source files only. Without this step every boot
        fails with "Cannot find module 'express'" or "No module named
        'fastapi'", and the judge then evaluates a dead server.
        """
        if not self.install_deps:
            logger.info("Dependency install disabled; booting as-is.")
            return True

        ok = True
        self.boot_report["install_ran"] = True

        has_package_json = os.path.exists(os.path.join(self.output_dir, "package.json"))
        has_node_modules = os.path.isdir(os.path.join(self.output_dir, "node_modules"))
        if has_package_json:
            if has_node_modules:
                logger.info("node_modules already present; skipping node install.")
            else:
                ok = self._run_install("node", self._node_installer()) and ok

        req_path = os.path.join(self.output_dir, "requirements.txt")
        if os.path.exists(req_path):
            ok = (
                self._run_install(
                    "python",
                    [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
                )
                and ok
            )

        self.boot_report["install_ok"] = ok
        return ok

    # ------------------------------------------------------------------
    # Boot
    # ------------------------------------------------------------------

    def boot(self):
        manifest = self.load_manifest()

        # Install first. A boot without dependencies is guaranteed to fail
        # and would leave the judge auditing nothing.
        self.install_dependencies()

        env = self._build_env()
        os.makedirs(self.log_dir, exist_ok=True)

        logger.info("Booting system manifest for %s...", self.output_dir)
        if self.dtu_url:
            logger.info("DTU integration active: %s", self.dtu_url)
        if self._expected_ports():
            logger.info(
                "Assigned ports: backend=%s frontend=%s",
                self.backend_port,
                self.frontend_port,
            )

        for comp in manifest.get("components", []):
            name = comp.get("name")
            cmd = comp.get("command")
            cwd = os.path.join(self.output_dir, comp.get("cwd", ""))

            # On Windows, npm/npx need the .cmd extension to resolve via shell
            if os.name == "nt" and isinstance(cmd, str):
                if cmd.startswith("npm "):
                    cmd = "npm.cmd " + cmd[4:]
                elif cmd.startswith("npx "):
                    cmd = "npx.cmd " + cmd[4:]

            logger.info("Starting %s (cmd: %s) in %s...", name, cmd, cwd)

            # Child output goes to a file, not a pipe. An unread PIPE fills
            # its OS buffer and deadlocks verbose processes such as Vite.
            log_path = os.path.join(self.log_dir, f"{name}.log")
            try:
                log_handle = open(log_path, "w", encoding="utf-8", errors="replace")
                p = subprocess.Popen(
                    cmd,
                    cwd=cwd,
                    stdout=log_handle,
                    stderr=subprocess.STDOUT,
                    env=env,
                    shell=True,
                    **popen_kwargs(),
                )
                self.processes.append(
                    {
                        "name": name,
                        "process": p,
                        "log": log_path,
                        "handle": log_handle,
                    }
                )
            except Exception as e:
                logger.error("Failed to start %s: %s", name, e)
                self.boot_report["install_errors"].append(f"{name} failed to start: {e}")

        self._wait_for_startup(timeout=60)
        return self.boot_report

    def _wait_for_startup(self, timeout: int = 60):
        """Poll the ports we assigned until one opens or the timeout expires.

        Only ports handed to the child are polled. Probing a shared list of
        common dev ports can latch onto an unrelated server and report a
        successful boot for an app that never started.
        """
        expected = self._expected_ports()
        if not expected:
            # No explicit assignment; fall back to the legacy probe but say so.
            expected = [3000, 8000, 5173, 5174, 8080]
            logger.warning(
                "No ports assigned to this run; falling back to a shared-port "
                "probe. A match may belong to an unrelated process."
            )
            trusted = False
        else:
            trusted = True

        deadline = time.time() + timeout
        logger.info("Waiting for app to start (up to %ds)...", timeout)
        while time.time() < deadline:
            for port in expected:
                if is_port_listening(port):
                    logger.info("App listening on port %d.", port)
                    self.boot_report["listening_port"] = port
                    self.boot_report["app_url"] = f"http://localhost:{port}"
                    self.boot_report["is_live"] = trusted
                    self.check_status()
                    return
            if self.processes and all(p["process"].poll() is not None for p in self.processes):
                logger.error("All processes exited before startup completed.")
                break
            time.sleep(1)

        logger.warning("App never listened on %s.", expected)
        self.boot_report["is_live"] = False
        self._collect_log_excerpts()
        self.check_status()

    def _collect_log_excerpts(self):
        """Capture the tail of each child log so failures are explainable."""
        for item in self.processes:
            tail = self._read_tail(item.get("log", ""), 25)
            if tail:
                self.boot_report["log_excerpts"][item["name"]] = tail
                logger.warning("%s log tail:\n%s", item["name"], tail)

    def check_status(self):
        statuses = []
        for item in self.processes:
            name = item["name"]
            p = item["process"]
            if p.poll() is None:
                logger.info("%s (PID: %d) is running.", name, p.pid)
                statuses.append({"name": name, "running": True, "exit_code": None})
            else:
                logger.error("%s has stopped (Exit code: %s).", name, p.returncode)
                statuses.append({"name": name, "running": False, "exit_code": p.returncode})
                tail = self._read_tail(item.get("log", ""), 25)
                if tail:
                    self.boot_report["log_excerpts"][name] = tail
        self.boot_report["process_status"] = statuses

    def terminate(self):
        """Kill each component and every process it spawned.

        Popen.terminate() on a shell=True process only kills the shell, so
        the real server survives, keeps its port, and causes the next run to
        mistake it for a successful boot.
        """
        logger.info("Terminating all processes...")
        for item in self.processes:
            p = item["process"]
            try:
                kill_pid_tree(p.pid)
                try:
                    p.wait(timeout=5)
                except Exception:
                    pass
                logger.debug("Terminated %s", item["name"])
            except Exception as e:
                logger.warning("Could not terminate %s: %s", item["name"], e)
            finally:
                handle = item.get("handle")
                if handle:
                    try:
                        handle.close()
                    except Exception:
                        pass
        self.processes = []


if __name__ == "__main__":
    import argparse

    from src.utils.ports import find_free_ports

    parser = argparse.ArgumentParser(description="Dark App Factory Run Manifest")
    parser.add_argument("output_dir", help="Directory of the app to boot")
    parser.add_argument(
        "--dtu-url",
        default=None,
        help="DTU base URL (e.g. http://localhost:8001). Injects DTU env vars.",
    )
    parser.add_argument(
        "--no-install",
        action="store_true",
        help="Skip npm/pip install (assumes dependencies are already present).",
    )
    args = parser.parse_args()

    backend_port, frontend_port = find_free_ports(2)
    orchestrator = RunManifest(
        args.output_dir,
        dtu_url=args.dtu_url,
        backend_port=backend_port,
        frontend_port=frontend_port,
        install_deps=not args.no_install,
    )
    try:
        orchestrator.boot()
        if orchestrator.is_live:
            logger.info("App available at %s", orchestrator.app_url)
        else:
            logger.error("App did not start. See %s", orchestrator.log_dir)
        input("Press Enter to stop all components...\n")
    finally:
        orchestrator.terminate()
