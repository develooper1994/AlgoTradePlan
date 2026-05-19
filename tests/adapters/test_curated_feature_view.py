from __future__ import annotations

import unittest

from src.algotradeplan.plugins.data.contracts import DataRequest
from src.algotradeplan.plugins.data.curated.feature_view import ExampleFeatureViewPlugin
from src.algotradeplan.plugins.data.example_data_storage import InMemoryDataStoragePlugin
from src.algotradeplan.plugins.data.example_provenance import ExampleProvenancePlugin
from src.algotradeplan.plugins.data.example_quality_check import RequiredFieldsQualityPlugin
from src.algotradeplan.plugins.data.market.example_market_source import ExampleMarketDataSource
from src.algotradeplan.plugins.data.pipeline import DataIngestionPipeline


class CuratedFeatureViewTest(unittest.TestCase):
    def _ingest(self) -> tuple[list, object]:
        pipeline = DataIngestionPipeline(
            source=ExampleMarketDataSource(),
            storage=InMemoryDataStoragePlugin(),
            quality=RequiredFieldsQualityPlugin(),
            provenance=ExampleProvenancePlugin(),
        )
        result = pipeline.ingest(DataRequest(dataset="daily_bars", symbol="AAPL"))
        return result.records, result.provenance

    def test_curated_feature_records_link_to_upstream_provenance(self) -> None:
        records, provenance = self._ingest()
        view = ExampleFeatureViewPlugin().build(records, provenance)

        self.assertEqual(len(view.feature_records), 1)
        feature = view.feature_records[0]
        self.assertEqual(feature.domain, "curated")
        self.assertEqual(feature.metadata["lake_zone"], "curated")
        self.assertEqual(feature.metadata["upstream_revision"], provenance.revision)
        self.assertEqual(
            feature.metadata["upstream_source_plugin_id"], provenance.source_plugin_id
        )
        self.assertIn(provenance.revision, view.upstream_revisions)

    def test_feature_generation_is_deterministic_and_replayable(self) -> None:
        records, provenance = self._ingest()
        plugin = ExampleFeatureViewPlugin()
        first = plugin.build(records, provenance)
        second = plugin.build(records, provenance)
        self.assertEqual(first.feature_records, second.feature_records)


if __name__ == "__main__":
    unittest.main()
