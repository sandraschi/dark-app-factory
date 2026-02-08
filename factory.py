import argparse
import subprocess
import time
import os
import sys
import socket
import json
import re

sys.path.append(os.path.join(os.path.dirname(__file__), "src"))
from utils.logger import logger


def kill_zombies(start_port=19300, end_port=19400):
    """Kills any process listening on ports in the given range."""
    logger.info("Hunting zombie processes on ports %d-%d...", start_port, end_port)

    try:
        result = subprocess.run(
            "netstat -ano | findstr LISTENING",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        if not result.stdout:
            logger.info("No zombies found.")
            return

        lines = result.stdout.splitlines()
        pids_to_kill = set()

        for line in lines:
            parts = line.split()
            if len(parts) >= 5:
                address = parts[1]
                pid = parts[4]

                if ":" in address:
                    port_str = address.rsplit(":", 1)[1]
                    try:
                        port = int(port_str)
                        if start_port <= port <= end_port:
                            pids_to_kill.add(pid)
                    except ValueError:
                        pass

        if not pids_to_kill:
            logger.info("No zombies found in port range.")
            return

        logger.info("Found %d zombie processes. Terminating...", len(pids_to_kill))
        for pid in pids_to_kill:
            subprocess.run(
                f"taskkill /F /PID {pid}",
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            logger.debug("Killed PID %s", pid)

    except Exception as e:
        logger.error("Failed to hunt zombies: %s", e)


def find_free_ports(count=2, start_port=19300, end_port=19400):
    """Finds 'count' consecutive free ports."""
    for port in range(start_port, end_port - count + 1):
        if all(is_port_free(p) for p in range(port, port + count)):
            return [port + i for i in range(count)]

    raise RuntimeError(
        f"Could not find {count} free ports in range {start_port}-{end_port}"
    )


def is_port_free(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("localhost", port)) != 0


def run_step(description, command):
    logger.info("STEP: %s", description)
    try:
        subprocess.run(command, shell=True, check=True)
        logger.success("%s Complete", description)
        return True
    except subprocess.CalledProcessError:
        logger.error("%s Failed", description)
        return False


def spin_up_dtu():
    logger.info("Spinning up Digital Twin Universe...")
    dtu_process = subprocess.Popen(
        [sys.executable, "dtu/main.py"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    time.sleep(2)
    if dtu_process.poll() is None:
        logger.success("DTU is online (Port 8001)")
        return dtu_process
    else:
        logger.error("DTU failed to start")
        return None


def get_next_output_dir(base="output"):
    """Finds the next available output directory (e.g., output_001)."""
    i = 1
    while True:
        dirname = f"{base}_{i:03d}"
        if not os.path.exists(dirname):
            return dirname
        i += 1


def main():
    parser = argparse.ArgumentParser(description="Dark App Factory Orchestrator")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("run", help="Run the full factory loop")

    args = parser.parse_args()

    if args.command == "run":
        logger.info("=== DARK APP FACTORY ===")

        # 0. Kill Zombies & Prepare
        kill_zombies()

        # 1. Determine Output Directory
        os.makedirs("outputs", exist_ok=True)
        output_dir = get_next_output_dir(base="outputs/output")
        logger.info("Target output: %s", output_dir)

        # 2. Foreman Research (Oracle)
        if not run_step(
            "Domain Research (Oracle)", [sys.executable, "foreman.py", "research"]
        ):
            return

        # 3. Foreman (Plan)
        if not run_step("Foreman Planning", [sys.executable, "foreman.py", "plan"]):
            return

        # 4. Worker (Build) - Pass dynamic output dir
        if not run_step(
            "Worker Building",
            [sys.executable, "worker.py", "build", "--output", output_dir],
        ):
            return

        # 5. DTU (Mock Environment)
        dtu = spin_up_dtu()
        if not dtu:
            return

        try:
            # 6. Satisficer (Judge)
            run_step(
                "Satisficer Judging",
                [sys.executable, "judge.py", "judge", "--output", output_dir],
            )

            logger.success("Factory Run Complete! Output: %s", output_dir)

            # Auto-launch results (Windows)
            if os.name == "nt":
                try:
                    # Detect stack from output
                    has_requirements = os.path.exists(f"{output_dir}/requirements.txt")
                    has_main_py = os.path.exists(f"{output_dir}/main.py")
                    has_package_json = os.path.exists(f"{output_dir}/package.json")
                    is_python = has_requirements or has_main_py

                    # Allocate Ports
                    try:
                        server_port, client_port = find_free_ports(2)
                        logger.info(
                            "Allocated ports: Backend=%d Frontend=%d",
                            server_port,
                            client_port,
                        )
                    except RuntimeError as e:
                        logger.error("Port allocation failed: %s", e)
                        return

                    # 1. Open Output Folder
                    os.startfile(output_dir)

                    # 2. Launch Backend
                    if is_python:
                        logger.info("Launching Python backend...")
                        launch_cmd = (
                            f'start "Python Backend (port {server_port})" cmd /k '
                            f'"cd {output_dir} && pip install -r requirements.txt && set PORT={server_port} && python main.py"'
                        )
                        subprocess.Popen(launch_cmd, shell=True)
                        audit_port = server_port

                        # If hybrid (Python + React), also launch frontend
                        if has_package_json:
                            logger.info("Launching React frontend (hybrid)...")
                            frontend_cmd = (
                                f'start "React Frontend (port {client_port})" cmd /k '
                                f'"cd {output_dir} && set VITE_PORT={client_port} && npm install --legacy-peer-deps && npm run dev"'
                            )
                            subprocess.Popen(frontend_cmd, shell=True)
                            audit_port = client_port

                    elif has_package_json:
                        logger.info("Launching Node.js app...")
                        launch_cmd = (
                            f'start "Generated App ({server_port}/{client_port})" cmd /k '
                            f'"cd {output_dir} && set PORT={server_port} && set VITE_PORT={client_port} && npm install --legacy-peer-deps && npm run dev"'
                        )
                        subprocess.Popen(launch_cmd, shell=True)
                        audit_port = client_port
                    else:
                        logger.warning("No package.json or requirements.txt found. Cannot auto-launch.")
                        audit_port = None

                    # 3. Launch Questionnaire in new window
                    logger.info("Launching Feedback Loop...")
                    subprocess.Popen(
                        'start "Feedback Loop" cmd /c "python questionnaire.py"',
                        shell=True,
                    )

                    # 4. Automated Audit
                    if audit_port:
                        logger.info("Starting Automated Audit...")
                        logger.debug(
                            "Waiting for port %d to become active...", audit_port
                        )

                        found = False
                        for _ in range(30):  # Wait up to 60s
                            if not is_port_free(audit_port):
                                found = True
                                break
                            time.sleep(2)

                        if found:
                            logger.info("Port active. Warming up (5s)...")
                            time.sleep(5)
                            try:
                                audit_cmd = [
                                    sys.executable,
                                    "src/auditor.py",
                                    f"http://localhost:{audit_port}",
                                ]
                                audit_result = subprocess.run(
                                    audit_cmd, capture_output=True, text=True
                                )
                                if audit_result.stdout:
                                    try:
                                        report = json.loads(audit_result.stdout)
                                        if report["success"]:
                                            logger.success(
                                                "Audit Passed. No critical runtime errors."
                                            )
                                        else:
                                            logger.error("Audit Failed.")
                                            for err in report["errors"]:
                                                logger.error("  - %s", err)
                                            if report["screenshot_path"]:
                                                logger.info(
                                                    "Screenshot: %s",
                                                    report["screenshot_path"],
                                                )
                                    except json.JSONDecodeError:
                                        logger.warning(
                                            "Could not parse audit report: %s",
                                            audit_result.stdout[:500],
                                        )
                            except Exception as e:
                                logger.error("Auditor failed to run: %s", e)
                        else:
                            logger.error(
                                "Port %d never came online. Audit skipped.", audit_port
                            )

                except Exception as e:
                    logger.error("Could not launch generated app: %s", e)

        finally:
            if dtu:
                logger.info("Shutting down DTU...")
                dtu.terminate()

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
