"""Minimal migration script scaffold."""

from __future__ import annotations

from pathlib import Path


def main() -> None:
    Path("artifacts/migrations").mkdir(parents=True, exist_ok=True)
    Path("artifacts/migrations/last_migration.txt").write_text("ok\n", encoding="utf-8")
    print("Migration simulation completed")


if __name__ == "__main__":
    main()
