"""Coverage helpers are delegated to MarketData bridge via DataHub wrappers."""

from __future__ import annotations

from typing import Any

from src.algotradeplan.data import DataHub

DATASET_COLUMNS: tuple[str, ...] = tuple()
ASSET_COLUMNS: tuple[str, ...] = tuple()


def dataset_status(*_args: Any, **_kwargs: Any) -> str:
    raise RuntimeError("dataset_status moved to MarketData bridge; use DataHub.dataset_status().")


def asset_status(*_args: Any, **_kwargs: Any) -> str:
    raise RuntimeError("asset_status moved to MarketData bridge; use DataHub.asset_status().")


def build_coverage_table(*_args: Any, **_kwargs: Any) -> list[dict[str, str]]:
    return DataHub().coverage_table()
