"""Deployment readiness check (Phase 13).

Verifies that lint, test, and smoke targets exist and that the documented
deployment runbook is present before promotion is allowed.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REQUIRED_FILES = [
    "Makefile",
    "scripts/run_tests.py",
    "scripts/hello_world_e2e.py",
    "docs/runbooks/deployment_rollback.md",
    "docs/runbooks/dry_run_promotion.md",
    "docs/runbooks/emergency_stop.md",
]

REQUIRED_MAKE_TARGETS = ("lint:", "test:", "smoke:")


def check_readiness(repo_root: Path) -> list[str]:
    issues: list[str] = []

    for relative in REQUIRED_FILES:
        if not (repo_root / relative).is_file():
            issues.append(f"missing required file: {relative}")

    makefile = repo_root / "Makefile"
    if makefile.is_file():
        content = makefile.read_text(encoding="utf-8")
        for target in REQUIRED_MAKE_TARGETS:
            if target not in content:
                issues.append(f"Makefile missing target: {target}")

    return issues


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Deployment readiness check")
    parser.add_argument("--repo-root", default=".")
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    issues = check_readiness(repo_root)
    if issues:
        for issue in issues:
            print(f"deploy_check_fail {issue}")
        return 1
    print("deploy_check_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
