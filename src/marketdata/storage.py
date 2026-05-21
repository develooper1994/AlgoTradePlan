"""Deprecated compatibility wrapper for storage plugins."""

from src.algotradeplan.data.storage import InMemoryStorage, LocalArtifactStorage

__all__ = ["InMemoryStorage", "LocalArtifactStorage"]
