"""Deprecated: normalization moved to MarketData."""

from __future__ import annotations

from typing import Any


def normalize_dataset(*_args: Any, **_kwargs: Any) -> list[dict[str, Any]]:
    raise RuntimeError("Normalization moved to MarketData; use MarketData ingest/load APIs.")


def to_data_records(*_args: Any, **_kwargs: Any):
    raise RuntimeError("Record conversion moved to MarketData; use MarketData ingest output directly.")
