"""Deprecated: storage moved to MarketData."""

from __future__ import annotations


class InMemoryStorage:
    def write(self, records):
        raise RuntimeError("Storage moved to MarketData.")


class LocalArtifactStorage:
    def __init__(self, root):
        self.root = root

    def write(self, records):
        raise RuntimeError("Storage moved to MarketData.")
