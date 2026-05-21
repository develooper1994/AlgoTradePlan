from __future__ import annotations

import json
import os
import shlex
import subprocess
from typing import Any, Callable

Runner = Callable[..., subprocess.CompletedProcess[str]]


class MarketDataBridgeError(RuntimeError):
    """Raised when MarketData bridge invocation fails."""


class MarketDataBridgeClient:
    """Thin subprocess client for the external MarketData bridge binary."""

    def __init__(
        self,
        *,
        bridge_bin: str | None = None,
        runner: Runner | None = None,
    ) -> None:
        self._bridge_bin = bridge_bin or os.getenv("MARKET_DATA_BIN") or "market_data_bridge"
        self._runner = runner or subprocess.run

    def invoke(
        self,
        operation: str,
        payload: dict[str, Any] | None = None,
        *,
        default: Any = None,
        allow_missing: bool = False,
    ) -> Any:
        request_payload = payload or {}
        command = [*shlex.split(self._bridge_bin), operation, "--json"]
        try:
            result = self._runner(
                command,
                input=json.dumps(request_payload),
                capture_output=True,
                text=True,
                check=False,
            )
        except FileNotFoundError as exc:
            if allow_missing:
                return default
            raise MarketDataBridgeError(
                "MarketData bridge binary not found. Set MARKET_DATA_BIN to a valid bridge executable."
            ) from exc

        if result.returncode != 0:
            if allow_missing:
                return default
            stderr = (result.stderr or "").strip()
            raise MarketDataBridgeError(
                f"MarketData bridge operation '{operation}' failed with exit code {result.returncode}: {stderr}"
            )

        raw = (result.stdout or "").strip()
        if not raw:
            return default
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise MarketDataBridgeError(
                f"MarketData bridge operation '{operation}' returned invalid JSON output"
            ) from exc

        if isinstance(parsed, dict) and "result" in parsed and len(parsed) == 1:
            parsed = parsed["result"]
        return parsed

    def query(self, operation: str, payload: dict[str, Any] | None = None, *, default: Any) -> Any:
        return self.invoke(operation, payload, default=default, allow_missing=True)


__all__ = ["MarketDataBridgeClient", "MarketDataBridgeError"]
