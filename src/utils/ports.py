"""Port allocation and process-tree termination helpers.

Centralises the logic that was previously duplicated (and inconsistent)
across factory.py, judge.py and run_manifest.py.

Two problems this module exists to solve:

1. **Port guessing.** The judge used to probe a hardcoded list of ports
   (3000, 8000, 5173, ...) to find the generated app. On a developer
   workstation with other servers running, that probe can latch onto an
   unrelated process and audit the wrong application, producing a PASS for
   an app that never booted. Ports are now allocated up front and passed
   explicitly to the child via PORT / VITE_PORT, and only those ports are
   polled.

2. **Orphaned children.** Processes are started with shell=True, so
   Popen.terminate() kills the shell and leaves the real node/python
   process running. Those orphans hold ports and cause the next run's
   probe to report a false success.
"""

import os
import socket
import subprocess
import sys

from src.utils.logger import logger

# Default allocation window for generated apps. Deliberately outside the
# common dev-server range (3000/5173/8000/8080) so a developer's own
# servers can never be mistaken for a generated app. Override with
# APP_PORT_START / APP_PORT_END.
DEFAULT_PORT_START = int(os.environ.get("APP_PORT_START", "19300"))
DEFAULT_PORT_END = int(os.environ.get("APP_PORT_END", "19400"))

# Ports that the factory's own infrastructure and generated apps have
# historically bound. Used by the zombie hunter.
KNOWN_FACTORY_PORTS = (3000, 5173, 5174, 8000, 8001, 8002, 8080)


def is_port_free(port: int, host: str = "localhost") -> bool:
    """Return True if nothing is listening on the given port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) != 0


def is_port_listening(port: int, host: str = "localhost") -> bool:
    """Return True if something IS listening on the given port."""
    return not is_port_free(port, host)


def find_free_ports(
    count: int = 2,
    start_port: int = DEFAULT_PORT_START,
    end_port: int = DEFAULT_PORT_END,
) -> list[int]:
    """Find `count` consecutive free ports in the given window."""
    for port in range(start_port, end_port - count + 2):
        if all(is_port_free(p) for p in range(port, port + count)):
            return [port + i for i in range(count)]
    raise RuntimeError(f"Could not find {count} free ports in range {start_port}-{end_port}")


def listening_pids(ports) -> set:
    """Return the set of PIDs listening on any of the given ports.

    `ports` may be an iterable of ints or (start, end) range tuples.
    """
    wanted = set()
    for entry in ports:
        if isinstance(entry, tuple):
            wanted.update(range(entry[0], entry[1] + 1))
        else:
            wanted.add(int(entry))

    pids = set()
    try:
        if sys.platform == "win32":
            result = subprocess.run(
                ["netstat", "-ano"],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
            )
            for line in (result.stdout or "").splitlines():
                parts = line.split()
                if len(parts) >= 5 and "LISTENING" in line:
                    address, pid = parts[1], parts[4]
                    if ":" not in address:
                        continue
                    try:
                        port = int(address.rsplit(":", 1)[1])
                    except ValueError:
                        continue
                    if port in wanted and pid.isdigit() and pid != "0":
                        pids.add(int(pid))
        else:
            result = subprocess.run(
                ["lsof", "-nP", "-iTCP", "-sTCP:LISTEN"],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
            )
            for line in (result.stdout or "").splitlines()[1:]:
                parts = line.split()
                if len(parts) >= 9 and parts[1].isdigit():
                    address = parts[8]
                    if ":" not in address:
                        continue
                    try:
                        port = int(address.rsplit(":", 1)[1])
                    except ValueError:
                        continue
                    if port in wanted:
                        pids.add(int(parts[1]))
    except FileNotFoundError:
        logger.warning("Port scan tool not found; skipping zombie hunt.")
    except Exception as e:
        logger.warning("Port scan failed: %s", e)

    return pids


def kill_pid_tree(pid: int) -> bool:
    """Kill a process and every descendant it spawned.

    Popen.terminate() on a shell=True process only kills the shell, so the
    real server keeps running and holding its port. This kills the tree.
    """
    if not pid:
        return False
    try:
        if sys.platform == "win32":
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(pid)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=15,
            )
        else:
            try:
                os.killpg(os.getpgid(pid), 9)
            except (ProcessLookupError, PermissionError):
                os.kill(pid, 9)
        return True
    except Exception as e:
        logger.debug("kill_pid_tree(%s) failed: %s", pid, e)
        return False


def kill_ports(ports) -> int:
    """Kill every process listening on the given ports. Returns the count."""
    pids = listening_pids(ports)
    if not pids:
        return 0
    killed = 0
    for pid in pids:
        if kill_pid_tree(pid):
            killed += 1
    return killed


def popen_kwargs() -> dict:
    """Platform kwargs so a child can later be killed as a group."""
    if sys.platform == "win32":
        return {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}
    return {"start_new_session": True}
