"""Deprecated: provenance tracking moved to MarketData."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any


class ManifestProvenanceTracker:
    def __init__(self, *_args: Any, **_kwargs: Any) -> None:
        pass

    def capture(self, **_kwargs: Any):
        raise RuntimeError("Provenance tracking moved to MarketData.")


def provenance_to_dict(provenance: Any) -> dict[str, Any]:
    if provenance is None:
        return {}
    if is_dataclass(provenance):
        return asdict(provenance)
    if isinstance(provenance, dict):
        return provenance
    return {"value": str(provenance)}
