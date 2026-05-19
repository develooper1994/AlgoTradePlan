"""Plugin interface definitions."""

from __future__ import annotations

from typing import Any, Protocol


class StrategyPlugin(Protocol):
    plugin_id: str

    def generate_signal(self, context: dict[str, Any]) -> dict[str, Any]:
        """Return signal payload for downstream validation."""


class DataPlugin(Protocol):
    plugin_id: str

    def fetch(self, symbol: str) -> dict[str, Any]:
        """Return normalized market payload."""


class RiskPlugin(Protocol):
    plugin_id: str

    def evaluate(self, order_intent: dict[str, Any]) -> dict[str, Any]:
        """Return risk decision payload."""


class ExecutionConnectorPlugin(Protocol):
    plugin_id: str

    def send_order(self, order: dict[str, Any]) -> dict[str, Any]:
        """Submit order to venue and return transport result."""


class ReconciliationPlugin(Protocol):
    plugin_id: str

    def reconcile(self, local_state: dict[str, Any], remote_state: dict[str, Any]) -> dict[str, Any]:
        """Compare local and venue state snapshots."""


class ModelPlugin(Protocol):
    plugin_id: str

    def predict(self, features: dict[str, Any]) -> dict[str, Any]:
        """Return model inference payload."""


class IndicatorPlugin(Protocol):
    plugin_id: str

    def compute(self, candles: list[dict[str, float]]) -> dict[str, float]:
        """Return derived indicator values."""
