"""Restore placeholder that validates backup file existence."""

from __future__ import annotations

import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("backup_file")
    args = parser.parse_args()
    backup = Path(args.backup_file)
    if not backup.exists():
        raise FileNotFoundError(f"Backup file not found: {backup}")
    print(f"Restore simulation completed from {backup}")


if __name__ == "__main__":
    main()
