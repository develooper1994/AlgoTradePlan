from __future__ import annotations

import json
import unittest
from pathlib import Path
from typing import Any

from src.algotradeplan.plugins.data.contracts import DataRequest
from src.algotradeplan.plugins.data.example_data_storage import InMemoryDataStoragePlugin
from src.algotradeplan.plugins.data.example_provenance import ExampleProvenancePlugin
from src.algotradeplan.plugins.data.example_quality_check import RequiredFieldsQualityPlugin
from src.algotradeplan.plugins.data.macro.example_macro_source import ExampleMacroDataSource
from src.algotradeplan.plugins.data.market.example_market_source import ExampleMarketDataSource
from src.algotradeplan.plugins.data.news.example_news_source import ExampleNewsDataSource
from src.algotradeplan.plugins.data.pipeline import DataIngestionPipeline


class EmptyDataSource:
    plugin_id = "empty_data_source"
    domain = "market"

    def fetch(self, request: DataRequest) -> list[object]:
        del request
        return []


class DataIngestionPipelineExamplesTest(unittest.TestCase):
    FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"
    _DATA_INGESTION_SCENARIOS_CACHE: list[dict[str, Any]] | None = None

    @staticmethod
    def _load_data_ingestion_scenarios() -> list[dict[str, Any]]:
        if DataIngestionPipelineExamplesTest._DATA_INGESTION_SCENARIOS_CACHE is not None:
            return DataIngestionPipelineExamplesTest._DATA_INGESTION_SCENARIOS_CACHE
        fixtures_path = DataIngestionPipelineExamplesTest.FIXTURES_DIR / "data_ingestion_assets.json"
        with fixtures_path.open("r", encoding="utf-8") as fixture_file:
            fixture_payload = json.load(fixture_file)
        DataIngestionPipelineExamplesTest._DATA_INGESTION_SCENARIOS_CACHE = fixture_payload["scenarios"]
        return DataIngestionPipelineExamplesTest._DATA_INGESTION_SCENARIOS_CACHE

    def test_pipeline_supports_market_news_and_macro_plugins(self) -> None:
        scenarios = self._load_data_ingestion_scenarios()
        source_by_domain = {
            "market": ExampleMarketDataSource,
            "news": ExampleNewsDataSource,
            "macro": ExampleMacroDataSource,
        }

        for scenario in scenarios:
            source = source_by_domain[scenario["domain"]]()
            request = DataRequest(
                dataset=scenario["dataset"],
                symbol=scenario.get("symbol"),
                parameters=scenario.get("parameters", {}),
            )
            pipeline = DataIngestionPipeline(
                source=source,
                storage=InMemoryDataStoragePlugin(),
                quality=RequiredFieldsQualityPlugin(),
                provenance=ExampleProvenancePlugin(),
            )

            result = pipeline.ingest(request)

            self.assertTrue(result.quality_report.passed)
            self.assertEqual(result.records[0].domain, scenario["domain"])
            self.assertEqual(result.records[0].metadata["join_key"], scenario["expected_join_key"])
            self.assertEqual(result.provenance.source_plugin_id, source.plugin_id)
            self.assertEqual(result.storage_receipts[0].record_keys, [result.records[0].key])

    def test_pipeline_rejects_empty_batches(self) -> None:
        pipeline = DataIngestionPipeline(
            source=EmptyDataSource(),
            storage=InMemoryDataStoragePlugin(),
            quality=RequiredFieldsQualityPlugin(),
            provenance=ExampleProvenancePlugin(),
        )

        with self.assertRaisesRegex(ValueError, "Data quality validation failed"):
            pipeline.ingest(DataRequest(dataset="empty"))


if __name__ == "__main__":
    unittest.main()
