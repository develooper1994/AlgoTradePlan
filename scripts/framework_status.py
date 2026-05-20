from __future__ import annotations

import argparse
import json
import pathlib
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.algotradeplan.data import DataHub

DOC_PATH = REPO_ROOT / "docs" / "framework_status.md"
PLAN_PATH = REPO_ROOT / "docs" / "next_actions.md"
REQUIRED_NOTEBOOKS = [
    "00_framework_tutorial.ipynb",
    "01_real_data_smoke.ipynb",
    "02_strategy_backtest_portfolio.ipynb",
    "03_multi_source_asset_coverage.ipynb",
]
ARTIFACT_PATHS = {
    "framework_status_doc": DOC_PATH,
    "next_actions_doc": PLAN_PATH,
    "coverage_doc": REPO_ROOT / "docs" / "data_source_coverage.md",
    "source_recommendations_doc": REPO_ROOT / "docs" / "source_recommendations.md",
    "tutorial_walkthrough": REPO_ROOT / "artifacts" / "tutorial" / "tutorial_walkthrough.md",
    "real_data_smoke_report": REPO_ROOT / "artifacts" / "real_data_smoke_report.json",
    "offline_data_health_report": REPO_ROOT / "artifacts" / "data_health" / "offline_fallback_BTCUSDT_health.md",
    "offline_experiment_summary": REPO_ROOT / "artifacts" / "experiments",
}
EXPECTED_TESTS = [
    REPO_ROOT / "tests" / "unit" / "test_data_api.py",
    REPO_ROOT / "tests" / "unit" / "test_framework_scripts.py",
]
SCORE_BASE = 40
SCORE_COMPONENT_CAP = 35
SCORE_COMPONENT_WEIGHT = 4
SCORE_LIVE_CAP = 10
SCORE_FALLBACK_CAP = 5
SCORE_METADATA_PENALTY_CAP = 20
SCORE_METADATA_PENALTY_WEIGHT = 2
SCORE_ARTIFACT_PENALTY_CAP = 10
SCORE_ARTIFACT_PENALTY_WEIGHT = 2
SCORE_MAX = 100


def _redact_sensitive_fields(value: object) -> object:
    if isinstance(value, dict):
        sanitized: dict[object, object] = {}
        for key, item in value.items():
            lowered = str(key).lower()
            if any(token in lowered for token in ("api_key", "token", "password", "secret")):
                if isinstance(item, str):
                    text = item.strip()
                    if text in {"yes", "no", "", "api_key", "api_key_or_plan"} or text.endswith("_API_KEY"):
                        sanitized[key] = text
                    else:
                        sanitized[key] = "<redacted>"
                else:
                    sanitized[key] = _redact_sensitive_fields(item)
            else:
                sanitized[key] = _redact_sensitive_fields(item)
        return sanitized
    if isinstance(value, list):
        return [_redact_sensitive_fields(item) for item in value]
    return value


def _artifact_state(path: Path, *, stale_after_days: int = 7) -> dict[str, Any]:
    if not path.exists():
        return {"path": str(path.relative_to(REPO_ROOT)), "status": "missing"}
    age_days = (datetime.now(UTC) - datetime.fromtimestamp(path.stat().st_mtime, tz=UTC)).days
    return {
        "path": str(path.relative_to(REPO_ROOT)),
        "status": "stale" if age_days > stale_after_days else "fresh",
        "age_days": age_days,
    }


