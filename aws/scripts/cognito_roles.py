#!/usr/bin/env python3
"""Cognito User Pool group and role management.

Subcommands:
    create-groups       Create standard groups (Reader, Writer, Admin) in a User Pool
    list-groups         List groups in a User Pool
    assign-user         Add a user to a group
    trust-policy        Generate IAM trust policy for Cognito identity pool role mapping
    group-config        Generate group creation JSON with IAM role ARN and precedence

Standard groups (--standard):
    Reader  - Read-only API access (precedence 3)
    Writer  - Read/write API access (precedence 2)
    Admin   - Full administrative access (precedence 1)
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys


def run_aws(args: list[str]) -> dict:
    """Run an AWS CLI command (list args, no shell) and return parsed JSON output."""
    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    return json.loads(result.stdout) if result.stdout.strip() else {}


STANDARD_GROUPS = [
    {"name": "Reader", "description": "Read-only API access", "precedence": 3},
    {"name": "Writer", "description": "Read/write API access", "precedence": 2},
    {"name": "Admin", "description": "Full administrative access", "precedence": 1},
]


def create_groups(args):
    """Create standard Cognito groups."""
    groups = STANDARD_GROUPS
    if args.custom:
        groups = []
        for spec in args.custom:
            parts = spec.split(":")
            if len(parts) != 3:
                print(
                    f"Error: custom format is Name:Description:Precedence, got '{spec}'",
                    file=sys.stderr,
                )
                sys.exit(1)
            groups.append(
                {
                    "name": parts[0],
                    "description": parts[1],
                    "precedence": int(parts[2]),
                }
            )

    for group in groups:
        cmd = [
            "aws", "cognito-idp", "create-group",
            "--user-pool-id", args.user_pool_id,
            "--group-name", group["name"],
            "--description", group["description"],
            "--precedence", str(group["precedence"]),
        ]
        if args.role_arn_prefix:
            cmd += ["--role-arn", f"{args.role_arn_prefix}-{group['name']}"]
        if args.dry_run:
            print(f"[dry-run] {' '.join(cmd)}")
        else:
            print(f"Creating group: {group['name']}")
            run_aws(cmd)
            print(f"  ✓ {group['name']} (precedence={group['precedence']})")


def list_groups(args):
    """List groups in a User Pool."""
    result = run_aws(
        ["aws", "cognito-idp", "list-groups", "--user-pool-id", args.user_pool_id]
    )
    for group in result.get("Groups", []):
        print(f"  {group['GroupName']} (precedence={group.get('Precedence', 'N/A')})")


def assign_user(args):
    """Add a user to a group."""
    cmd = [
        "aws", "cognito-idp", "admin-add-user-to-group",
        "--user-pool-id", args.user_pool_id,
        "--username", args.username,
        "--group-name", args.group,
    ]
    if args.dry_run:
        print(f"[dry-run] {' '.join(cmd)}")
    else:
        run_aws(cmd)
        print(f"  ✓ Added {args.username} to {args.group}")


def trust_policy(args):
    """Generate IAM trust policy for Cognito identity pool."""
    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"Federated": "cognito-identity.amazonaws.com"},
                "Action": "sts:AssumeRoleWithWebIdentity",
                "Condition": {
                    "StringEquals": {
                        "cognito-identity.amazonaws.com:aud": args.identity_pool_id
                    },
                    "ForAnyValue:StringLike": {
                        "cognito-identity.amazonaws.com:amr": "authenticated"
                    },
                },
            }
        ],
    }
    print(json.dumps(policy, indent=2))


def group_config(_args):
    """Generate group creation config JSON."""
    groups = [
        {"GroupName": g["name"], "Description": g["description"], "Precedence": g["precedence"]}
        for g in STANDARD_GROUPS
    ]
    print(json.dumps(groups, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = parser.add_subparsers(dest="command")

    p_cg = sub.add_parser("create-groups", help="Create groups in User Pool")
    p_cg.add_argument("--user-pool-id", required=True)
    p_cg.add_argument("--role-arn-prefix", default="", help="IAM role ARN prefix")
    p_cg.add_argument("--custom", nargs="*", help="Custom groups: Name:Description:Precedence")
    p_cg.add_argument("--dry-run", action="store_true")

    p_lg = sub.add_parser("list-groups", help="List groups")
    p_lg.add_argument("--user-pool-id", required=True)

    p_au = sub.add_parser("assign-user", help="Add user to group")
    p_au.add_argument("--user-pool-id", required=True)
    p_au.add_argument("--username", required=True)
    p_au.add_argument("--group", required=True)
    p_au.add_argument("--dry-run", action="store_true")

    p_tp = sub.add_parser("trust-policy", help="Generate IAM trust policy")
    p_tp.add_argument("--identity-pool-id", required=True)

    sub.add_parser("group-config", help="Print standard group config JSON")

    args = parser.parse_args()
    dispatch = {
        "create-groups": create_groups,
        "list-groups": list_groups,
        "assign-user": assign_user,
        "trust-policy": trust_policy,
        "group-config": group_config,
    }
    fn = dispatch.get(args.command)
    if not fn:
        parser.print_help()
        return 1
    fn(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
