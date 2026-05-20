from __future__ import annotations

import argparse
import json
import pathlib
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.algotradeplan.data import DataHub

DOC_PATH = REPO_ROOT / "docs" / "framework_status.md"
REQUIRED_NOTEBOOKS = [
    "00_framework_tutorial.ipynb",
    "01_real_data_smoke.ipynb",
    "02_strategy_backtest_portfolio.ipynb",
    "03_multi_source_asset_coverage.ipynb",
]
EXPECTED_TESTS = [
    REPO_ROOT / "tests" / "unit" / "test_data_api.py",
    REPO_ROOT / "tests" / "unit" / "test_framework_scripts.py",
]


def _redact_sensitive_fields(value: object) -> object:
    if isinstance(value, dict):
        sanitized: dict[object, object] = {}
        for key, item in value.items():
            lowered = str(key).lower()
            if any(token in lowered for token in ("api_key", "token", "password", "secret")):
                sanitized[key] = "<redacted>"
            else:
                sanitized[key] = _redact_sensitive_fields(item)
        return sanitized
    if isinstance(value, list):
        return [_redact_sensitive_fields(item) for item in value]
    return value


def build_status_report() -> dict[str, object]:
    hub = DataHub()
    coverage_rows = hub.coverage_table()
    summaries = [hub.source_summary(source) for source in hub.sources()]
    status_counter = Counter(str(summary["implementation_status"]) for summary in summaries)
    missing_notebooks = [name for name in REQUIRED_NOTEBOOKS if not (REPO_ROOT / "notebooks" / name).exists()]
    unsupported_probe = hub.ingest(
        source="offline_fallback",
        symbol="BTCUSDT",
        datasets=["news"],
        allow_partial=True,
        store=False,
    )

    components = {
        "DataHub": {
            "done": all(hasattr(hub, name) for name in ("dataset_status", "sources_for", "compare_sources", "source_summary")),
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
    }

    next_actions: list[str] = []
    if not (REPO_ROOT / "docs" / "data_source_coverage.md").exists():
        next_actions.append("Generate coverage documentation with `python scripts/generate_data_coverage_doc.py`.")
    if not (REPO_ROOT / "docs" / "tutorial.md").exists():
        next_actions.append("Create or refresh `docs/tutorial.md` for the offline and notebook tutorial flow.")
    if missing_notebooks:
        next_actions.append(f"Create or update missing notebooks: {', '.join(missing_notebooks)}.")
    metadata_heavy = [
        summary["source"]
        for summary in summaries
        if summary["metadata_only_datasets"] or summary["implementation_status"] == "metadata_only"
    ]
    if metadata_heavy:
        next_actions.append(
            "Reduce metadata-only coverage by extending adapters for: " + ", ".join(metadata_heavy[:5]) + "."
        )
    missing_tests = [str(path.relative_to(REPO_ROOT)) for path in EXPECTED_TESTS if not path.exists()]
    if missing_tests:
        next_actions.append("Add or restore targeted tests: " + ", ".join(missing_tests) + ".")
    if not (REPO_ROOT / "artifacts" / "real_data_smoke_report.json").exists():
        next_actions.append("Run `python scripts/e2e_real_data_smoke.py --interactive --allow-partial` to refresh the E2E smoke artifact.")
    if not next_actions:
        next_actions.append("Run full validation (`make lint && make test && make smoke && make runbook_check`) and then extend the next metadata-only adapter.")

    risks = [
        "API-key and plan-scoped providers can report broader theoretical coverage than current implemented datasets.",
        "Real-data examples remain sensitive to upstream API availability and throttling.",
    ]

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "components": components,
        "completed": [name for name, item in components.items() if item["done"]],
        "pending": [name for name, item in components.items() if not item["done"]],
        "next_actions": next_actions,
        "risks": risks,
        "coverage_summary": {
            "source_count": len(coverage_rows),
            "live_sources_count": status_counter.get("live", 0),
            "api_key_sources_count": status_counter.get("api_key", 0) + status_counter.get("api_key_or_plan", 0),
            "metadata_only_sources_count": len(metadata_heavy),
            "fallback_sources_count": status_counter.get("fallback", 0),
            "unsupported_dataset_requests_behavior": unsupported_probe.source_issues,
        },
    }


def render_markdown(report: dict[str, object]) -> str:
    components = report["components"]
    lines = [
        "# Framework Status",
        "",
        f"Generated: {report['generated_at']}",
        "",
        "## Module Status",
    ]
    for name, item in components.items():
        marker = "[x]" if item["done"] else "[ ]"
        lines.append(f"- {marker} **{name}** — {item['detail']}")
    lines.extend(
        [
            "",
            "## Next Actions",
            *[f"- {item}" for item in report["next_actions"]],
            "",
            "## Risks / Technical Debt",
            *[f"- {item}" for item in report["risks"]],
            "",
            "## Coverage Summary",
            f"- live sources count: {report['coverage_summary']['live_sources_count']}",
            f"- api_key sources count: {report['coverage_summary']['api_key_sources_count']}",
            f"- metadata_only sources count: {report['coverage_summary']['metadata_only_sources_count']}",
            f"- fallback sources count: {report['coverage_summary']['fallback_sources_count']}",
            f"- unsupported dataset requests behavior: {json.dumps(report['coverage_summary']['unsupported_dataset_requests_behavior'])}",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--write-doc", action="store_true")
    args = parser.parse_args()

    report = build_status_report()
    if args.write_doc:
        DOC_PATH.write_text(render_markdown(report), encoding="utf-8")
    if args.json:
        print(json.dumps(_redact_sensitive_fields(report), indent=2))
        return
    print(render_markdown(report))


if __name__ == "__main__":
    main()
