"""Shared helpers for Makefile tests."""
import os
import re
import subprocess
from pathlib import Path

MAKEFILES_DIR = Path(__file__).parent.parent
HOME_MAKEFILE = Path.home() / "Makefile"
SHIMS_DIR = MAKEFILES_DIR / "tests" / "shims"

# Default variable stubs to satisfy required params in dry-run
DEFAULT_VARS = {
    "n": "test",
    "env": "dev",
    "q": "test",
    "key": "TEST_KEY",
    "v": "1.0.0",
    "b": "main",
    "m": "test message",
    "path": "/test",
    "role": "API.Read",
    "calls": "100",
    "period": "60",
    "origin": "http://localhost",
    "dir": "./build",
    "swagger": "http://example.com/swagger.json",
    "spec": "spec.json",
    "username": "test@test.com",
    "group": "Reader",
    "stage": "dev",
    "metric": "Errors",
    "pk": "id",
    "rate": "10",
    "burst": "20",
    "weight": "50",
    "service": "s3",
    "runtime": "python",
    "method": "GET",
    "use": "web",
    "DOMAIN": "example.com",
    "HOSTED_ZONE_ID": "Z123",
    "BUDGET_AMOUNT": "50",
    "BUDGET_EMAIL": "test@test.com",
    "BUCKET_NAME": "test-bucket",
    "FUNC_NAME": "fn-test",
    "LAMBDA_ROLE_NAME": "role-test",
    "TABLE_NAME": "ddb-test",
    "DB_NAME": "sql-test",
    "REDIS_NAME": "redis-test",
    "VPC_NAME": "vnet-test",
    "API_NAME": "agw-test",
    "POOL_NAME": "auth-test",
    "CLIENT_NAME": "app-test",
    "DOMAIN_PREFIX": "testdomain",
    "DB_SUBNET_GROUP": "dbsnet-test",
    "CACHE_SUBNET_GROUP": "csnet-test",
    "CICD_USER": "sp-test-cicd",
    "KV_NAME": "kv-test",
    "callback": "http://localhost/callback",
}


def extract_phony_targets(makefile_path: Path) -> list[str]:
    """Extract all .PHONY target names from a Makefile."""
    content = makefile_path.read_text()
    targets = []
    for match in re.finditer(r"\.PHONY:\s*(.+)", content):
        for t in match.group(1).split():
            if t != "help":
                targets.append(t)
    return sorted(set(targets))


def dry_run(makefile: Path, target: str, extra_vars: dict | None = None, env: dict | None = None) -> subprocess.CompletedProcess:
    """Run make -n on a target with default variable stubs."""
    vars_to_use = dict(DEFAULT_VARS)
    if extra_vars:
        vars_to_use.update(extra_vars)

    cmd = ["make", "-n", "-f", str(makefile), target]
    for k, val in vars_to_use.items():
        cmd.append(f"{k}={val}")

    run_env = env if env else os.environ.copy()
    run_env["PATH"] = f"{SHIMS_DIR}:{run_env.get('PATH', '')}"
    run_env.setdefault("MOCK_LOG", "/tmp/mock_dryrun.log")

    return subprocess.run(cmd, capture_output=True, text=True, timeout=30, env=run_env)


def run_make(makefile: Path, target: str, extra_vars: dict | None = None, env: dict | None = None) -> subprocess.CompletedProcess:
    """Run make target for real (used in mock/integration tests)."""
    cmd = ["make", "-f", str(makefile), target]
    vars_to_use = extra_vars or {}
    for k, val in vars_to_use.items():
        cmd.append(f"{k}={val}")

    run_env = env if env else os.environ.copy()
    return subprocess.run(cmd, capture_output=True, text=True, timeout=120, env=run_env)
