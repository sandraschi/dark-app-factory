"""Tests for src.verification.showboat_runner.

These tests mock subprocess.run to avoid requiring the actual showboat binary.
"""

# ruff: noqa: E402
import os
import subprocess
import sys

import pytest

# Ensure project root is on path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from unittest.mock import patch

from src.verification import showboat_runner


@pytest.fixture(autouse=True)
def reset_cmd_cache():
    """Reset the cached command between tests."""
    showboat_runner._SHOWBOAT_CMD = None
    yield
    showboat_runner._SHOWBOAT_CMD = None


@patch("shutil.which")
def test_get_showboat_cmd_binary_on_path(mock_which):
    """When showboat is on PATH, use it directly."""
    mock_which.side_effect = lambda name: (
        "/usr/bin/showboat" if name == "showboat" else None
    )
    cmd = showboat_runner._get_showboat_cmd()
    assert cmd == ["showboat"]


@patch("shutil.which")
def test_get_showboat_cmd_uvx_fallback(mock_which):
    """When showboat is NOT on PATH but uvx is, use uvx showboat."""

    def which_side_effect(name):
        if name == "showboat":
            return None
        if name == "uvx":
            return "/usr/bin/uvx"
        return None

    mock_which.side_effect = which_side_effect
    cmd = showboat_runner._get_showboat_cmd()
    assert cmd == ["uvx", "showboat"]


@patch("shutil.which", return_value=None)
def test_get_showboat_cmd_not_available(mock_which):
    """When neither showboat nor uvx is found, return empty list."""
    cmd = showboat_runner._get_showboat_cmd()
    assert cmd == []


@patch("shutil.which", return_value=None)
def test_is_available_false(mock_which):
    """is_available returns False when showboat is not found."""
    assert showboat_runner.is_available() is False


@patch("subprocess.run")
@patch("shutil.which", return_value="/usr/bin/showboat")
def test_is_available_true(mock_which, mock_run):
    """is_available returns True when showboat --version exits 0."""
    mock_run.return_value = subprocess.CompletedProcess(
        args=["showboat", "--version"], returncode=0, stdout="0.1.0", stderr=""
    )
    assert showboat_runner.is_available() is True


@patch("subprocess.run")
@patch("shutil.which", return_value="/usr/bin/showboat")
def test_init(mock_which, mock_run):
    """init() calls showboat init with correct args."""
    mock_run.return_value = subprocess.CompletedProcess(
        args=[], returncode=0, stdout="", stderr=""
    )
    result = showboat_runner.init("demo.md", "My Title")
    assert result is True
    mock_run.assert_called_once()
    call_args = mock_run.call_args[0][0]
    assert "init" in call_args
    assert "demo.md" in call_args
    assert "My Title" in call_args


@patch("subprocess.run")
@patch("shutil.which", return_value="/usr/bin/showboat")
def test_note(mock_which, mock_run):
    """note() appends commentary text."""
    mock_run.return_value = subprocess.CompletedProcess(
        args=[], returncode=0, stdout="", stderr=""
    )
    result = showboat_runner.note("demo.md", "Some commentary")
    assert result is True


@patch("subprocess.run")
@patch("shutil.which", return_value="/usr/bin/showboat")
def test_exec_cmd_success(mock_which, mock_run):
    """exec_cmd() returns (True, stdout) on success."""
    mock_run.return_value = subprocess.CompletedProcess(
        args=[], returncode=0, stdout="hello world\n", stderr=""
    )
    success, output = showboat_runner.exec_cmd("demo.md", "bash", "echo hello world")
    assert success is True
    assert "hello world" in output


@patch("subprocess.run")
@patch("shutil.which", return_value="/usr/bin/showboat")
def test_exec_cmd_failure(mock_which, mock_run):
    """exec_cmd() returns (False, stdout) when command fails."""
    mock_run.return_value = subprocess.CompletedProcess(
        args=[], returncode=1, stdout="error output\n", stderr="error"
    )
    success, output = showboat_runner.exec_cmd("demo.md", "bash", "false")
    assert success is False
    assert "error output" in output


@patch("subprocess.run")
@patch("shutil.which", return_value="/usr/bin/showboat")
def test_verify_pass(mock_which, mock_run):
    """verify() returns (True, output) when all blocks match."""
    mock_run.return_value = subprocess.CompletedProcess(
        args=[], returncode=0, stdout="All outputs match.\n", stderr=""
    )
    passed, output = showboat_runner.verify("demo.md")
    assert passed is True


@patch("subprocess.run")
@patch("shutil.which", return_value="/usr/bin/showboat")
def test_verify_fail(mock_which, mock_run):
    """verify() returns (False, diff) when outputs differ."""
    mock_run.return_value = subprocess.CompletedProcess(
        args=[], returncode=1, stdout="", stderr="Diff: -old +new\n"
    )
    passed, output = showboat_runner.verify("demo.md")
    assert passed is False
    assert "Diff" in output


@patch("subprocess.run")
@patch("shutil.which", return_value="/usr/bin/showboat")
def test_pop(mock_which, mock_run):
    """pop() removes the last entry."""
    mock_run.return_value = subprocess.CompletedProcess(
        args=[], returncode=0, stdout="", stderr=""
    )
    assert showboat_runner.pop("demo.md") is True


@patch("shutil.which", return_value=None)
def test_create_build_demo_not_available(mock_which, tmp_path):
    """create_build_demo returns None when showboat is not installed."""
    result = showboat_runner.create_build_demo(
        output_dir=str(tmp_path),
        demo_dir=str(tmp_path / "demos"),
        project_name="test",
    )
    assert result is None
