"""Strategies plugin examples."""

from src.algotradeplan.plugins.strategies.autopilot_signal_strategy import (
    AutopilotSignalStrategyPlugin,
)
from src.algotradeplan.plugins.strategies.ema_cross_atr_stop import (
    EmaAtrParams,
    EmaCrossAtrStopStrategyPlugin,
)

__all__ = ["AutopilotSignalStrategyPlugin", "EmaCrossAtrStopStrategyPlugin", "EmaAtrParams"]
