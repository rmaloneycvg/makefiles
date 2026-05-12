#!/usr/bin/env python3
"""
Generate Entra ID app-roles JSON for `az ad app update --app-roles`.

Each role gets a unique UUID. Output is an array of role objects.

Usage:
    app_roles.py --out roles.json Read:API.Read:"Read access" Write:API.Write:"Write access"
    app_roles.py --out roles.json --standard   # emits Read/Write/Admin defaults
"""
from __future__ import annotations

import argparse
import json
import sys
import uuid
from pathlib import Path


STANDARD_ROLES = [
    ("Read", "API.Read", "Read access"),
    ("Write", "API.Write", "Write access"),
    ("Admin", "API.Admin", "Full admin access"),
]


def build_role(display_name: str, value: str, description: str) -> dict:
    return {
        "allowedMemberTypes": ["User", "Application"],
        "displayName": display_name,
        "description": description,
        "isEnabled": True,
        "value": value,
        "id": str(uuid.uuid4()),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "roles",
        nargs="*",
        help='Roles in "DisplayName:value:Description" format',
    )
    parser.add_argument("--standard", action="store_true", help="Use standard Read/Write/Admin roles")
    parser.add_argument("--out", help="Output file (default stdout)")
    args = parser.parse_args()

    if args.standard:
        specs = STANDARD_ROLES
    else:
        specs = []
        for r in args.roles:
            parts = r.split(":", 2)
            if len(parts) != 3:
                parser.error(f"Invalid role spec (expected Name:value:Description): {r}")
            specs.append(tuple(parts))  # type: ignore[arg-type]

    roles = [build_role(name, value, desc) for name, value, desc in specs]
    output = json.dumps(roles, indent=2)

    if args.out:
        Path(args.out).write_text(output)
    else:
        sys.stdout.write(output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