def _build_priority_actions(report: dict[str, Any]) -> dict[str, list[str]]:
    metadata_candidates = [item["source"] for item in report["top_metadata_only_adapter_candidates"][:5]]
    use_case_gaps = report["use_case_coverage_gaps"]
    p0 = [
        "Run framework status (`python scripts/framework_status.py --write-doc --write-plan`).",
        "Regenerate coverage docs (`python scripts/generate_data_coverage_doc.py`).",
        "Run offline tutorial walkthrough (`python scripts/tutorial_mode.py --all --offline --write-doc`).",
        "Generate offline data health (`python scripts/data_health_report.py --source offline_fallback --symbol BTCUSDT --datasets kline funding --offline`).",
        "Record offline demo experiment (`python scripts/run_experiment.py --source offline_fallback --symbol BTCUSDT --strategy ema_cross_atr_stop --offline`).",
        "Dry-run executable recipe (`python scripts/run_recipe.py recipes/crypto_momentum.yaml --dry-run`).",
    ]
    if any(item["status"] != "fresh" for item in report["artifact_state"]):
        p0.append("Refresh stale or missing artifacts listed in the artifact state section.")
    p0.append("Run real-data smoke (`python scripts/e2e_real_data_smoke.py --interactive --allow-partial`).")
    p1 = [
        "Add and document recommend_sources / best_sources_for query recipes in tutorial and quickstart docs.",
        "Expose source and dataset explanation snippets in user-facing docs/notebooks.",
        "Keep capability, recommendation, and coverage indices synchronized with generated docs.",
        "Keep strategy catalog metadata synchronized with preflight checks and recipes.",
        "Document preflight/data-health/experiment workflow in tutorial and README.",
    ]
    p1.extend(
        f"Use-case gap: {item}"
        for item in use_case_gaps[:5]
    )
    p2 = [
        "Improve CoinGecko synthetic OHLCV transparency and dataset notes.",
        "Improve DefiLlama TVL/protocol metadata clarity for macro/fundamentals.",
        f"Reduce metadata-only adapters in priority order: {', '.join(metadata_candidates) if metadata_candidates else 'none'}.",
        "Complete missing strategy metadata entries in strategy catalog.",
    ]
    p2.extend(report["recommended_next_adapter_work"][:5])
    p3 = [
        "Expand data-quality checks and monitor quality issues over time.",
        "Harden backtest/risk/portfolio integration scenarios.",
        "Refine storage/provenance artifact layout and retention policy.",
        "Expand recipe coverage for additional multi-source and asset-class workflows.",
    ]
    return {"P0": p0, "P1": p1, "P2": p2, "P3": p3}


def _compute_score(report: dict[str, Any]) -> int:
    score = SCORE_BASE
    score += min(SCORE_COMPONENT_CAP, len(report["completed_components"]) * SCORE_COMPONENT_WEIGHT)
    score += min(SCORE_LIVE_CAP, report["coverage_summary"]["live_sources_count"])
    score += min(SCORE_FALLBACK_CAP, report["coverage_summary"]["fallback_sources_count"])
    score -= min(
        SCORE_METADATA_PENALTY_CAP,
        report["coverage_summary"]["metadata_only_sources_count"] * SCORE_METADATA_PENALTY_WEIGHT,
    )
    score -= min(
        SCORE_ARTIFACT_PENALTY_CAP,
        len([item for item in report["artifact_state"] if item["status"] in {"missing", "stale"}])
        * SCORE_ARTIFACT_PENALTY_WEIGHT,
    )
    return max(0, min(SCORE_MAX, score))


def _build_use_case_report(hub: DataHub) -> tuple[list[dict[str, Any]], list[str], list[str]]:
    coverage_rows: list[dict[str, Any]] = []
    gaps: list[str] = []
    adapter_work: list[str] = []
    for use_case in hub.supported_use_cases():
        public_recommendations = hub.recommend_sources(use_case, allow_api_key=False, limit=3)
        all_recommendations = hub.recommend_sources(use_case, allow_api_key=True, limit=3)
        if public_recommendations:
            status = "public_or_fallback"
        elif all_recommendations:
            status = "api_key_only"
            gaps.append(
                f"{use_case}: only API-key / plan-scoped recommendations available ({', '.join(item['source'] for item in all_recommendations[:2])})"
            )
        else:
            status = "uncovered"
            gaps.append(f"{use_case}: no current recommendation available")
        if status in {"api_key_only", "uncovered"} and all_recommendations:
            top = all_recommendations[0]
            adapter_work.append(
                f"Improve {top['source']} for {use_case} ({top['dataset']} -> {top['dataset_status']})"
            )
        coverage_rows.append(
            {
                "use_case": use_case,
                "status": status,
                "public_sources": [item["source"] for item in public_recommendations],
                "all_sources": [item["source"] for item in all_recommendations],
            }
        )
    return coverage_rows, gaps, adapter_work


