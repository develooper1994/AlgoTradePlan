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
                open_price = record.payload.get("open", 0.0)
                high_price = record.payload.get("high", 0.0)
                low_price = record.payload.get("low", 0.0)
                close_price = record.payload.get("close", 0.0)
                try:
                    open_value = float(open_price)
                    high_value = float(high_price)
                    low_value = float(low_price)
                    close_value = float(close_price)
                    if high_value < max(open_value, close_value):
                        issues.append(f"Inconsistent OHLC high in {record.key}")
                    if low_value > min(open_value, close_value):
                        issues.append(f"Inconsistent OHLC low in {record.key}")
                    if high_value < low_value:
                        issues.append(f"Inconsistent OHLC range in {record.key}")
                except (TypeError, ValueError):
                    issues.append(f"Non-numeric OHLC values in {record.key}")
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
