"""Plugin interface definitions."""

from __future__ import annotations

from typing import Any, Protocol


class StrategyPlugin(Protocol):
    plugin_id: str

    def generate_signal(self, context: dict[str, Any]) -> dict[str, Any]:
        """Return signal payload for downstream validation."""
