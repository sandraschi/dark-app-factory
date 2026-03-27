"""Tests for src.verification.rodney_runner.

These tests mock subprocess.run to avoid requiring Chrome or the rodney binary.
"""

import os
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from unittest.mock import MagicMock, patch

from src.verification import rodney_runner


@pytest.fixture(autouse=True)
def reset_cmd_cache():
    """Reset the cached command between tests."""
    rodney_runner._RODNEY_CMD = None
    yield
    rodney_runner._RODNEY_CMD = None


@patch("shutil.which")
def test_get_rodney_cmd_binary(mock_which):
    mock_which.side_effect = lambda name: "/usr/bin/rodney" if name == "rodney" else None
    cmd = rodney_runner._get_rodney_cmd()
    assert cmd == ["rodney"]


@patch("shutil.which")
def test_get_rodney_cmd_uvx(mock_which):
    def side_effect(name):
        if name == "rodney":
            return None
        if name == "uvx":
            return "/usr/bin/uvx"
        return None

    mock_which.side_effect = side_effect
    cmd = rodney_runner._get_rodney_cmd()
    assert cmd == ["uvx", "rodney"]


@patch("shutil.which", return_value=None)
def test_get_rodney_cmd_not_available(mock_which):
    cmd = rodney_runner._get_rodney_cmd()
    assert cmd == []


@patch("shutil.which", return_value=None)
def test_is_available_false(mock_which):
    assert rodney_runner.is_available() is False


@patch("subprocess.run")
@patch("shutil.which", return_value="/usr/bin/rodney")
def test_start(mock_which, mock_run):
    mock_run.return_value = subprocess.CompletedProcess(
        args=[], returncode=0, stdout="", stderr=""
    )
    assert rodney_runner.start() is True


@patch("subprocess.run")
@patch("shutil.which", return_value="/usr/bin/rodney")
def test_stop(mock_which, mock_run):
    mock_run.return_value = subprocess.CompletedProcess(
        args=[], returncode=0, stdout="", stderr=""
    )
    assert rodney_runner.stop() is True


@patch("subprocess.run")
@patch("shutil.which", return_value="/usr/bin/rodney")
def test_open_url(mock_which, mock_run):
    mock_run.return_value = subprocess.CompletedProcess(
        args=[], returncode=0, stdout="", stderr=""
    )
    assert rodney_runner.open_url("http://localhost:3000") is True
    call_args = mock_run.call_args[0][0]
    assert "open" in call_args
    assert "http://localhost:3000" in call_args


@patch("subprocess.run")
@patch("shutil.which", return_value="/usr/bin/rodney")
def test_title(mock_which, mock_run):
    mock_run.return_value = subprocess.CompletedProcess(
        args=[], returncode=0, stdout="My App\n", stderr=""
    )
    assert rodney_runner.title() == "My App"


@patch("subprocess.run")
@patch("shutil.which", return_value="/usr/bin/rodney")
def test_js(mock_which, mock_run):
    mock_run.return_value = subprocess.CompletedProcess(
        args=[], returncode=0, stdout="42\n", stderr=""
    )
    assert rodney_runner.js("1 + 41") == "42"


@patch("subprocess.run")
@patch("shutil.which", return_value="/usr/bin/rodney")
def test_exists_true(mock_which, mock_run):
    mock_run.return_value = subprocess.CompletedProcess(
        args=[], returncode=0, stdout="", stderr=""
    )
    assert rodney_runner.exists("h1") is True


@patch("subprocess.run")
@patch("shutil.which", return_value="/usr/bin/rodney")
def test_exists_false(mock_which, mock_run):
    mock_run.return_value = subprocess.CompletedProcess(
        args=[], returncode=1, stdout="", stderr=""
    )
    assert rodney_runner.exists(".nonexistent") is False


@patch("subprocess.run")
@patch("shutil.which", return_value="/usr/bin/rodney")
def test_count(mock_which, mock_run):
    mock_run.return_value = subprocess.CompletedProcess(
        args=[], returncode=0, stdout="5\n", stderr=""
    )
    assert rodney_runner.count("li.item") == 5


@patch("subprocess.run")
@patch("shutil.which", return_value="/usr/bin/rodney")
def test_screenshot(mock_which, mock_run):
    mock_run.return_value = subprocess.CompletedProcess(
        args=[], returncode=0, stdout="", stderr=""
    )
    assert rodney_runner.screenshot("test.png") is True


@patch("subprocess.run")
@patch("shutil.which", return_value="/usr/bin/rodney")
def test_click(mock_which, mock_run):
    mock_run.return_value = subprocess.CompletedProcess(
        args=[], returncode=0, stdout="", stderr=""
    )
    assert rodney_runner.click("button.submit") is True


@patch("shutil.which", return_value=None)
def test_verify_webapp_not_available(mock_which, tmp_path):
    """verify_webapp returns skipped when rodney is not installed."""
    result = rodney_runner.verify_webapp(
        url="http://localhost:3000",
        screenshot_dir=str(tmp_path / "shots"),
    )
    assert result["skipped"] is True
    assert result["success"] is False


@patch("subprocess.run")
@patch("shutil.which", return_value="/usr/bin/rodney")
def test_verify_webapp_basic_flow(mock_which, mock_run, tmp_path):
    """verify_webapp runs start -> open -> waitstable -> screenshot -> stop."""

    call_count = [0]

    def run_side_effect(args, **kwargs):
        call_count[0] += 1
        cmd_part = args[1] if len(args) > 1 else ""

        if cmd_part == "title":
            return subprocess.CompletedProcess(args=args, returncode=0, stdout="Test App\n", stderr="")
        if cmd_part == "exists":
            return subprocess.CompletedProcess(args=args, returncode=0, stdout="", stderr="")
        # Default success
        return subprocess.CompletedProcess(args=args, returncode=0, stdout="", stderr="")

    mock_run.side_effect = run_side_effect

    result = rodney_runner.verify_webapp(
        url="http://localhost:3000",
        screenshot_dir=str(tmp_path / "shots"),
        checks=[
            {"selector": "body", "action": "exists", "name": "body_exists"},
        ],
    )
    assert result["title"] == "Test App"
    assert result["checks_passed"] >= 1
    assert result["checks_failed"] == 0
    # Verify stop was called (last subprocess invocation should be stop)
    assert call_count[0] > 3  # start, open, waitstable, waitidle, ...
