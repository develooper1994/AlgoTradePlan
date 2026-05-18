"""Validate that migration marker exists."""

from __future__ import annotations

from pathlib import Path


def main() -> None:
    marker = Path("artifacts/migrations/last_migration.txt")
    if not marker.exists():
        raise SystemExit("Migration marker is missing")
    print("Migration validation passed")


if __name__ == "__main__":
    main()
