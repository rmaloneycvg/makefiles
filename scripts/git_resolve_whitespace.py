#!/usr/bin/env python3
import subprocess
import argparse
import sys


def main():
    parser = argparse.ArgumentParser(
        description="Auto-resolve whitespace merge conflicts."
    )
    parser.add_argument(
        "--side",
        choices=["current", "theirs"],
        required=True,
        help="Which side to favor (current/ours or theirs)",
    )
    args = parser.parse_args()

    checkout_flag = "--ours" if args.side == "current" else "--theirs"

    # Get conflicted files (Unmerged files)
    result = subprocess.run(
        ["git", "diff", "--name-only", "--diff-filter=U"],
        capture_output=True,
        text=True,
        check=True,
    )
    conflicted_files = [f for f in result.stdout.splitlines() if f]

    if not conflicted_files:
        print("No merge conflicts found.")
        sys.exit(0)

    for file in conflicted_files:
        # Check if difference is whitespace only using git's exit code
        diff_cmd = f"git diff --ignore-all-space --exit-code ':2:{file}' ':3:{file}'"
        diff_result = subprocess.run(diff_cmd, shell=True, capture_output=True)

        if diff_result.returncode == 0:
            # 0 means no differences (other than the ignored whitespace)
            print(f"WHITESPACE ONLY: {file} - using {args.side} ({checkout_flag})")
            subprocess.run(["git", "checkout", checkout_flag, file], check=True)
            subprocess.run(["git", "add", file], check=True)
        else:
            print(f"REAL CHANGES: {file} - skipping")


if __name__ == "__main__":
    main()
