#!/usr/bin/env python3
"""Generate Lambda alias routing-config JSON for weighted traffic shifting.

Usage:
    lambda_routing.py --version 5 --weight 25
    # → {"AdditionalVersionWeights":{"5":0.25}}
"""
from __future__ import annotations

import argparse
import json
import sys


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--version", required=True, help="Additional version number")
    p.add_argument(
        "--weight",
        required=True,
        type=float,
        help="Percentage (0-100) of traffic to route to --version",
    )
    args = p.parse_args()

    if not 0 <= args.weight <= 100:
        print("Error: --weight must be between 0 and 100", file=sys.stderr)
        return 1

    fraction = round(args.weight / 100.0, 4)
    print(json.dumps({"AdditionalVersionWeights": {args.version: fraction}}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
