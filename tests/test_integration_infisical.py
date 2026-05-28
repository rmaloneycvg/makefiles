"""Integration tests for infisical/Makefile — requires running Infisical instance."""
import pytest
from tests.helpers import MAKEFILES_DIR, run_make

MAKEFILE = MAKEFILES_DIR / "infisical" / "Makefile"


@pytest.mark.integration
class TestInfisicalIntegration:
    def test_infisical_export(self):
        """Export secrets in dotenv format — read-only."""
        result = run_make(MAKEFILE, "infisical-export", {"INFISICAL_ENV": "dev"})
        assert result.returncode == 0 or "login" in result.stderr.lower()

    def test_infisical_manifest(self):
        """Generate manifest file — writes infisical.example."""
        result = run_make(MAKEFILE, "infisical-manifest", {"INFISICAL_ENV": "dev"})
        assert result.returncode == 0 or "login" in result.stderr.lower()
