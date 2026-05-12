#!/usr/bin/env python3
"""
Assign Entra ID groups to app roles via Microsoft Graph.

Looks up role IDs from the app registration and group IDs by display name,
then POSTs appRoleAssignedTo for each (group, role) pair.

Usage:
    assign_group_roles.py --client-id <app-client-id> --pair "API-Readers:API.Read" "API-Writers:API.Write"
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys


def az(*args: str) -> str:
    """Run az CLI and return stdout. Raises on failure."""
    result = subprocess.run(
        ["az", *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def get_sp_id(client_id: str) -> str:
    output = az(
        "ad", "sp", "list",
        "--filter", f"appId eq '{client_id}'",
        "--query", "[0].id",
        "-o", "tsv",
    )
    if not output:
        raise SystemExit(f"No service principal found for app client ID '{client_id}'. "
                         "Did the app registration get created?")
    return output


def get_app_roles(client_id: str) -> dict[str, str]:
    output = az(
        "ad", "app", "show",
        "--id", client_id,
        "--query", "appRoles",
    )
    roles = json.loads(output) if output else []
    return {role["value"]: role["id"] for role in roles}


def get_group_id(display_name: str) -> str:
    output = az(
        "ad", "group", "show",
        "--group", display_name,
        "--query", "id",
        "-o", "tsv",
    )
    if not output:
        raise SystemExit(f"Group '{display_name}' not found.")
    return output


def assign(sp_id: str, principal_id: str, role_id: str) -> None:
    body = json.dumps({
        "principalId": principal_id,
        "resourceId": sp_id,
        "appRoleId": role_id,
    })
    az(
        "rest",
        "--method", "POST",
        "--uri", f"https://graph.microsoft.com/v1.0/servicePrincipals/{sp_id}/appRoleAssignedTo",
        "--body", body,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--client-id", required=True, help="App registration client ID (appId)")
    parser.add_argument(
        "--pair",
        nargs="+",
        required=True,
        help='Group-to-role pairs: "GroupName:RoleValue"',
    )
    args = parser.parse_args()

    sp_id = get_sp_id(args.client_id)
    role_map = get_app_roles(args.client_id)

    for pair in args.pair:
        if ":" not in pair:
            parser.error(f"Invalid pair (expected GroupName:RoleValue): {pair}")
        group_name, role_value = pair.split(":", 1)
        if role_value not in role_map:
            raise SystemExit(f"Role '{role_value}' not defined on app registration. "
                             f"Available: {list(role_map)}")
        group_id = get_group_id(group_name)
        assign(sp_id, group_id, role_map[role_value])
        print(f"✅ {group_name} → {role_value}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
