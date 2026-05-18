"""Create a timestamped local backup placeholder."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path


def main() -> None:
    backup_dir = Path("artifacts/backups")
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    output = backup_dir / f"backup_{stamp}.jsonl"
    output.write_text('{"status":"backup_created"}\n', encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
