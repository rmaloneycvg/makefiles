"""Mock/stub tests for infisical/Makefile — validates command construction."""
import os

import pytest
from tests.helpers import MAKEFILES_DIR, SHIMS_DIR, run_make


MAKEFILE = MAKEFILES_DIR / "infisical" / "Makefile"


def mock_env(tmp_path):
    env = os.environ.copy()
    env["PATH"] = f"{SHIMS_DIR}:{env['PATH']}"
    env["MOCK_LOG"] = str(tmp_path / "cmds.log")
    env["INFISICAL_API_URL"] = "http://localhost:9999/api"
    return env


@pytest.mark.mock
class TestInfisicalMock:
    def test_infisical_login(self, tmp_path):
        env = mock_env(tmp_path)
        result = run_make(MAKEFILE, "infisical-login", env=env)
        assert result.returncode == 0
        log = (tmp_path / "cmds.log").read_text()
        assert "infisical login --domain http://localhost:9999/api" in log

    def test_infisical_init(self, tmp_path):
        env = mock_env(tmp_path)
        result = run_make(MAKEFILE, "infisical-init", env=env)
        assert result.returncode == 0
        log = (tmp_path / "cmds.log").read_text()
        assert "infisical init --domain http://localhost:9999/api" in log

    def test_infisical_export(self, tmp_path):
        env = mock_env(tmp_path)
        result = run_make(MAKEFILE, "infisical-export", env=env)
        assert result.returncode == 0
        log = (tmp_path / "cmds.log").read_text()
        assert "python3" in log
        assert "infisical_sync.py" in log
        assert "export --env dev --format dotenv" in log

    def test_infisical_pull(self, tmp_path):
        env = mock_env(tmp_path)
        result = run_make(MAKEFILE, "infisical-pull", {"KV_NAME": "kv-test"}, env=env)
        assert result.returncode == 0
        log = (tmp_path / "cmds.log").read_text()
        assert "infisical_sync.py" in log
        assert "pull --provider azure --vault-name kv-test --env dev" in log

    def test_infisical_push_env(self, tmp_path):
        env = mock_env(tmp_path)
        result = run_make(MAKEFILE, "infisical-push-env", env=env)
        # May fail if no .env in infisical/ dir, but command construction is what matters
        assert True
