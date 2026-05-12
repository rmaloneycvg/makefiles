#!/usr/bin/env python3
import subprocess
import argparse
import sys


def run_cmd(cmd, capture=True, check=True):
    """Helper to run shell commands cleanly."""
    result = subprocess.run(cmd, shell=True, text=True, capture_output=capture)
    if check and result.returncode != 0:
        print(f"Error executing: {cmd}\n{result.stderr.strip()}")
        sys.exit(1)
    return result.stdout.strip() if capture else None


def main():
    parser = argparse.ArgumentParser(description="Squash commits onto a target branch.")
    parser.add_argument("--target-branch", default="main", help="Branch to squash onto")
    parser.add_argument("--num-commits", help="Number of commits to squash (n)")
    parser.add_argument("--message", help="Custom commit message prefix (m)")
    parser.add_argument(
        "--use-kiro",
        type=int,
        choices=[0, 1],
        default=1,
        help="Use AI for commit message",
    )
    parser.add_argument(
        "--base-msg", default="Squashed commits", help="Fallback message"
    )
    args = parser.parse_args()

    # 1. Check for uncommitted changes
    if (
        run_cmd("git diff --quiet", check=False) is None
        or run_cmd("git diff --cached --quiet", check=False) is None
    ):
        # If return code is not 0, it means there are diffs
        if (
            subprocess.run("git diff --quiet", shell=True).returncode != 0
            or subprocess.run("git diff --cached --quiet", shell=True).returncode != 0
        ):
            print("Error: Pending uncommitted changes detected. Doing nothing.")
            sys.exit(1)

    # 2. Determine base reference
    if args.num_commits:
        print(f"Squashing last {args.num_commits} commits...")
        base_ref = f"HEAD~{args.num_commits}"
    else:
        print(f"Fetching latest {args.target_branch} from origin...")
        run_cmd(f"git fetch origin {args.target_branch}", capture=False)
        base_ref = f"origin/{args.target_branch}"

    # 3. Generate Commit Message
    final_msg = args.base_msg
    if args.use_kiro == 1:
        print("Generating commit message with Kiro...")
        # Get diff stat to feed to Kiro
        diff_stat = run_cmd(f"git diff {base_ref}...HEAD --stat | head -80")
        prompt = f"Generate a concise git commit message summarizing changes from all commits being squashed. Output ONLY the commit message, no introductory text.\n\n{diff_stat}"

        # Call Kiro
        kiro_cmd = (
            f"kiro-cli chat --agent commit-msg -a -f plain --no-interactive '{prompt}'"
        )
        ai_msg = run_cmd(kiro_cmd, check=False)

        # Clean up AI output (Python replaces the crazy sed/tr/grep chain)
        if ai_msg:
            # Keep only the first non-empty line
            clean_ai_msg = next(
                (line for line in ai_msg.splitlines() if line.strip()), ""
            ).strip()
            final_msg = clean_ai_msg if clean_ai_msg else args.base_msg

    if args.message:
        final_msg = (
            f"{args.message} : {final_msg}" if args.use_kiro == 1 else args.message
        )

    # 4. Perform the Reset and Commit
    if args.num_commits:
        run_cmd(f"git reset --soft {base_ref}", capture=False)
        run_cmd(f"git commit -m '{final_msg}'", capture=False)
    else:
        run_cmd(f"git -c merge.ff=false merge {base_ref} --no-edit", capture=False)
        run_cmd(f"git reset --soft {base_ref}", capture=False)
        run_cmd(f"git commit --allow-empty -m '{final_msg}'", capture=False)

    # 5. Push
    run_cmd("git push --force-with-lease", capture=False)
    print("Done.")


if __name__ == "__main__":
    main()
