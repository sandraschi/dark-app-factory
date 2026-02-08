import argparse
import asyncio
import subprocess
import time
import os
import sys
import socket
import json
import re

sys.path.append(os.path.join(os.path.dirname(__file__), "src"))
from utils.logger import logger
from llm_client import LLMClient


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


DTU_PORT = int(os.environ.get("DTU_PORT", "8001"))
DTU_URL = f"http://localhost:{DTU_PORT}"


def spin_up_dtu():
    """Start the Digital Twin Universe mock server.

    Returns the subprocess handle if started successfully, else None.
    """
    logger.info("Spinning up Digital Twin Universe on port %d...", DTU_PORT)
    dtu_env = os.environ.copy()
    dtu_env["DTU_PORT"] = str(DTU_PORT)

    dtu_process = subprocess.Popen(
        [sys.executable, "dtu/main.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=dtu_env,
    )
    time.sleep(3)
    if dtu_process.poll() is None:
        # Verify DTU is actually responding
        try:
            import urllib.request
            resp = urllib.request.urlopen(f"{DTU_URL}/health", timeout=5)
            if resp.status == 200:
                logger.info("DTU is online and healthy (%s)", DTU_URL)
                return dtu_process
        except Exception as e:
            logger.warning("DTU process alive but health check failed: %s", e)
            return dtu_process
    else:
        logger.error("DTU process exited immediately (exit code %s)", dtu_process.returncode)
        return None


def get_next_output_dir(base="output"):
    """Finds the next available output directory (e.g., output_001)."""
    i = 1
    while True:
        dirname = f"{base}_{i:03d}"
        if not os.path.exists(dirname):
            return dirname
        i += 1


def _extract_landing_page_data(specs_path: str, vibe_path: str = "vibe.md") -> dict:
    """Extract project name, subtitle, and features from specs and vibe
    for the landing page generator.
    """
    specs = ""
    if os.path.exists(specs_path):
        with open(specs_path, "r", encoding="utf-8") as f:
            specs = f.read()

    vibe = ""
    if os.path.exists(vibe_path):
        with open(vibe_path, "r", encoding="utf-8") as f:
            vibe = f.read()

    # Try to extract project title from first H1 in specs
    title_match = re.search(r"^#\s+(.+)$", specs, re.MULTILINE)
    project_name = title_match.group(1).strip() if title_match else "Dark App"

    # Extract features: look for bullet points under "## Features" or similar
    features = []
    feat_section = re.search(
        r"##\s+(?:Features|Key Features|Core Features)\s*\n(.*?)(?=\n##|\Z)",
        specs,
        re.DOTALL | re.IGNORECASE,
    )
    if feat_section:
        for line in feat_section.group(1).splitlines():
            line = line.strip().lstrip("-*").strip()
            if line and len(line) > 5:
                features.append(line)

    # Fallback: grab first 5 H3 headings as features
    if not features:
        h3s = re.findall(r"^###\s+(.+)$", specs, re.MULTILINE)
        features = h3s[:6]

    # Subtitle from vibe's first blockquote or first paragraph
    subtitle_match = re.search(r"^>\s+(.+)$", vibe, re.MULTILINE)
    subtitle = subtitle_match.group(1).strip().strip('"') if subtitle_match else ""
    if not subtitle:
        subtitle = f"Built with the Dark App Factory -- {project_name}"

    return {
        "project_name": project_name,
        "hero_title": project_name,
        "hero_subtitle": subtitle,
        "features": features[:8],  # cap at 8
    }


async def generate_landing_page(output_dir: str, specs_path: str = "specs/specs.md"):
    """Generate a landing page for the built app using LLM + static site builder.

    Creates {output_dir}/www/ with a multi-page static site.
    """
    logger.info("Propagandist: Generating landing page...")

    data = _extract_landing_page_data(specs_path)
    project_name = data["project_name"]
    features = data["features"]

    www_dir = os.path.join(output_dir, "www")
    os.makedirs(www_dir, exist_ok=True)

    # Use Foreman LLM to generate the landing page HTML
    foreman = LLMClient(role="foreman")

    features_block = "\n".join(f"- {f}" for f in features) if features else "- Cutting-edge application"

    html_prompt = f"""
    Generate a SINGLE, SELF-CONTAINED index.html landing page for:
    
    Project: {project_name}
    Tagline: {data["hero_subtitle"]}
    
    Features:
    {features_block}
    
    DESIGN REQUIREMENTS:
    - SINGLE FILE: ALL CSS and JS must be inline (no external files).
    - Dark theme (#09090b background, white text).
    - Hero section with project name, tagline, and a glowing CTA button.
    - Features section with cards (glassmorphism: backdrop-blur, semi-transparent backgrounds).
    - Smooth scroll-triggered animations (CSS only, no libraries).
    - Responsive (mobile-first with media queries).
    - Modern typography (use Google Fonts link: Inter or Outfit).
    - Gradient accent colors (cyan #00f3ff to purple #bd00ff).
    - Footer with "Built with Dark App Factory" credit.
    - NO external JS libraries. NO React. Plain HTML + CSS + vanilla JS.
    - Minimum 200 lines. DENSE, PRODUCTION-QUALITY code.
    
    Output ONLY the complete HTML file. No markdown fences.
    """

    html = await foreman.generate(
        html_prompt,
        system_prompt=(
            "You are a world-class web designer. Generate ONLY a complete, "
            "self-contained index.html file. No explanations, no markdown."
        ),
        temperature=0.5,
    )

    if not html:
        logger.error("Propagandist: LLM failed to generate landing page.")
        return

    # Clean markdown fences if present
    html = html.strip()
    if html.startswith("```"):
        html = re.sub(r"^```\w*\s*\n", "", html)
        html = re.sub(r"\n```\s*$", "", html)

    index_path = os.path.join(www_dir, "index.html")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(html)

    logger.success("Landing page generated -> %s", index_path)
    return index_path


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

        # 4. DTU (Mock Environment) -- start BEFORE build so it is available for testing
        dtu = spin_up_dtu()
        if not dtu:
            logger.warning("DTU failed to start. Continuing without Digital Twin integration.")

        try:
            # 5. Worker (Build) - Pass dynamic output dir
            if not run_step(
                "Worker Building",
                [sys.executable, "worker.py", "build", "--output", output_dir],
            ):
                return

            # 6. Propagandist (Landing Page) -- always runs, even for API-only apps
            try:
                asyncio.run(generate_landing_page(output_dir))
            except Exception as e:
                logger.warning("Landing page generation failed (non-fatal): %s", e)

            # 7. Satisficer (Judge) -- passes DTU URL so RunManifest injects env vars
            judge_cmd = [sys.executable, "judge.py", "judge", "--output", output_dir]
            if dtu:
                judge_cmd.extend(["--dtu-url", DTU_URL])
            run_step("Satisficer Judging", judge_cmd)

            logger.info("Factory Run Complete. Output: %s", output_dir)

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

                    # Build DTU env var string for cmd /k
                    dtu_env_str = ""
                    if dtu:
                        dtu_env_str = (
                            f" && set DTU_URL={DTU_URL}"
                            f" && set STRIPE_API_URL={DTU_URL}/stripe"
                            f" && set AUTH_API_URL={DTU_URL}/auth"
                            f" && set EMAIL_API_URL={DTU_URL}/email"
                            f" && set SMS_API_URL={DTU_URL}/sms"
                            f" && set STORAGE_API_URL={DTU_URL}/storage"
                        )

                    # 1. Open Output Folder
                    os.startfile(output_dir)

                    # 2. Launch Backend
                    if is_python:
                        logger.info("Launching Python backend...")
                        launch_cmd = (
                            f'start "Python Backend (port {server_port})" cmd /k '
                            f'"cd {output_dir}{dtu_env_str} && pip install -r requirements.txt && set PORT={server_port} && python main.py"'
                        )
                        subprocess.Popen(launch_cmd, shell=True)
                        audit_port = server_port

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
                            f'"cd {output_dir}{dtu_env_str} && set PORT={server_port} && set VITE_PORT={client_port} && npm install --legacy-peer-deps && npm run dev"'
                        )
                        subprocess.Popen(launch_cmd, shell=True)
                        audit_port = client_port
                    else:
                        logger.warning("No package.json or requirements.txt found. Cannot auto-launch.")
                        audit_port = None

                    # 3. Launch Questionnaire
                    logger.info("Launching Feedback Loop...")
                    subprocess.Popen(
                        'start "Feedback Loop" cmd /c "python questionnaire.py"',
                        shell=True,
                    )

                    # 4. Automated Audit
                    if audit_port:
                        logger.info("Starting Automated Audit...")
                        logger.debug("Waiting for port %d to become active...", audit_port)

                        found = False
                        for _ in range(30):
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
                                            logger.info("Audit Passed. No critical runtime errors.")
                                        else:
                                            logger.error("Audit Failed.")
                                            for err in report["errors"]:
                                                logger.error("  - %s", err)
                                            if report.get("screenshot_path"):
                                                logger.info("Screenshot: %s", report["screenshot_path"])
                                    except json.JSONDecodeError:
                                        logger.warning(
                                            "Could not parse audit report: %s",
                                            audit_result.stdout[:500],
                                        )
                            except Exception as e:
                                logger.error("Auditor failed to run: %s", e)
                        else:
                            logger.error("Port %d never came online. Audit skipped.", audit_port)

                except Exception as e:
                    logger.error("Could not launch generated app: %s", e)

        finally:
            if dtu:
                logger.info("Shutting down DTU...")
                dtu.terminate()
                dtu.wait(timeout=5)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
