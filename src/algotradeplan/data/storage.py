"""Deprecated: storage moved to MarketData."""

from __future__ import annotations

from src.algotradeplan.data.errors import DataLayerMigrationError


class InMemoryStorage:
    def write(self, records):
        raise DataLayerMigrationError("Storage moved to MarketData.")


class LocalArtifactStorage:
    def __init__(self, root):
        del root
        raise DataLayerMigrationError("Storage moved to MarketData.")

    def write(self, records):
        raise DataLayerMigrationError("Storage moved to MarketData.")
