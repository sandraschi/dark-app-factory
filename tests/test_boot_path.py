"""Tests for the boot and verify path fixes (2026-07-29).

Covers the three defects that made the judge structurally unable to
evaluate a generated app:

1. no dependency install before boot
2. startup detection by probing shared dev ports
3. shell-only termination leaving orphaned servers
"""

import os

from run_manifest import RunManifest


class TestPortAssignment:
    def test_ports_injected_into_env(self, tmp_output_dir):
        rm = RunManifest(tmp_output_dir, backend_port=19300, frontend_port=19301)
        env = rm._build_env()
        assert env["PORT"] == "19300"
        assert env["BACKEND_PORT"] == "19300"
        assert env["VITE_PORT"] == "19301"

    def test_no_ports_means_no_injection(self, tmp_output_dir):
        rm = RunManifest(tmp_output_dir)
        env = rm._build_env()
        assert "VITE_PORT" not in env

    def test_expected_ports_prefers_frontend(self, tmp_output_dir):
        rm = RunManifest(tmp_output_dir, backend_port=19300, frontend_port=19301)
        assert rm._expected_ports() == [19301, 19300]

    def test_expected_ports_empty_without_assignment(self, tmp_output_dir):
        rm = RunManifest(tmp_output_dir)
        assert rm._expected_ports() == []

    def test_dtu_and_ports_coexist(self, tmp_output_dir):
        rm = RunManifest(tmp_output_dir, dtu_url="http://localhost:8001", backend_port=19300)
        env = rm._build_env()
        assert env["DTU_URL"] == "http://localhost:8001"
        assert env["PORT"] == "19300"


class TestBootReport:
    def test_defaults_are_not_live(self, tmp_output_dir):
        rm = RunManifest(tmp_output_dir)
        assert rm.is_live is False
        assert rm.app_url is None
        assert rm.boot_report["install_ran"] is False

    def test_log_dir_inside_output(self, tmp_output_dir):
        rm = RunManifest(tmp_output_dir)
        assert rm.log_dir == os.path.join(tmp_output_dir, ".factory-logs")


class TestInstallPhase:
    def test_noop_when_nothing_to_install(self, tmp_output_dir):
        rm = RunManifest(tmp_output_dir)
        assert rm.install_dependencies() is True
        assert rm.boot_report["install_errors"] == []

    def test_disabled_install_skips(self, tmp_output_dir):
        rm = RunManifest(tmp_output_dir, install_deps=False)
        assert rm.install_dependencies() is True
        assert rm.boot_report["install_ran"] is False

    def test_existing_node_modules_skips_node_install(self, tmp_output_dir):
        with open(os.path.join(tmp_output_dir, "package.json"), "w") as f:
            f.write('{"name": "x"}')
        os.makedirs(os.path.join(tmp_output_dir, "node_modules"), exist_ok=True)

        rm = RunManifest(tmp_output_dir)
        assert rm.install_dependencies() is True
        # No install command ran, so no log file was produced.
        assert not os.path.exists(os.path.join(rm.log_dir, "install-node.log"))

    def test_node_installer_is_a_real_command(self, tmp_output_dir):
        rm = RunManifest(tmp_output_dir)
        cmd = rm._node_installer()
        assert isinstance(cmd, list) and len(cmd) >= 2
        assert cmd[0] in ("bun", "pnpm", "npm", "npm.cmd")
        assert "install" in cmd
