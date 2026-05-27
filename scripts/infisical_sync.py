#!/usr/bin/env python3
"""
Sync secrets between Infisical and cloud providers (Azure Key Vault / AWS Secrets Manager).

Workflow:
    pull   — Cloud → Infisical (import secrets from cloud into Infisical project)
    push   — Infisical → Cloud (export secrets from Infisical to cloud vault)
    export — Infisical → stdout (key=value pairs for shell eval or .env)
    manifest — Generate infisical.example from current Infisical secrets (names only)

Requires:
    - infisical CLI (https://infisical.com/docs/cli/overview)
    - az CLI (for Azure) or aws CLI (for AWS)
    - INFISICAL_TOKEN or logged-in infisical session

Usage:
    infisical_sync.py pull --provider azure --vault-name my-kv --env dev
    infisical_sync.py pull --provider aws --region us-east-1 --env dev
    infisical_sync.py push --provider azure --vault-name my-kv --env dev
    infisical_sync.py push --provider aws --region us-east-1 --env dev
    infisical_sync.py export --env dev --format dotenv
    infisical_sync.py export --env dev --format shell
    infisical_sync.py manifest --env dev --out infisical.example
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def run(cmd: list[str], check: bool = True) -> str:
    result = subprocess.run(cmd, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"Error running: {' '.join(cmd)}", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        sys.exit(1)
    return result.stdout.strip()


# --- Infisical operations ---

def infisical_list(env: str, project_id: str | None = None) -> list[dict]:
    """List all secrets from Infisical for a given environment."""
    cmd = ["infisical", "secrets", "--env", env, "--plain", "--silent"]
    if project_id:
        cmd += ["--projectId", project_id]
    output = run(cmd + ["--output", "json"])
    if not output:
        return []
    return json.loads(output)


def infisical_set(key: str, value: str, env: str, project_id: str | None = None) -> None:
    """Set a secret in Infisical."""
    cmd = ["infisical", "secrets", "set", f"{key}={value}", "--env", env, "--silent"]
    if project_id:
        cmd += ["--projectId", project_id]
    run(cmd)


def infisical_export(env: str, fmt: str = "dotenv", project_id: str | None = None) -> str:
    """Export secrets from Infisical in the given format."""
    cmd = ["infisical", "export", "--env", env, "--format", fmt, "--silent"]
    if project_id:
        cmd += ["--projectId", project_id]
    return run(cmd)


# --- Azure Key Vault operations ---

def azure_list_secrets(vault_name: str) -> dict[str, str]:
    """List all secrets from Azure Key Vault (name → value)."""
    names_json = run(["az", "keyvault", "secret", "list",
                      "--vault-name", vault_name, "--query", "[].name", "-o", "json"])
    names = json.loads(names_json) if names_json else []
    secrets = {}
    for name in names:
        value = run(["az", "keyvault", "secret", "show",
                     "--vault-name", vault_name, "--name", name,
                     "--query", "value", "-o", "tsv"])
        # Key Vault uses hyphens, env vars use underscores
        env_key = name.replace("-", "_").upper()
        secrets[env_key] = value
    return secrets


def azure_set_secret(vault_name: str, name: str, value: str) -> None:
    """Set a secret in Azure Key Vault."""
    # Convert env-var style to Key Vault style (underscores → hyphens, lowercase)
    kv_name = name.replace("_", "-").lower()
    run(["az", "keyvault", "secret", "set",
         "--vault-name", vault_name, "--name", kv_name, "--value", value],
        check=True)


# --- AWS Secrets Manager operations ---

def aws_list_secrets(region: str, prefix: str = "") -> dict[str, str]:
    """List all secrets from AWS Secrets Manager (name → value)."""
    names_json = run(["aws", "secretsmanager", "list-secrets",
                      "--region", region, "--query", "SecretList[].Name", "--output", "json"])
    names = json.loads(names_json) if names_json else []
    secrets = {}
    for name in names:
        if prefix and not name.startswith(prefix):
            continue
        value = run(["aws", "secretsmanager", "get-secret-value",
                     "--secret-id", name, "--region", region,
                     "--query", "SecretString", "--output", "text"])
        env_key = name.replace("-", "_").replace("/", "_").upper()
        secrets[env_key] = value
    return secrets


def aws_set_secret(region: str, name: str, value: str) -> None:
    """Create or update a secret in AWS Secrets Manager."""
    sm_name = name.replace("_", "-").lower()
    # Try update first, create if not found
    result = subprocess.run(
        ["aws", "secretsmanager", "put-secret-value",
         "--secret-id", sm_name, "--secret-string", value,
         "--region", region],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        run(["aws", "secretsmanager", "create-secret",
             "--name", sm_name, "--secret-string", value,
             "--region", region])


# --- Commands ---

def cmd_pull(args) -> int:
    """Pull secrets from cloud provider into Infisical."""
    print(f"Pulling secrets from {args.provider} → Infisical ({args.env})...")

    if args.provider == "azure":
        if not args.vault_name:
            print("--vault-name is required for Azure", file=sys.stderr)
            return 1
        secrets = azure_list_secrets(args.vault_name)
    elif args.provider == "aws":
        secrets = aws_list_secrets(args.region, args.prefix)
    else:
        print(f"Unknown provider: {args.provider}", file=sys.stderr)
        return 1

    count = 0
    for key, value in secrets.items():
        infisical_set(key, value, args.env, args.project_id)
        count += 1
        print(f"  ✓ {key}")

    print(f"✅ Pulled {count} secrets into Infisical ({args.env}).")
    return 0


def cmd_push(args) -> int:
    """Push secrets from Infisical to cloud provider."""
    print(f"Pushing secrets from Infisical ({args.env}) → {args.provider}...")

    secrets = infisical_list(args.env, args.project_id)
    count = 0
    for secret in secrets:
        key = secret.get("key") or secret.get("secretKey", "")
        value = secret.get("value") or secret.get("secretValue", "")
        if not key or not value:
            continue

        if args.provider == "azure":
            if not args.vault_name:
                print("--vault-name is required for Azure", file=sys.stderr)
                return 1
            azure_set_secret(args.vault_name, key, value)
        elif args.provider == "aws":
            aws_set_secret(args.region, key, value)
        else:
            print(f"Unknown provider: {args.provider}", file=sys.stderr)
            return 1

        count += 1
        print(f"  ✓ {key}")

    print(f"✅ Pushed {count} secrets to {args.provider}.")
    return 0


def cmd_export(args) -> int:
    """Export secrets from Infisical to stdout."""
    output = infisical_export(args.env, args.format, args.project_id)
    print(output)
    return 0


def cmd_manifest(args) -> int:
    """Generate infisical.example file (secret names + descriptions, no values)."""
    secrets = infisical_list(args.env, args.project_id)
    lines = [
        "# infisical.example",
        "# Secret names managed by Infisical for this project.",
        "# This file is committed to git. DO NOT add values.",
        f"# Environment: {args.env}",
        "#",
        "# To pull secrets locally: make pull-secrets env={env}",
        "# To push secrets to cloud: make push-secrets env={env}",
        "",
    ]
    for secret in sorted(secrets, key=lambda s: s.get("key", s.get("secretKey", ""))):
        key = secret.get("key") or secret.get("secretKey", "")
        comment = secret.get("comment", "")
        if comment:
            lines.append(f"# {comment}")
        lines.append(f"{key}=")

    content = "\n".join(lines) + "\n"
    out_path = Path(args.out) if args.out else None
    if out_path:
        out_path.write_text(content)
        print(f"✅ Generated {out_path} ({len(secrets)} secrets)")
    else:
        print(content)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--project-id", help="Infisical project ID (or set INFISICAL_PROJECT_ID)")
    sub = parser.add_subparsers(dest="cmd", required=True)

    # pull
    p_pull = sub.add_parser("pull", help="Cloud → Infisical")
    p_pull.add_argument("--provider", required=True, choices=["azure", "aws"])
    p_pull.add_argument("--vault-name", help="Azure Key Vault name")
    p_pull.add_argument("--region", default="us-east-1", help="AWS region")
    p_pull.add_argument("--prefix", default="", help="AWS secret name prefix filter")
    p_pull.add_argument("--env", default="dev", help="Infisical environment")

    # push
    p_push = sub.add_parser("push", help="Infisical → Cloud")
    p_push.add_argument("--provider", required=True, choices=["azure", "aws"])
    p_push.add_argument("--vault-name", help="Azure Key Vault name")
    p_push.add_argument("--region", default="us-east-1", help="AWS region")
    p_push.add_argument("--env", default="dev", help="Infisical environment")

    # export
    p_export = sub.add_parser("export", help="Infisical → stdout")
    p_export.add_argument("--env", default="dev")
    p_export.add_argument("--format", default="dotenv", choices=["dotenv", "json", "yaml", "csv"])

    # manifest
    p_manifest = sub.add_parser("manifest", help="Generate infisical.example")
    p_manifest.add_argument("--env", default="dev")
    p_manifest.add_argument("--out", default="infisical.example")

    args = parser.parse_args()
    args.project_id = args.project_id or None

    dispatch = {"pull": cmd_pull, "push": cmd_push, "export": cmd_export, "manifest": cmd_manifest}
    return dispatch[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
