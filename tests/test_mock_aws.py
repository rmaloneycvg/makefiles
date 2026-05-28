"""Mock/stub tests for aws/Makefile — validates command construction."""
import pytest
from tests.helpers import MAKEFILES_DIR, SHIMS_DIR, run_make
import os


MAKEFILE = MAKEFILES_DIR / "aws" / "Makefile"


def mock_env(tmp_path):
    env = os.environ.copy()
    env["PATH"] = f"{SHIMS_DIR}:{env['PATH']}"
    env["MOCK_LOG"] = str(tmp_path / "cmds.log")
    return env


@pytest.mark.mock
class TestAwsMock:
    def test_aws_create_secret(self, tmp_path):
        env = mock_env(tmp_path)
        result = run_make(MAKEFILE, "aws-create-secret", {"n": "my-secret", "v": "my-value", "AWS_REGION": "us-east-1"}, env=env)
        assert result.returncode == 0
        log = (tmp_path / "cmds.log").read_text()
        assert "aws secretsmanager create-secret" in log
        assert "--name my-secret" in log

    def test_aws_create_s3(self, tmp_path):
        env = mock_env(tmp_path)
        result = run_make(MAKEFILE, "aws-create-s3", {"BUCKET_NAME": "test-bkt", "env": "dev", "use": "web", "AWS_REGION": "us-east-1"}, env=env)
        assert result.returncode == 0
        log = (tmp_path / "cmds.log").read_text()
        assert "aws s3api create-bucket" in log
        assert "--bucket test-bkt" in log

    def test_aws_create_lambda_role(self, tmp_path):
        env = mock_env(tmp_path)
        result = run_make(MAKEFILE, "aws-create-lambda-role", {"LAMBDA_ROLE_NAME": "role-test", "AWS_REGION": "us-east-1"}, env=env)
        assert result.returncode == 0
        log = (tmp_path / "cmds.log").read_text()
        assert "aws iam create-role" in log
        assert "--role-name role-test" in log

    def test_aws_create_user_pool(self, tmp_path):
        env = mock_env(tmp_path)
        result = run_make(MAKEFILE, "aws-create-user-pool", {"POOL_NAME": "auth-test", "AWS_REGION": "us-east-1"}, env=env)
        assert result.returncode == 0
        log = (tmp_path / "cmds.log").read_text()
        assert "aws cognito-idp create-user-pool" in log
        assert "--pool-name auth-test" in log

    def test_aws_create_api_gw(self, tmp_path):
        env = mock_env(tmp_path)
        result = run_make(MAKEFILE, "aws-create-api-gw", {"API_NAME": "agw-test", "AWS_REGION": "us-east-1"}, env=env)
        assert result.returncode == 0
        log = (tmp_path / "cmds.log").read_text()
        assert "aws apigatewayv2 create-api" in log
        assert "--name agw-test" in log

    def test_aws_delete_secret(self, tmp_path):
        env = mock_env(tmp_path)
        result = run_make(MAKEFILE, "aws-delete-secret", {"n": "my-secret", "AWS_REGION": "us-east-1"}, env=env)
        assert result.returncode == 0
        log = (tmp_path / "cmds.log").read_text()
        assert "aws secretsmanager delete-secret" in log
        assert "--secret-id my-secret" in log
