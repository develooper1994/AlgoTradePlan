"""Strategy plugin used by autonomous real-data smoke flow."""

from __future__ import annotations

from typing import Any


class AutopilotSignalStrategyPlugin:
    plugin_id = "autopilot_signal_strategy"

    def __init__(self, signal_action: str) -> None:
        self._signal_action = signal_action

    def generate_signal(self, context: dict[str, Any]) -> dict[str, Any]:
        return {"action": self._signal_action, "context": context}
