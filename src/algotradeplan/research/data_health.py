from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from src.algotradeplan.data import DataHub
from src.algotradeplan.marketdata_client import MarketDataBridgeError


@dataclass(frozen=True)
class DataHealthReport:
    source: str
    symbol: str
    datasets: list[str]
    dataset_coverage_count: int
    record_count: int
    source_issues: list[str]
    quality_passed: bool
    quality_checks: list[str]
    quality_issues: list[str]
    duplicate_timestamp_issues_count: int
    non_monotonic_timestamp_issues_count: int
    ohlc_consistency_issue_count: int
    negative_value_issue_count: int
    missing_required_field_issue_count: int
    per_dataset_record_counts: dict[str, int]
    health_score: int
    generated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_markdown(self) -> str:
        return (
            "# Data Health Report\n\n"
            f"- generated_at: `{self.generated_at}`\n"
            f"- source: `{self.source}`\n"
            f"- symbol: `{self.symbol}`\n"
            f"- datasets: `{self.datasets}`\n"
            f"- dataset_coverage_count: `{self.dataset_coverage_count}`\n"
            f"- record_count: `{self.record_count}`\n"
            f"- quality_passed: `{self.quality_passed}`\n"
            f"- health_score: `{self.health_score}`\n\n"
            "## Dataset coverage\n\n"
            f"`{self.per_dataset_record_counts}`\n\n"
            "## Source issues\n\n"
            f"`{self.source_issues}`\n\n"
            "## Quality checks\n\n"
            f"`{self.quality_checks}`\n\n"
            "## Quality issues\n\n"
            f"`{self.quality_issues}`\n\n"
            "## Issue counters\n\n"
            f"- duplicate_timestamp_issues_count: `{self.duplicate_timestamp_issues_count}`\n"
            f"- non_monotonic_timestamp_issues_count: `{self.non_monotonic_timestamp_issues_count}`\n"
            f"- ohlc_consistency_issue_count: `{self.ohlc_consistency_issue_count}`\n"
            f"- negative_value_issue_count: `{self.negative_value_issue_count}`\n"
            f"- missing_required_field_issue_count: `{self.missing_required_field_issue_count}`\n"
        )


def generate_data_health_report(
    *,
    hub: DataHub | None = None,
    source: str,
    symbol: str,
    datasets: list[str],
    allow_partial: bool = False,
) -> DataHealthReport:
    selected_hub = hub or DataHub()
    try:
        ingest = selected_hub.ingest(
            source=source,
            symbol=symbol,
            datasets=datasets,
            allow_partial=allow_partial,
            store=False,
        )
    except MarketDataBridgeError as exc:
        ingest = _bridge_error_ingest(datasets=datasets, issue=str(exc))
    quality_issues = list(ingest.quality_report.issues)
    source_issues = [str(item.get("reason", "")) for item in ingest.source_issues]
    per_dataset = {name: int(count) for name, count in ingest.dataset_coverage.items()}
    dataset_coverage_count = len([count for count in per_dataset.values() if count > 0])

    duplicate_count = len([issue for issue in quality_issues if "Duplicate timestamp" in issue])
    non_monotonic_count = len([issue for issue in quality_issues if "Non-monotonic timestamps" in issue])
    ohlc_count = len([issue for issue in quality_issues if "Inconsistent OHLC" in issue])
    negative_count = len([issue for issue in quality_issues if issue.startswith("Negative")])
    missing_required_count = len([issue for issue in quality_issues if "missing required" in issue.lower()])

    health_score = _health_score(
        quality_issues=quality_issues,
        source_issues=source_issues,
        per_dataset=per_dataset,
        requested_count=len(datasets),
    )

    return DataHealthReport(
        source=source,
        symbol=symbol,
        datasets=list(datasets),
        dataset_coverage_count=dataset_coverage_count,
        record_count=len(ingest.records),
        source_issues=source_issues,
        quality_passed=ingest.quality_report.passed,
        quality_checks=list(ingest.quality_report.checks),
        quality_issues=quality_issues,
        duplicate_timestamp_issues_count=duplicate_count,
        non_monotonic_timestamp_issues_count=non_monotonic_count,
        ohlc_consistency_issue_count=ohlc_count,
        negative_value_issue_count=negative_count,
        missing_required_field_issue_count=missing_required_count,
        per_dataset_record_counts=per_dataset,
        health_score=health_score,
    )


def write_data_health_markdown(report: DataHealthReport, *, root: Path | None = None) -> Path:
    artifact_root = root or Path("artifacts") / "data_health"
    artifact_root.mkdir(parents=True, exist_ok=True)
    safe_symbol = report.symbol.replace("/", "_").replace(" ", "_")
    path = artifact_root / f"{report.source}_{safe_symbol}_health.md"
    path.write_text(report.to_markdown(), encoding="utf-8")
    return path


def _health_score(*, quality_issues: list[str], source_issues: list[str], per_dataset: dict[str, int], requested_count: int) -> int:
    score = 100
    score -= min(40, len(quality_issues) * 4)
    score -= min(30, len(source_issues) * 10)
    missing_datasets = requested_count - len([count for count in per_dataset.values() if count > 0])
    score -= max(0, missing_datasets) * 8
    return max(0, min(100, score))


@dataclass(frozen=True)
class _BridgeUnavailableQuality:
    passed: bool
    checks: list[str]
    issues: list[str]


@dataclass(frozen=True)
class _BridgeUnavailableIngest:
    dataset_coverage: dict[str, int]
    records: list[object]
    source_issues: list[dict[str, str]]
    quality_report: _BridgeUnavailableQuality


def _bridge_error_ingest(*, datasets: list[str], issue: str):
    return _BridgeUnavailableIngest(
        dataset_coverage={name: 0 for name in datasets},
        records=[],
        source_issues=[{"source": "marketdata_bridge", "reason": issue}],
        quality_report=_BridgeUnavailableQuality(
            passed=False,
            checks=["marketdata_bridge_available"],
            issues=[issue],
        ),
    )
