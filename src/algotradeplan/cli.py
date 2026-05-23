"""Unified CLI entry point for AlgoTradePlan.

Usage:
    python -m algotradeplan <subcommand> [options]
    python -m algotradeplan --help

Subcommands:
    status      Show framework status and next actions
    tutorial    Run the offline tutorial walkthrough
    coverage    Generate data source coverage docs
    recommend   Recommend data sources for a use case
    preflight   Check if a pipeline configuration can run
    health      Run data health report
    recipe      Execute a YAML recipe
    refresh     Refresh all generated framework artifacts
    doctor      Check environment and API key health
    examples    List available recipes and use cases
    explain     Explain a source or dataset
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


def _ensure_repo_in_path() -> None:
    repo = str(REPO_ROOT)
    if repo not in sys.path:
        sys.path.insert(0, repo)


def _run_script(args: list[str]) -> int:
    result = subprocess.run(args, check=False)
    return result.returncode


# ---------------------------------------------------------------------------
# Subcommand implementations
# ---------------------------------------------------------------------------


def cmd_status(args: argparse.Namespace) -> int:
    _ensure_repo_in_path()
    from scripts.framework_status import build_status_report, render_markdown, _redact_sensitive_fields  # type: ignore[import]

    report = build_status_report()
    sanitized = _redact_sensitive_fields(report)

    if args.score:
        score_value: int = sanitized["framework_score"]
        print(f"framework_score: {score_value}/100")
        if not args.verbose and not args.json:
            return 0

    if args.next_actions:
        priorities: dict[str, list[str]] = sanitized["priority_actions"]
        numbered = [
            f"[{p}] {entry}"
            for p in ("P0", "P1", "P2", "P3")
            for entry in priorities[p]
        ]
        for i, item in enumerate(numbered, 1):
            print(f"{i}. {item}")
        if not args.json:
            return 0

    if args.json:
        print(json.dumps(sanitized, indent=2))
        return 0

    if args.verbose:
        print(render_markdown(sanitized))
        return 0

    # Default: compact summary — extract only non-sensitive fields
    fw_score: int = sanitized["framework_score"]
    top_actions: list[str] = sanitized["priority_actions"].get("P0", [])
    cov: dict[str, Any] = sanitized.get("coverage_summary", {})
    use_case_gaps: list[str] = sanitized.get("use_case_coverage_gaps", [])
    source_count = cov.get("source_count", "?")
    live_count = cov.get("live_sources_count", "?")

    print(f"framework_score: {fw_score}/100")
    print(f"sources: {source_count} total, {live_count} live")
    if top_actions:
        print("\nTop next actions (P0):")
        for action_item in top_actions[:5]:
            print(f"  - {action_item}")
    if use_case_gaps:
        gap_preview = ", ".join(use_case_gaps[:3])
        extra = f" (+{len(use_case_gaps)-3} more)" if len(use_case_gaps) > 3 else ""
        print(f"\nUse-case gaps: {gap_preview}{extra}")
    return 0


def cmd_tutorial(args: argparse.Namespace) -> int:
    _ensure_repo_in_path()
    script = str(REPO_ROOT / "scripts" / "tutorial_mode.py")
    cli_args = [sys.executable, script, "--all", "--offline"]
    if args.pretty:
        cli_args.append("--pretty")
    elif args.markdown:
        cli_args.append("--markdown")
    if args.write_doc:
        cli_args.append("--write-doc")
    return _run_script(cli_args)


def cmd_coverage(args: argparse.Namespace) -> int:
    _ensure_repo_in_path()
    script = str(REPO_ROOT / "scripts" / "generate_data_coverage_doc.py")
    return _run_script([sys.executable, script])


def cmd_recommend(args: argparse.Namespace) -> int:
    _ensure_repo_in_path()
    from src.algotradeplan.data import DataHub  # type: ignore[import]

    hub = DataHub()
    allow_api_key = not args.no_api_key
    use_case = args.use_case

    if not use_case:
        # List available use cases
        from src.algotradeplan.data.query import supported_use_cases  # type: ignore[import]
        print("Available use cases:")
        for uc in supported_use_cases():
            print(f"  {uc}")
        return 0

    results = hub.recommend_sources(use_case, allow_api_key=allow_api_key)
    if args.json:
        print(json.dumps(results, indent=2))
        return 0

    if not results:
        print(f"No sources found for use case: {use_case}")
        return 1

    print(f"Recommended sources for '{use_case}':")
    for item in results:
        api_note = " [API key required]" if item.get("requires_api_key") == "yes" else ""
        print(f"  {item['source']}{api_note} — {item.get('reason', '')}")
    return 0


def cmd_preflight(args: argparse.Namespace) -> int:
    _ensure_repo_in_path()
    from src.algotradeplan.data import DataHub  # type: ignore[import]
    from src.algotradeplan.research import PreflightChecker  # type: ignore[import]

    checker = PreflightChecker(DataHub())
    result = checker.check(
        source=args.source,
        symbol=args.symbol,
        datasets=args.datasets,
        strategy=args.strategy,
        allow_api_key=not args.no_api_key,
    ).to_dict()

    if args.json:
        print(json.dumps(result, indent=2))
        return 0

    print(f"can_run: {result['can_run']}")
    print(f"source: {result['source']}")
    print(f"symbol: {result['symbol']}")
    print(f"datasets: {result['datasets']}")
    if result.get("blocking_issues"):
        print(f"blocking_issues: {result['blocking_issues']}")
    if result.get("warnings"):
        print(f"warnings: {result['warnings']}")
    if result.get("suggestions"):
        print(f"suggestions: {result['suggestions']}")
    if result.get("recommended_sources"):
        print(f"recommended_sources: {result['recommended_sources']}")
    return 0 if result["can_run"] else 1


def cmd_health(args: argparse.Namespace) -> int:
    _ensure_repo_in_path()
    script = str(REPO_ROOT / "scripts" / "data_health_report.py")
    cli_args = [
        sys.executable, script,
        "--source", args.source,
        "--symbol", args.symbol,
        "--datasets", *args.datasets,
    ]
    if args.offline:
        cli_args.append("--offline")
    if args.allow_partial:
        cli_args.append("--allow-partial")
    if args.json:
        cli_args.append("--json")
    return _run_script(cli_args)


def cmd_recipe(args: argparse.Namespace) -> int:
    _ensure_repo_in_path()
    script = str(REPO_ROOT / "scripts" / "run_recipe.py")
    cli_args = [sys.executable, script, args.recipe_path]
    if args.dry_run:
        cli_args.append("--dry-run")
    if args.json:
        cli_args.append("--json")
    return _run_script(cli_args)


def cmd_refresh(args: argparse.Namespace) -> int:
    _ensure_repo_in_path()
    script = str(REPO_ROOT / "scripts" / "refresh_framework_artifacts.py")
    cli_args = [sys.executable, script]
    if args.skip_live:
        cli_args.append("--skip-live")
    return _run_script(cli_args)


def cmd_doctor(args: argparse.Namespace) -> int:  # noqa: ARG001
    """Check environment, API keys, docs, and artifact health."""
    _ensure_repo_in_path()

    issues: list[str] = []
    ok_items: list[str] = []

    # Python version
    major, minor = sys.version_info[:2]
    if (major, minor) >= (3, 9):
        ok_items.append(f"Python {major}.{minor} ✓")
    else:
        issues.append(f"Python {major}.{minor} — requires >= 3.9")

    # Required docs
    required_docs = [
        REPO_ROOT / "docs" / "data_source_coverage.md",
        REPO_ROOT / "docs" / "source_recommendations.md",
        REPO_ROOT / "docs" / "framework_status.md",
    ]
    for doc in required_docs:
        if doc.exists():
            ok_items.append(f"doc:{doc.name} ✓")
        else:
            issues.append(f"doc:{doc.name} missing — run: python -m algotradeplan refresh --skip-live")

    # Artifact freshness
    tutorial_artifact = REPO_ROOT / "artifacts" / "tutorial" / "tutorial_walkthrough.md"
    if tutorial_artifact.exists():
        ok_items.append("artifact:tutorial_walkthrough ✓")
    else:
        issues.append("artifact:tutorial_walkthrough missing — run: python -m algotradeplan tutorial --write-doc")

    # Optional API keys
    api_key_vars = [
        "ALPHAVANTAGE_API_KEY", "TWELVEDATA_API_KEY", "POLYGON_API_KEY",
        "FINNHUB_API_KEY", "FRED_API_KEY",
    ]
    present_keys = [v for v in api_key_vars if os.environ.get(v)]
    if present_keys:
        ok_items.append(f"api_keys: {len(present_keys)}/{len(api_key_vars)} optional keys set")
    else:
        ok_items.append("api_keys: none set (public sources work without API keys)")

    # Prefer the canonical name `TEFAS_CLI_CMD`. Fall back to legacy `TEFAS_CLI_BIN` for compatibility.
    tefas_cli_cmd = os.environ.get("TEFAS_CLI_CMD", "").strip()
    tefas_cli_bin = tefas_cli_cmd or os.environ.get("TEFAS_CLI_BIN", "").strip()
    tefas_ffi_lib = os.environ.get("TEFAS_FFI_LIB", "").strip()
    tefas_cli_ok = False
    tefas_ffi_ok = False

    if tefas_cli_bin:
        cli_path = Path(tefas_cli_bin)
        tefas_cli_ok = cli_path.exists() and os.access(cli_path, os.X_OK)
        if not tefas_cli_ok:
            issues.append("TEFAS CLI path is set but not executable: ensure TEFAS_CLI_CMD or TEFAS_CLI_BIN points to a runnable binary")
    if tefas_ffi_lib:
        ffi_path = Path(tefas_ffi_lib)
        tefas_ffi_ok = ffi_path.exists()
        if not tefas_ffi_ok:
            issues.append("TEFAS_FFI_LIB is set but file does not exist")

    # Recipes
    recipes_dir = REPO_ROOT / "recipes"
    if recipes_dir.exists():
        recipe_files = list(recipes_dir.glob("*.yaml"))
        ok_items.append(f"recipes: {len(recipe_files)} found")
    else:
        issues.append("recipes/ directory missing")

    print("AlgoTradePlan Doctor")
    print("=" * 40)
    for item in ok_items:
        print(f"  ✓ {item}")
    for item in issues:
        print(f"  ✗ {item}")
    print()
    print("TEFAS integration:")
    if tefas_cli_cmd:
        print(f"  - TEFAS_CLI_CMD: {'ok' if tefas_cli_ok else 'invalid'}")
    elif tefas_cli_bin:
        print(f"  - TEFAS_CLI_BIN: {'ok' if tefas_cli_ok else 'invalid'}")
    else:
        print("  - TEFAS_CLI_CMD/TEFAS_CLI_BIN: missing")
    if tefas_ffi_lib:
        print(f"  - TEFAS_FFI_LIB: {'ok' if tefas_ffi_ok else 'invalid'}")
    else:
        print("  - TEFAS_FFI_LIB: missing")
    if tefas_cli_ok or tefas_ffi_ok:
        print("  - tefas_public fetch: available")
    else:
        print("  - tefas_public source available but fetch disabled")
    print()
    if issues:
        print(f"Found {len(issues)} issue(s). See suggestions above.")
        return 1
    print("All checks passed.")
    return 0


def cmd_examples(args: argparse.Namespace) -> int:  # noqa: ARG001
    """List available recipes and use cases."""
    _ensure_repo_in_path()
    from src.algotradeplan.data.query import supported_use_cases  # type: ignore[import]

    print("=== Use Cases ===")
    for uc in supported_use_cases():
        print(f"  {uc}")

    print()
    print("=== Recipes ===")
    recipes_dir = REPO_ROOT / "recipes"
    if recipes_dir.exists():
        for recipe_file in sorted(recipes_dir.glob("*.yaml")):
            print(f"  {recipe_file.name}")
    else:
        print("  (no recipes found)")

    print()
    print("=== Try it ===")
    print("  python -m algotradeplan recommend --use-case crypto_spot_kline --no-api-key")
    print("  python -m algotradeplan tutorial --offline")
    print("  python -m algotradeplan recipe recipes/crypto_momentum.yaml --dry-run")
    return 0


def cmd_explain(args: argparse.Namespace) -> int:
    """Explain a source or dataset."""
    _ensure_repo_in_path()
    from src.algotradeplan.data import DataHub  # type: ignore[import]

    hub = DataHub()
    kind = args.kind
    name = args.name

    if kind == "source":
        result = hub.explain_source(name)
        if args.json:
            print(json.dumps(result, indent=2))
            return 0
        source_name: str = result.get("source", name)
        impl_status: str = result.get("implementation_status", "?")
        needs_key: object = result.get("requires_api_key", "?")
        key_env_name: str = result.get("api_key_env", "")
        datasets_list: list[str] = result.get("implemented_datasets", [])
        source_notes: str = result.get("notes", "")
        print(f"Source: {source_name}")
        print(f"  implementation_status: {impl_status}")
        print(f"  requires_api_key: {needs_key}")
        if key_env_name:
            print(f"  api_key_env: {key_env_name}")
        if datasets_list:
            print(f"  datasets: {', '.join(datasets_list)}")
        if source_notes:
            print(f"  notes: {source_notes}")
        return 0

    if kind == "dataset":
        result = hub.explain_dataset(name)
        if args.json:
            print(json.dumps(result, indent=2))
            return 0
        dataset_name: str = result.get("dataset", name)
        dataset_desc: str = result.get("description", "?")
        best_public: list[dict[str, Any]] = result.get("best_sources_no_api_key", [])
        print(f"Dataset: {dataset_name}")
        print(f"  description: {dataset_desc}")
        if best_public:
            public_source_names = [s["source"] for s in best_public]
            print(f"  best_sources (no API key): {', '.join(public_source_names)}")
        return 0

    print(f"Unknown explain kind: {kind}. Use 'source' or 'dataset'.")
    return 1


# ---------------------------------------------------------------------------
# Parser setup
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m algotradeplan",
        description=(
            "AlgoTradePlan — algorithmic trading research framework.\n\n"
            "Quick start:\n"
            "  python -m algotradeplan tutorial --offline\n"
            "  python -m algotradeplan recommend --use-case crypto_spot_kline --no-api-key\n"
            "  python -m algotradeplan status\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="subcommand", metavar="<subcommand>")

    # status
    p_status = sub.add_parser("status", help="Show framework status and next actions")
    p_status.add_argument("--score", action="store_true", help="Print only the framework score")
    p_status.add_argument("--next-actions", action="store_true", help="Print next actions only")
    p_status.add_argument("--json", action="store_true", help="Output as JSON")
    p_status.add_argument("--verbose", action="store_true", help="Full detailed report")

    # tutorial
    p_tut = sub.add_parser("tutorial", help="Run the tutorial walkthrough")
    p_tut.add_argument("--offline", action="store_true", default=True, help="Use offline fallback data (default: True)")
    p_tut.add_argument("--pretty", action="store_true", help="Pretty-print output")
    p_tut.add_argument("--markdown", action="store_true", help="Print as markdown")
    p_tut.add_argument("--write-doc", action="store_true", help="Write artifact to disk")

    # coverage
    sub.add_parser("coverage", help="Generate data source coverage docs")

    # recommend
    p_rec = sub.add_parser("recommend", help="Recommend sources for a use case")
    p_rec.add_argument("--use-case", metavar="USE_CASE", help="Use case to look up (e.g. crypto_spot_kline)")
    p_rec.add_argument("--no-api-key", action="store_true", help="Only show sources without API key requirement")
    p_rec.add_argument("--json", action="store_true", help="Output as JSON")

    # preflight
    p_pre = sub.add_parser("preflight", help="Check if a pipeline configuration can run")
    p_pre.add_argument("--source", required=True)
    p_pre.add_argument("--symbol", required=True)
    p_pre.add_argument("--datasets", nargs="+", required=True)
    p_pre.add_argument("--strategy", required=True)
    p_pre.add_argument("--no-api-key", action="store_true", help="Require no API key")
    p_pre.add_argument("--json", action="store_true", help="Output as JSON")

    # health
    p_health = sub.add_parser("health", help="Run data health report")
    p_health.add_argument("--source", required=True)
    p_health.add_argument("--symbol", required=True)
    p_health.add_argument("--datasets", nargs="+", required=True)
    p_health.add_argument("--offline", action="store_true")
    p_health.add_argument("--allow-partial", action="store_true")
    p_health.add_argument("--json", action="store_true")

    # recipe
    p_recipe = sub.add_parser("recipe", help="Execute a YAML recipe")
    p_recipe.add_argument("recipe_path", metavar="RECIPE")
    p_recipe.add_argument("--dry-run", action="store_true", help="Validate only, do not run")
    p_recipe.add_argument("--json", action="store_true", help="Output as JSON")

    # refresh
    p_refresh = sub.add_parser("refresh", help="Refresh all generated framework artifacts")
    p_refresh.add_argument("--skip-live", action="store_true", help="Skip live API calls (offline-safe)")

    # doctor
    sub.add_parser("doctor", help="Check environment, API keys, docs, and artifact health")

    # examples
    sub.add_parser("examples", help="List available recipes and use cases")

    # explain
    p_explain = sub.add_parser("explain", help="Explain a source or dataset")
    p_explain.add_argument("kind", choices=["source", "dataset"], metavar="source|dataset")
    p_explain.add_argument("name", metavar="NAME")
    p_explain.add_argument("--json", action="store_true", help="Output as JSON")

    return parser


_SUBCOMMAND_MAP = {
    "status": cmd_status,
    "tutorial": cmd_tutorial,
    "coverage": cmd_coverage,
    "recommend": cmd_recommend,
    "preflight": cmd_preflight,
    "health": cmd_health,
    "recipe": cmd_recipe,
    "refresh": cmd_refresh,
    "doctor": cmd_doctor,
    "examples": cmd_examples,
    "explain": cmd_explain,
}


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.subcommand is None:
        parser.print_help()
        return 0

    handler = _SUBCOMMAND_MAP.get(args.subcommand)
    if handler is None:
        parser.print_help()
        return 1

    return handler(args)


if __name__ == "__main__":
    sys.exit(main())
