#!/usr/bin/env python3
"""
Look up Azure Policy definition IDs by display name (avoids hardcoding GUIDs).

Usage:
    policy_defs.py lookup "Require a tag on resource groups"
    policy_defs.py resolve --alias required-tag-on-rg
    policy_defs.py resolve --alias allowed-locations
    policy_defs.py resolve --alias kv-key-rotation-interval

Aliases map to well-known Azure built-in policy display names. If Microsoft
renames a policy, update the alias mapping in one place.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys


# Map of user-friendly aliases to Azure built-in policy display names.
# Display names are stable but easier to inspect in portal than GUIDs.
POLICY_ALIASES: dict[str, str] = {
    "required-tag-on-rg": "Require a tag on resource groups",
    "allowed-locations": "Allowed locations",
    "kv-key-rotation-interval": "Keys should have a rotation policy ensuring that their rotation is scheduled within the specified number of days after creation.",
    "kv-secret-expiration": "Key Vault secrets should have an expiration date",
    "storage-secure-transfer": "Secure transfer to storage accounts should be enabled",
    "sql-auditing": "Auditing on SQL server should be enabled",
}


def az(*args: str) -> str:
    result = subprocess.run(["az", *args], check=True, capture_output=True, text=True)
    return result.stdout.strip()


def find_by_display_name(display_name: str) -> str:
    output = az(
        "policy", "definition", "list",
        "--query", f"[?displayName=='{display_name}'].id",
        "-o", "tsv",
    )
    if not output:
        raise SystemExit(f"No built-in policy definition found with display name: {display_name!r}")
    # Can return multiple lines if duplicates; take the first built-in one
    for line in output.splitlines():
        if "/providers/Microsoft.Authorization/policyDefinitions/" in line:
            return line.strip()
    return output.splitlines()[0].strip()


def resolve_alias(alias: str) -> str:
    if alias not in POLICY_ALIASES:
        raise SystemExit(f"Unknown alias '{alias}'. Available: {list(POLICY_ALIASES)}")
    return find_by_display_name(POLICY_ALIASES[alias])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_lookup = sub.add_parser("lookup", help="Look up policy by exact display name")
    p_lookup.add_argument("display_name")

    p_resolve = sub.add_parser("resolve", help="Resolve a friendly alias to a policy ID")
    p_resolve.add_argument("--alias", required=True, choices=list(POLICY_ALIASES))

    sub.add_parser("list-aliases", help="List known aliases")

    args = parser.parse_args()

    if args.cmd == "lookup":
        print(find_by_display_name(args.display_name))
    elif args.cmd == "resolve":
        print(resolve_alias(args.alias))
    elif args.cmd == "list-aliases":
        for alias, name in POLICY_ALIASES.items():
            print(f"{alias}\t{name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
