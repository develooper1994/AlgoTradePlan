"""Lightweight dependency policy check (Phase 14).

Verifies that the project's declared dependencies satisfy the pinning and
allowlist rules in ``docs/dependency_policy.md`` without contacting any
external service. Designed to be safe in offline CI.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Allowlisted top-level package roots. Anything outside the allowlist must be
# justified in docs/dependency_policy.md and added here.
ALLOWED_PACKAGES = frozenset(
    {
        "pandas",
        "scikit-learn",
        "ccxt",
        "mkdocs",
        "mkdocs-material",
    }
)

# Every dependency must have an explicit lower bound (>=) per policy.
_DEP_PATTERN = re.compile(r'^"?([A-Za-z0-9_.\-]+)\s*(?:\[[^\]]+\])?\s*([^"\s,]*)"?$')


def _iter_dependencies(pyproject_text: str) -> list[tuple[str, str]]:
    """Return (name, version_spec) pairs from optional-dependencies in pyproject.toml."""

    results: list[tuple[str, str]] = []
    in_section = False
    for raw_line in pyproject_text.splitlines():
        line = raw_line.strip()
        if line.startswith("["):
            in_section = line == "[project.optional-dependencies]"
            continue
        if not in_section or not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        _, value = line.split("=", 1)
        value = value.strip()
        if not value.startswith("["):
            continue
        inner = value.strip("[]")
        for token in inner.split(","):
            token = token.strip().strip('"').strip("'")
            if not token:
                continue
            match = _DEP_PATTERN.match(f'"{token}"')
            if match:
                results.append((match.group(1), match.group(2)))
    return results


def check_policy(repo_root: Path) -> list[str]:
    issues: list[str] = []
    pyproject = repo_root / "pyproject.toml"
    if not pyproject.is_file():
        return ["pyproject.toml not found"]

    deps = _iter_dependencies(pyproject.read_text(encoding="utf-8"))
    for name, spec in deps:
        if name not in ALLOWED_PACKAGES:
            issues.append(f"dependency not in allowlist: {name}")
        if ">=" not in spec:
            issues.append(f"dependency missing >= lower bound: {name} {spec!r}")

    policy_doc = repo_root / "docs" / "dependency_policy.md"
    if not policy_doc.is_file():
        issues.append("missing docs/dependency_policy.md")

    return issues


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Dependency policy check")
    parser.add_argument("--repo-root", default=".")
    args = parser.parse_args(argv)

    issues = check_policy(Path(args.repo_root).resolve())
    if issues:
        for issue in issues:
            print(f"security_check_fail {issue}")
        return 1
    print("security_check_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
