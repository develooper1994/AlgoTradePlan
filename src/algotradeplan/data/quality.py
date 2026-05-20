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
        grouped_timestamp_seen: dict[tuple[str, str], set[int]] = defaultdict(set)

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
                if timestamp_ms in grouped_timestamp_seen[(dataset, join_key)]:
                    issues.append(f"Duplicate timestamp for dataset={dataset} join_key={join_key}: {timestamp_ms}")
                grouped_timestamp_seen[(dataset, join_key)].add(timestamp_ms)

            if dataset == "kline":
                for field in ("open", "high", "low", "close"):
                    if record.payload.get(field) is None:
                        issues.append(f"OHLCV record missing {field}: {record.key}")
                numeric_values: dict[str, float] = {}
                for field in ("open", "high", "low", "close", "volume"):
                    try:
                        numeric_values[field] = float(record.payload.get(field, 0.0))
                    except (TypeError, ValueError):
                        issues.append(f"Non-numeric {field} in {record.key}")
                if all(field in numeric_values for field in ("open", "high", "low", "close")):
                    open_value = numeric_values["open"]
                    high_value = numeric_values["high"]
                    low_value = numeric_values["low"]
                    close_value = numeric_values["close"]
                    if high_value < max(open_value, close_value):
                        issues.append(f"Inconsistent OHLC high in {record.key}")
                    if low_value > min(open_value, close_value):
                        issues.append(f"Inconsistent OHLC low in {record.key}")
                    if high_value < low_value:
                        issues.append(f"Inconsistent OHLC range in {record.key}")
                else:
                    issues.append(f"Non-numeric OHLC values in {record.key}")
                for field, value in numeric_values.items():
                    if value < 0:
                        issues.append(f"Negative {field} in {record.key}")
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
