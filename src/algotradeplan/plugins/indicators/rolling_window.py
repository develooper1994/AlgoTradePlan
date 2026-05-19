"""Rolling-window indicator engine (EMA, ATR, Bollinger)."""

from __future__ import annotations

import math
from dataclasses import dataclass


def ema(values: list[float], window: int) -> list[float]:
    if not values or window <= 0:
        return []
    alpha = 2.0 / (window + 1.0)
    result = [float(values[0])]
    for value in values[1:]:
        result.append((float(value) * alpha) + (result[-1] * (1 - alpha)))
    return result


def atr(highs: list[float], lows: list[float], closes: list[float], window: int) -> list[float]:
    if not highs or not lows or not closes or window <= 0:
        return []
    true_ranges: list[float] = []
    previous_close = closes[0]
    for high, low, close in zip(highs, lows, closes):
        high = float(high)
        low = float(low)
        close = float(close)
        true_ranges.append(max(high - low, abs(high - previous_close), abs(low - previous_close)))
        previous_close = close
    return ema(true_ranges, window)


def bollinger_bands(values: list[float], window: int, deviation: float = 2.0) -> list[dict[str, float]]:
    if not values or window <= 1:
        return []
    result: list[dict[str, float]] = []
    for index in range(len(values)):
        start = max(0, index - window + 1)
        subset = [float(value) for value in values[start : index + 1]]
        mean = sum(subset) / len(subset)
        variance = sum((value - mean) ** 2 for value in subset) / len(subset)
        sigma = math.sqrt(variance)
        result.append(
            {
                "mid": mean,
                "upper": mean + (deviation * sigma),
                "lower": mean - (deviation * sigma),
            }
        )
    return result


@dataclass(frozen=True)
class RollingFeatureSnapshot:
    ema_fast: float
    ema_slow: float
    atr: float
    bollinger_mid: float
    bollinger_upper: float
    bollinger_lower: float


class RollingWindowFeatureEngine:
    plugin_id = "rolling_window_feature_engine"

    def compute(
        self,
        *,
        highs: list[float],
        lows: list[float],
        closes: list[float],
        ema_fast_window: int = 8,
        ema_slow_window: int = 21,
        atr_window: int = 14,
        bollinger_window: int = 20,
    ) -> RollingFeatureSnapshot:
        ema_fast_series = ema(closes, ema_fast_window)
        ema_slow_series = ema(closes, ema_slow_window)
        atr_series = atr(highs, lows, closes, atr_window)
        bollinger_series = bollinger_bands(closes, bollinger_window)
        if not ema_fast_series or not ema_slow_series or not atr_series or not bollinger_series:
            return RollingFeatureSnapshot(
                ema_fast=0.0,
                ema_slow=0.0,
                atr=0.0,
                bollinger_mid=0.0,
                bollinger_upper=0.0,
                bollinger_lower=0.0,
            )
        latest_band = bollinger_series[-1]
        return RollingFeatureSnapshot(
            ema_fast=ema_fast_series[-1],
            ema_slow=ema_slow_series[-1],
            atr=atr_series[-1],
            bollinger_mid=latest_band["mid"],
            bollinger_upper=latest_band["upper"],
            bollinger_lower=latest_band["lower"],
        )
