"""Deprecated: quality validation moved to MarketData."""

from __future__ import annotations


class CanonicalDataQualityPlugin:
    def validate(self, records):
        raise RuntimeError("Quality validation moved to MarketData.")
