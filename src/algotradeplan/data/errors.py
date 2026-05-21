"""Data-layer migration exceptions."""

from __future__ import annotations


class DataLayerMigrationError(RuntimeError):
    """Raised when removed AlgoTradePlan data-layer internals are accessed."""
