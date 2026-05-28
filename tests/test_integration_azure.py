"""Integration tests for azure/Makefile — creates real resources with cleanup."""
import os
import subprocess
import uuid

import pytest
from tests.helpers import MAKEFILES_DIR, run_make

MAKEFILE = MAKEFILES_DIR / "azure" / "Makefile"
SUBSCRIPTION_ID = os.environ.get("AZURE_SUBSCRIPTION_ID", "")
TENANT_ID = os.environ.get("AZURE_TENANT_ID", "")


def unique_name():
    return f"test-{uuid.uuid4().hex[:8]}"


@pytest.mark.integration
class TestAzureIntegration:
    def test_az_create_and_delete_rg(self):
        """Create a resource group, verify it exists, then delete it."""
        rg = f"rg-{unique_name()}"
        try:
            result = run_make(MAKEFILE, "az-create-rg", {
                "RG_NAME": rg,
                "LOCATION": "eastus",
                "SUBSCRIPTION_ID": SUBSCRIPTION_ID,
                "TENANT_ID": TENANT_ID,
            })
            assert result.returncode == 0, f"az-create-rg failed: {result.stderr}"

            check = subprocess.run(
                ["az", "group", "show", "--name", rg, "-o", "tsv", "--query", "name"],
                capture_output=True, text=True
            )
            assert rg in check.stdout
        finally:
            run_make(MAKEFILE, "az-delete-rg", {"RG_NAME": rg})

    def test_az_list_rg(self):
        """List resource groups — read-only, no cleanup."""
        result = run_make(MAKEFILE, "az-list-rg")
        assert result.returncode == 0
