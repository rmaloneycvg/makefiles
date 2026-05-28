"""Shared pytest fixtures for Makefile testing."""
import os
import tempfile
from pathlib import Path

import pytest

from tests.helpers import MAKEFILES_DIR, HOME_MAKEFILE, SHIMS_DIR


@pytest.fixture
def makefile_dir():
    return MAKEFILES_DIR


@pytest.fixture
def home_makefile():
    return HOME_MAKEFILE


@pytest.fixture
def mock_log(tmp_path):
    """Provides a temp file path for mock command logging."""
    return tmp_path / "mock_commands.log"


@pytest.fixture
def mock_env(mock_log):
    """Environment with mock shims on PATH."""
    env = os.environ.copy()
    env["PATH"] = f"{SHIMS_DIR}:{env['PATH']}"
    env["MOCK_LOG"] = str(mock_log)
    return env
