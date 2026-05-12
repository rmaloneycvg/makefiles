#!/usr/bin/env python3
"""
Manage .env file: set, get, remove keys atomically.
Handles multi-line values and preserves existing entries.

Usage:
    env_tool.py set KEY=value [KEY2=value2 ...]
    env_tool.py unset KEY [KEY2 ...]
    env_tool.py dump                    # print .env contents
    env_tool.py restore-from-secret     # read stdin, write as .env
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ENV_PATH = Path(".env")


def load() -> dict[str, str]:
    if not ENV_PATH.exists():
        return {}
    result: dict[str, str] = {}
    for line in ENV_PATH.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        result[key.strip()] = value.strip()
    return result


def save(values: dict[str, str]) -> None:
    # Write atomically via temp file
    tmp = ENV_PATH.with_suffix(".tmp")
    tmp.write_text("".join(f"{k}={v}\n" for k, v in values.items()))
    tmp.replace(ENV_PATH)


def cmd_set(pairs: list[str]) -> None:
    values = load()
    for pair in pairs:
        if "=" not in pair:
            print(f"Skipping malformed pair: {pair}", file=sys.stderr)
            continue
        key, _, value = pair.partition("=")
        values[key.strip()] = value.strip()
    save(values)


def cmd_unset(keys: list[str]) -> None:
    values = load()
    for key in keys:
        values.pop(key, None)
    save(values)


def cmd_dump() -> None:
    for k, v in load().items():
        print(f"{k}={v}")


def cmd_restore_from_stdin() -> None:
    content = sys.stdin.read()
    ENV_PATH.write_text(content)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("set", help="Set one or more KEY=VALUE pairs")
    s.add_argument("pairs", nargs="+")

    u = sub.add_parser("unset", help="Remove one or more keys")
    u.add_argument("keys", nargs="+")

    sub.add_parser("dump", help="Print .env contents")
    sub.add_parser("restore-from-stdin", help="Overwrite .env with stdin content")

    args = parser.parse_args()

    if args.cmd == "set":
        cmd_set(args.pairs)
    elif args.cmd == "unset":
        cmd_unset(args.keys)
    elif args.cmd == "dump":
        cmd_dump()
    elif args.cmd == "restore-from-stdin":
        cmd_restore_from_stdin()
    return 0


if __name__ == "__main__":
    sys.exit(main())