def build_status_report() -> dict[str, Any]:
    hub = DataHub()
    coverage_rows = hub.coverage_table()
    summaries = [hub.source_summary(source) for source in hub.sources()]
    use_case_rows, use_case_gaps, recommended_adapter_work = _build_use_case_report(hub)
    status_counter = Counter(str(summary["implementation_status"]) for summary in summaries)
    missing_notebooks = [name for name in REQUIRED_NOTEBOOKS if not (REPO_ROOT / "notebooks" / name).exists()]
    unsupported_probe = hub.ingest(
        source="offline_fallback",
        symbol="BTCUSDT",
        datasets=["news"],
        allow_partial=True,
        store=False,
    )
    metadata_candidates = []
    for summary in summaries:
        metadata_count = len(summary["metadata_only_datasets"])
        if metadata_count == 0 and summary["implementation_status"] != "metadata_only":
            continue
        metadata_candidates.append(
            {
                "source": summary["source"],
                "metadata_only_dataset_count": metadata_count,
                "implementation_status": summary["implementation_status"],
            }
        )
    metadata_candidates.sort(
        key=lambda item: (-item["metadata_only_dataset_count"], str(item["source"]))
    )

    components = {
        "DataHub": {
            "done": all(
                hasattr(hub, name)
                for name in (
                    "dataset_status",
                    "sources_for",
                    "compare_sources",
                    "source_summary",
                    "best_sources_for",
                    "recommend_sources",
                    "explain_source",
                    "explain_dataset",
                )
            ),
            "detail": "Capability query API and ETL facade are available.",
        },
        "adapters": {
            "done": len(hub.sources()) >= 10,
            "detail": f"{len(hub.sources())} registered sources via adapter registry.",
        },
        "coverage docs": {
            "done": (REPO_ROOT / "docs" / "data_source_coverage.md").exists(),
            "detail": "Generated data source coverage document is present.",
        },
        "notebooks": {
            "done": not missing_notebooks,
            "detail": "Required tutorial/smoke notebooks present." if not missing_notebooks else f"Missing: {', '.join(missing_notebooks)}",
        },
        "strategy": {
            "done": (REPO_ROOT / "src" / "algotradeplan" / "plugins" / "strategies" / "ema_cross_atr_stop.py").exists(),
            "detail": "Example strategy/backtest integration exists.",
        },
        "backtest": {
            "done": (REPO_ROOT / "src" / "algotradeplan" / "backtest" / "realistic.py").exists(),
            "detail": "Realistic backtester with summary metrics exists.",
        },
        "risk": {
            "done": (REPO_ROOT / "src" / "algotradeplan" / "plugins" / "risk" / "engine.py").exists(),
            "detail": "Structured RiskEngine exists.",
        },
        "execution": {
            "done": (REPO_ROOT / "src" / "algotradeplan" / "plugins" / "connectors" / "simulated_fill_connector.py").exists(),
            "detail": "Simulated execution connector exists.",
        },
        "portfolio": {
            "done": (REPO_ROOT / "src" / "algotradeplan" / "portfolio" / "manager.py").exists(),
            "detail": "PortfolioManager and ledger exist.",
        },
        "docs": {
            "done": (REPO_ROOT / "docs" / "tutorial.md").exists(),
            "detail": "Tutorial guide present." if (REPO_ROOT / "docs" / "tutorial.md").exists() else "Tutorial guide missing.",
        },
        "research/preflight": {
            "done": (REPO_ROOT / "src" / "algotradeplan" / "research" / "preflight.py").exists(),
            "detail": "Preflight runnability checks available.",
        },
        "data_health_report": {
            "done": (REPO_ROOT / "scripts" / "data_health_report.py").exists(),
            "detail": "Dataset health report CLI available.",
        },
        "strategy_catalog": {
            "done": (REPO_ROOT / "docs" / "strategy_catalog.md").exists(),
            "detail": "Strategy capability catalog document available.",
        },
        "experiment_registry": {
            "done": (REPO_ROOT / "src" / "algotradeplan" / "research" / "experiments.py").exists(),
            "detail": "Experiment artifact registry available.",
        },
        "recipes": {
            "done": (REPO_ROOT / "scripts" / "run_recipe.py").exists() and (REPO_ROOT / "recipes").exists(),
            "detail": "Executable recipe runner and sample recipe folder available.",
        },
    }
    artifact_state = [_artifact_state(path) for path in ARTIFACT_PATHS.values()]
    missing_tests = [str(path.relative_to(REPO_ROOT)) for path in EXPECTED_TESTS if not path.exists()]

    risks = [
        "API-key and plan-scoped providers can report broader theoretical coverage than current implemented datasets.",
        "Real-data examples remain sensitive to upstream API availability and throttling.",
    ]

    report: dict[str, Any] = {
        "generated_at": datetime.now(UTC).isoformat(),
        "components": components,
        "completed_components": [name for name, item in components.items() if item["done"]],
        "pending_components": [name for name, item in components.items() if not item["done"]],
        "risks": risks,
        "coverage_summary": {
            "source_count": len(coverage_rows),
            "live_sources_count": status_counter.get("live", 0),
            "api_key_sources_count": status_counter.get("api_key", 0) + status_counter.get("api_key_or_plan", 0),
            "metadata_only_sources_count": len(metadata_candidates),
            "fallback_sources_count": status_counter.get("fallback", 0),
            "use_case_public_coverage_count": len([row for row in use_case_rows if row["status"] == "public_or_fallback"]),
            "unsupported_dataset_requests_behavior": unsupported_probe.source_issues,
        },
        "top_metadata_only_adapter_candidates": metadata_candidates[:10],
        "use_case_coverage": use_case_rows,
        "use_case_coverage_gaps": use_case_gaps,
        "recommended_next_adapter_work": recommended_adapter_work,
        "artifact_state": artifact_state,
        "missing_expected_tests": missing_tests,
        "validation_commands": [
            "make lint",
            "make test",
            "make smoke",
            "make runbook_check",
            "python scripts/framework_status.py --write-doc --write-plan",
            "python scripts/generate_data_coverage_doc.py",
            "python scripts/tutorial_mode.py --all --offline --write-doc",
            "python scripts/preflight_check.py --source coingecko --symbol bitcoin --datasets kline funding --strategy ema_cross_atr_stop",
            "python scripts/data_health_report.py --source offline_fallback --symbol BTCUSDT --datasets kline funding --offline",
            "python scripts/run_experiment.py --source offline_fallback --symbol BTCUSDT --strategy ema_cross_atr_stop --offline",
            "python scripts/run_recipe.py recipes/crypto_momentum.yaml --dry-run",
            "python scripts/e2e_real_data_smoke.py --interactive --allow-partial",
        ],
    }
    report["priority_actions"] = _build_priority_actions(report)
    report["next_actions"] = [f"[{priority}] {item}" for priority in ("P0", "P1", "P2", "P3") for item in report["priority_actions"][priority]]
    report["framework_score"] = _compute_score(report)
    return report


