#!/usr/bin/env python3
import shutil
from pathlib import Path


def main():
    print("Cleaning UI components (removing node_modules)...")

    # Start searching from the directory where the script is executed
    root_dir = Path(".")

    # Find all node_modules directories
    # Note: Using rglob is safer and cross-platform
    count = 0
    for node_modules_dir in root_dir.rglob("node_modules"):
        if node_modules_dir.is_dir():
            print(f"Cleaning {node_modules_dir.parent}...")
            try:
                shutil.rmtree(node_modules_dir)
                count += 1
            except Exception as e:
                print(f"Failed to delete {node_modules_dir}: {e}")

    print(f"Done. Removed {count} node_modules directories.")


if __name__ == "__main__":
    main()
