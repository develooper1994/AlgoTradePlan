"""Common immutable data types."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StrategyTarget:
    strategy_id: str
    symbol: str
    target_exposure: float
