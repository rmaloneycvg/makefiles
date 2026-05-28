"""Dry-run tests for utilities/Makefile."""
import pytest
from tests.helpers import MAKEFILES_DIR, dry_run, extract_phony_targets

MAKEFILE = MAKEFILES_DIR / "utilities" / "Makefile"
TARGETS = extract_phony_targets(MAKEFILE)


@pytest.mark.dryrun
@pytest.mark.parametrize("target", TARGETS)
def test_dryrun(target):
    result = dry_run(MAKEFILE, target)
    assert result.returncode == 0, f"{target} failed:\n{result.stderr}"
