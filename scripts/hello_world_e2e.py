"""Hello-world E2E flow for terminal and notebook paths."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path


@dataclass(frozen=True)
class E2EResult:
    mode: str
    dry_run: bool
    timestamp: str


def run_flow(mode: str, dry_run: bool) -> E2EResult:
    artifacts = Path("artifacts")
    artifacts.mkdir(exist_ok=True)
    ts = datetime.now(UTC).isoformat()
    (artifacts / "hello_world_e2e.log").write_text(
        f"mode={mode} dry_run={dry_run} ts={ts}\n", encoding="utf-8"
    )
    return E2EResult(mode=mode, dry_run=dry_run, timestamp=ts)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["terminal", "notebook"], default="terminal")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    result = run_flow(mode=args.mode, dry_run=args.dry_run)
    message = f"hello_world_e2e_ok mode={result.mode} dry_run={result.dry_run}"
    if args.debug:
        message += f" ts={result.timestamp}"
    print(message)


if __name__ == "__main__":
    main()