def render_next_actions_markdown(report: dict[str, Any]) -> str:
    sanitized = _redact_sensitive_fields(report)
    priorities = sanitized["priority_actions"]
    use_case_gaps = (
        "\n".join(f"- {item}" for item in sanitized["use_case_coverage_gaps"])
        if sanitized["use_case_coverage_gaps"]
        else "\n- _none_"
    )
    return (
        "# Next Actions\n\n"
        "## P0 - Validation / Artifacts\n"
        + "\n".join(f"- {item}" for item in priorities["P0"])
        + "\n\n## P1 - Capability UX\n"
        + "\n".join(f"- {item}" for item in priorities["P1"])
        + "\n\n## P2 - Reduce metadata-only adapters\n"
        + "\n".join(f"- {item}" for item in priorities["P2"])
        + "\n\n## P3 - Production hardening\n"
        + "\n".join(f"- {item}" for item in priorities["P3"])
        + "\n\n## P1 - Use-case coverage gaps\n"
        + use_case_gaps
        + "\n"
    )


def render_markdown(report: dict[str, Any]) -> str:
    sanitized = _redact_sensitive_fields(report)
    components = sanitized["components"]
    lines = [
        "# Framework Status",
        "",
        f"Generated: {sanitized['generated_at']}",
        f"framework_score: {sanitized['framework_score']}/100",
        "",
        "## Module Status",
    ]
    for name, item in components.items():
        marker = "[x]" if item["done"] else "[ ]"
        lines.append(f"- {marker} **{name}** — {item['detail']}")
    lines.extend(
        [
            "",
            "## Completed Components",
            *[f"- {item}" for item in sanitized["completed_components"]],
            "",
            "## Pending Components",
            *([f"- {item}" for item in sanitized["pending_components"]] or ["- _none_"]),
            "",
            "## Priority Next Actions",
            "### P0",
            *[f"- {item}" for item in sanitized["priority_actions"]["P0"]],
            "### P1",
            *[f"- {item}" for item in sanitized["priority_actions"]["P1"]],
            "### P2",
            *[f"- {item}" for item in sanitized["priority_actions"]["P2"]],
            "### P3",
            *[f"- {item}" for item in sanitized["priority_actions"]["P3"]],
            "",
             "## Top Metadata-only Adapter Candidates",
             *[
                 f"- {item['source']} (metadata_only_datasets={item['metadata_only_dataset_count']}, status={item['implementation_status']})"
                 for item in sanitized["top_metadata_only_adapter_candidates"]
             ],
             "",
             "## Recommended next adapter work",
             *([f"- {item}" for item in sanitized["recommended_next_adapter_work"]] or ["- _none_"]),
             "",
             "## Use-case coverage gaps",
             *([f"- {item}" for item in sanitized["use_case_coverage_gaps"]] or ["- _none_"]),
             "",
             "## Artifact State",
             *[
                f"- {item['path']}: {item['status']}"
                + (f" ({item['age_days']}d old)" if "age_days" in item else "")
                for item in sanitized["artifact_state"]
            ],
        ]
    )
    lines.extend(
        [
            "",
            "## Risks / Technical Debt",
            *[f"- {item}" for item in sanitized["risks"]],
            "",
            "## Coverage Summary",
            f"- source count: {sanitized['coverage_summary']['source_count']}",
            f"- live sources count: {sanitized['coverage_summary']['live_sources_count']}",
             f"- api_key sources count: {sanitized['coverage_summary']['api_key_sources_count']}",
             f"- metadata_only sources count: {sanitized['coverage_summary']['metadata_only_sources_count']}",
             f"- fallback sources count: {sanitized['coverage_summary']['fallback_sources_count']}",
             f"- public/fallback use-case coverage count: {sanitized['coverage_summary']['use_case_public_coverage_count']}",
             f"- unsupported dataset requests behavior: {json.dumps(sanitized['coverage_summary']['unsupported_dataset_requests_behavior'])}",
             "",
             "## Validation Commands",
            *[f"- `{item}`" for item in sanitized["validation_commands"]],
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--next-actions-only", action="store_true")
    parser.add_argument("--score", action="store_true")
    parser.add_argument("--write-plan", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--write-doc", action="store_true")
    args = parser.parse_args()

    report = build_status_report()
    sanitized_report = _redact_sensitive_fields(report)
    if args.write_plan:
        PLAN_PATH.write_text(render_next_actions_markdown(sanitized_report), encoding="utf-8")
    if args.write_doc:
        DOC_PATH.write_text(render_markdown(sanitized_report), encoding="utf-8")
    if args.score:
        print(f"framework_score: {sanitized_report['framework_score']}/100")
        if not any((args.next_actions_only, args.json)):
            return
    if args.next_actions_only:
        priorities = sanitized_report["priority_actions"]
        numbered = [
            item
            for priority in ("P0", "P1", "P2", "P3")
            for item in [f"[{priority}] {entry}" for entry in priorities[priority]]
        ]
        for index, item in enumerate(numbered, start=1):
            print(f"{index}. {item}")
        if not args.json:
            return
    if args.json:
        print(json.dumps(sanitized_report, indent=2))
        return
    print(render_markdown(sanitized_report))


if __name__ == "__main__":
    main()
