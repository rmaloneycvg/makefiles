"""Mock/stub tests for azure/Makefile — validates command construction."""
import pytest
from tests.helpers import MAKEFILES_DIR, SHIMS_DIR, run_make
import os


MAKEFILE = MAKEFILES_DIR / "azure" / "Makefile"


def mock_env(tmp_path):
    env = os.environ.copy()
    env["PATH"] = f"{SHIMS_DIR}:{env['PATH']}"
    env["MOCK_LOG"] = str(tmp_path / "cmds.log")
    return env


@pytest.mark.mock
class TestAzureMock:
    def test_az_create_rg(self, tmp_path):
        env = mock_env(tmp_path)
        result = run_make(MAKEFILE, "az-create-rg", {"RG_NAME": "rg-testproj", "LOCATION": "westus2"}, env=env)
        assert result.returncode == 0
        log = (tmp_path / "cmds.log").read_text()
        assert "az group create --name rg-testproj --location westus2" in log

    def test_az_create_kv(self, tmp_path):
        env = mock_env(tmp_path)
        result = run_make(MAKEFILE, "az-create-kv", {"KV_NAME": "kv-testproj", "RG_NAME": "rg-testproj", "LOCATION": "eastus"}, env=env)
        assert result.returncode == 0
        log = (tmp_path / "cmds.log").read_text()
        assert "az keyvault create --name kv-testproj" in log

    def test_az_create_storage(self, tmp_path):
        env = mock_env(tmp_path)
        result = run_make(MAKEFILE, "az-create-storage", {"env": "dev", "use": "web", "STORAGE_NAME": "sttest123"}, env=env)
        assert result.returncode == 0
        log = (tmp_path / "cmds.log").read_text()
        assert "az storage account create" in log
        assert "--name sttest123" in log

    def test_az_create_funcapp(self, tmp_path):
        env = mock_env(tmp_path)
        result = run_make(MAKEFILE, "az-create-funcapp", {"env": "dev", "runtime": "python", "FUNC_NAME": "fn-test", "STORAGE_NAME": "sttest"}, env=env)
        assert result.returncode == 0
        log = (tmp_path / "cmds.log").read_text()
        assert "az functionapp create" in log
        assert "--name fn-test" in log

    def test_az_create_sql(self, tmp_path):
        env = mock_env(tmp_path)
        result = run_make(MAKEFILE, "az-create-sql", {"env": "dev", "SQL_SERVER_NAME": "sql-test", "SQL_DB_NAME": "sqldb-test", "KV_NAME": "kv-test"}, env=env)
        assert result.returncode == 0
        log = (tmp_path / "cmds.log").read_text()
        assert "az sql server create --name sql-test" in log

    def test_az_delete_rg(self, tmp_path):
        env = mock_env(tmp_path)
        result = run_make(MAKEFILE, "az-delete-rg", {"RG_NAME": "rg-testproj"}, env=env)
        assert result.returncode == 0
        log = (tmp_path / "cmds.log").read_text()
        assert "az group delete --name rg-testproj --yes --no-wait" in log
