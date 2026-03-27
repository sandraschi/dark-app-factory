"""Shared fixtures for Dark App Factory tests."""

import os
import sys

import pytest

# Ensure project root is on sys.path for all tests
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
if os.path.join(ROOT_DIR, "src") not in sys.path:
    sys.path.insert(1, os.path.join(ROOT_DIR, "src"))


@pytest.fixture
def tmp_output_dir(tmp_path):
    """Provide a temporary output directory for tests."""
    out = tmp_path / "output_001"
    out.mkdir()
    return str(out)
