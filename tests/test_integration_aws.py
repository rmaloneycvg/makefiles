"""Integration tests for aws/Makefile — creates real resources with cleanup."""
import uuid

import pytest
from tests.helpers import MAKEFILES_DIR, run_make

MAKEFILE = MAKEFILES_DIR / "aws" / "Makefile"
AWS_REGION = "us-east-1"


def unique_name():
    return f"test-{uuid.uuid4().hex[:8]}"


@pytest.mark.integration
class TestAwsIntegration:
    def test_aws_create_and_delete_secret(self):
        """Create a secret, verify, then force-delete it."""
        name = unique_name()
        try:
            result = run_make(MAKEFILE, "aws-create-secret", {
                "n": name,
                "v": "integration-test-value",
                "AWS_REGION": AWS_REGION,
            })
            assert result.returncode == 0, f"aws-create-secret failed: {result.stderr}"

            show = run_make(MAKEFILE, "aws-show-secret", {"n": name, "AWS_REGION": AWS_REGION})
            assert "integration-test-value" in show.stdout
        finally:
            run_make(MAKEFILE, "aws-purge-secret", {"n": name, "AWS_REGION": AWS_REGION})

    def test_aws_show_account(self):
        """Show account info — read-only."""
        result = run_make(MAKEFILE, "aws-show-account", {"AWS_REGION": AWS_REGION})
        assert result.returncode == 0
        assert "Account:" in result.stdout

    def test_aws_list_secrets(self):
        """List secrets — read-only."""
        result = run_make(MAKEFILE, "aws-list-secrets", {"AWS_REGION": AWS_REGION})
        assert result.returncode == 0
