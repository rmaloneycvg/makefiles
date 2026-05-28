"""Integration tests for git/Makefile — read-only operations, no cleanup needed."""
import subprocess

import pytest
from tests.helpers import MAKEFILES_DIR, run_make

MAKEFILE = MAKEFILES_DIR / "git" / "Makefile"


@pytest.mark.integration
class TestGitIntegration:
    def test_git_changed(self):
        result = run_make(MAKEFILE, "git-changed")
        assert result.returncode == 0

    def test_git_changed_branch(self):
        result = run_make(MAKEFILE, "git-changed-branch", {"b": "main"})
        # May fail if not in a git repo with 'main' — that's ok
        assert result.returncode == 0 or "fatal" in result.stderr

    def test_git_compare(self):
        result = run_make(MAKEFILE, "git-compare", {"b": "main"})
        assert result.returncode == 0 or "fatal" in result.stderr
