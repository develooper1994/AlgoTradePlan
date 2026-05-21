"""Deprecated: quality validation moved to MarketData."""

from __future__ import annotations

from src.algotradeplan.data.errors import DataLayerMigrationError


class CanonicalDataQualityPlugin:
    def validate(self, records):
        raise DataLayerMigrationError("Quality validation moved to MarketData.")
