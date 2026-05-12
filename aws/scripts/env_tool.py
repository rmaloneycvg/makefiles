#!/usr/bin/env python3
"""Atomic .env file management tool.

Subcommands:
    set KEY=value       Set a key-value pair (overwrites if exists)
    unset KEY           Remove a key
    get KEY             Print the value of KEY (empty if absent)
    dump                Print all key=value pairs
    restore-from-stdin  Replace .env with content from stdin

All writes are atomic (temp file + rename). Prevents duplicate keys.
"""
import sys
import os
import tempfile

ENV_FILE = os.environ.get("ENV_FILE", ".env")


def read_env():
    """Read .env into ordered list of (key, value) tuples, preserving comments."""
    lines = []
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE, "r") as f:
            for line in f:
                stripped = line.strip()
                if "=" in stripped and not stripped.startswith("#"):
                    key, _, value = stripped.partition("=")
                    lines.append((key.strip(), value.strip()))
                else:
                    lines.append((None, stripped))
    return lines


def write_env(lines):
    """Atomically write lines back to .env."""
    dir_name = os.path.dirname(os.path.abspath(ENV_FILE))
    fd, tmp_path = tempfile.mkstemp(dir=dir_name, prefix=".env_tmp_")
    try:
        with os.fdopen(fd, "w") as f:
            for key, value in lines:
                if key is None:
                    f.write(value + "\n")
                else:
                    f.write(f"{key}={value}\n")
        os.replace(tmp_path, ENV_FILE)
    except Exception:
        os.unlink(tmp_path)
        raise


def cmd_set(arg):
    if "=" not in arg:
        print(f"Error: expected KEY=value, got '{arg}'", file=sys.stderr)
        sys.exit(1)
    key, _, value = arg.partition("=")
    key = key.strip()
    value = value.strip()
    lines = read_env()
    found = False
    for i, (k, v) in enumerate(lines):
        if k == key:
            lines[i] = (key, value)
            found = True
            break
    if not found:
        lines.append((key, value))
    write_env(lines)


def cmd_unset(key):
    lines = read_env()
    lines = [(k, v) for k, v in lines if k != key]
    write_env(lines)


def cmd_dump():
    lines = read_env()
    for key, value in lines:
        if key is not None:
            print(f"{key}={value}")


def cmd_get(key):
    lines = read_env()
    for k, v in lines:
        if k == key:
            print(v)
            return
    # Exit 0 with empty output to avoid breaking shell pipelines that set -e might catch
    return


def cmd_restore():
    content = sys.stdin.read()
    dir_name = os.path.dirname(os.path.abspath(ENV_FILE))
    fd, tmp_path = tempfile.mkstemp(dir=dir_name, prefix=".env_tmp_")
    try:
        with os.fdopen(fd, "w") as f:
            f.write(content)
        os.replace(tmp_path, ENV_FILE)
    except Exception:
        os.unlink(tmp_path)
        raise


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "set" and len(sys.argv) >= 3:
        cmd_set(" ".join(sys.argv[2:]))
    elif cmd == "unset" and len(sys.argv) == 3:
        cmd_unset(sys.argv[2])
    elif cmd == "get" and len(sys.argv) == 3:
        cmd_get(sys.argv[2])
    elif cmd == "dump":
        cmd_dump()
    elif cmd == "restore-from-stdin":
        cmd_restore()
    else:
        print(__doc__)
        sys.exit(1)
