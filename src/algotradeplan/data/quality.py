"""Data quality checks for canonicalized DataHub records."""

from __future__ import annotations

from collections import defaultdict

from src.algotradeplan.plugins.data.contracts import DataRecord, QualityReport


class CanonicalDataQualityPlugin:
    plugin_id = "canonical_data_quality"

    def validate(self, records: list[DataRecord]) -> QualityReport:
        checks = [
            "records_present",
            "required_fields",
            "monotonic_timestamp",
            "duplicate_check",
            "non_null_ohlcv",
            "non_negative_values",
        ]
        issues: list[str] = []

        if not records:
            issues.append("No records fetched for request.")
            return QualityReport(passed=False, checks=checks, issues=issues)

        seen_keys: set[str] = set()
        grouped_timestamps: dict[tuple[str, str], list[int]] = defaultdict(list)

        for index, record in enumerate(records):
            if not record.key or not record.observed_at or not record.source or not record.asset_type:
                issues.append(f"Record {index} missing required metadata.")
            if record.key in seen_keys:
                issues.append(f"Duplicate record key detected: {record.key}")
            seen_keys.add(record.key)

            dataset = str(record.metadata.get("dataset", ""))
            join_key = str(record.metadata.get("join_key", ""))
            timestamp_ms = int(record.payload.get("timestamp_ms") or 0)
            if timestamp_ms:
                grouped_timestamps[(dataset, join_key)].append(timestamp_ms)

            if dataset == "kline":
                for field in ("open", "high", "low", "close"):
                    if record.payload.get(field) is None:
                        issues.append(f"OHLCV record missing {field}: {record.key}")
                for field in ("open", "high", "low", "close", "volume"):
                    value = record.payload.get(field, 0.0)
                    try:
                        if float(value) < 0:
                            issues.append(f"Negative {field} in {record.key}")
                    except (TypeError, ValueError):
                        issues.append(f"Non-numeric {field} in {record.key}")
            elif dataset == "trade":
                for field in ("price", "quantity"):
                    value = record.payload.get(field, 0.0)
                    if float(value) < 0:
                        issues.append(f"Negative {field} in {record.key}")
            elif dataset == "funding":
                if float(record.payload.get("rate", 0.0)) < -1.0:
                    issues.append(f"Funding rate below sanity floor in {record.key}")
            elif dataset == "orderbook":
                for side in ("bids", "asks"):
                    for level in record.payload.get(side, []):
                        if len(level) < 2 or float(level[0]) < 0 or float(level[1]) < 0:
                            issues.append(f"Invalid {side} level in {record.key}")

        for group, timestamps in grouped_timestamps.items():
            if timestamps != sorted(timestamps):
                issues.append(f"Non-monotonic timestamps for dataset={group[0]} join_key={group[1]}")

        return QualityReport(passed=not issues, checks=checks, issues=issues)
