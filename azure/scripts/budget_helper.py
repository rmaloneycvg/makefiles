#!/usr/bin/env python3
"""
Generate budget notifications JSON and date ranges for `az consumption budget create`.

Uses only the stdlib datetime module so it is portable across Linux/macOS
(the `date -d` flag used previously was GNU-specific).

Usage:
    budget_helper.py notifications --email admin@example.com --thresholds 80 100
    budget_helper.py start-date
    budget_helper.py end-date --years 1
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date


def notifications(email: str, thresholds: list[int]) -> str:
    out = {}
    for t in thresholds:
        out[f"actual_GreaterThan_{t}_Percent"] = {
            "enabled": True,
            "operator": "GreaterThan",
            "threshold": t,
            "contactEmails": [email],
        }
    return json.dumps(out)


def start_date() -> str:
    today = date.today()
    return today.replace(day=1).isoformat()


def end_date(years: int) -> str:
    today = date.today()
    return today.replace(year=today.year + years, day=1).isoformat()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    n = sub.add_parser("notifications")
    n.add_argument("--email", required=True)
    n.add_argument("--thresholds", nargs="+", type=int, default=[80, 100])

    sub.add_parser("start-date")

    e = sub.add_parser("end-date")
    e.add_argument("--years", type=int, default=1)

    args = parser.parse_args()

    if args.cmd == "notifications":
        print(notifications(args.email, args.thresholds))
    elif args.cmd == "start-date":
        print(start_date())
    elif args.cmd == "end-date":
        print(end_date(args.years))
    return 0


if __name__ == "__main__":
    sys.exit(main())
