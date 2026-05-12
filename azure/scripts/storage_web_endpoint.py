#!/usr/bin/env python3
"""
Query Azure for the actual static website hostname for a storage account.
Avoids hardcoding the z13/z## zone identifier, which varies per account.

Usage:
    storage_web_endpoint.py --account <name> --resource-group <rg>
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from urllib.parse import urlparse


def az(*args: str) -> str:
    result = subprocess.run(["az", *args], check=True, capture_output=True, text=True)
    return result.stdout.strip()


def get_web_endpoint(account: str, resource_group: str) -> str:
    url = az(
        "storage", "account", "show",
        "--name", account,
        "--resource-group", resource_group,
        "--query", "primaryEndpoints.web",
        "-o", "tsv",
    )
    if not url:
        raise SystemExit(f"Storage account '{account}' not found or web endpoint not enabled.")
    # Strip https:// and trailing slash
    parsed = urlparse(url)
    return parsed.hostname or url.strip("/")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--account", required=True)
    parser.add_argument("--resource-group", required=True)
    args = parser.parse_args()
    print(get_web_endpoint(args.account, args.resource_group))
    return 0


if __name__ == "__main__":
    sys.exit(main())
