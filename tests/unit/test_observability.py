from __future__ import annotations

import json
import unittest

from src.algotradeplan.observability import (
    InMemoryMetricsSink,
    StructuredLogger,
)


class StructuredLoggerTest(unittest.TestCase):
    def test_logger_redacts_sensitive_fields_and_preserves_correlation(self) -> None:
        logger = StructuredLogger(correlation_id="corr-123")
        entry = logger.info(
            "auth.attempt",
            user="alice",
            credentials={"password": "p@ss", "token": "tk", "scope": "read"},
        )

        self.assertEqual(entry.correlation_id, "corr-123")
        self.assertEqual(entry.fields["credentials"]["password"], "***")
        self.assertEqual(entry.fields["credentials"]["token"], "***")
        self.assertEqual(entry.fields["credentials"]["scope"], "read")

    def test_logger_serializes_entries_deterministically(self) -> None:
        logger = StructuredLogger(correlation_id="corr-abc")
        first = logger.info("evt", b=2, a=1).to_json()
        second = logger.info("evt", a=1, b=2).to_json()
        self.assertEqual(json.loads(first)["fields"], json.loads(second)["fields"])

    def test_metric_sink_aggregates_by_name(self) -> None:
        sink = InMemoryMetricsSink()
        sink.record("ingest.batches", 1, domain="market")
        sink.record("ingest.batches", 2, domain="news")
        sink.record("ingest.errors", 1, domain="market")

        self.assertEqual(sink.total("ingest.batches"), 3.0)
        self.assertEqual(sink.total("ingest.errors"), 1.0)


if __name__ == "__main__":
    unittest.main()
