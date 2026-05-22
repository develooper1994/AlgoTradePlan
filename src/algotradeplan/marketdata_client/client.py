from __future__ import annotations

import json
import os
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
        bridge_args: list[str] | None = None,
        json_flag: bool | None = None,
        runner: Runner | None = None,
    ) -> None:
        self._bridge_bin = bridge_bin or os.getenv("MARKET_DATA_BIN") or "market_data_bridge"
        args_env = os.getenv("MARKET_DATA_BIN_ARGS", "").strip()
        parsed_args: list[str] = []
        if bridge_args is not None:
            parsed_args = list(bridge_args)
        elif args_env:
            try:
                loaded = json.loads(args_env)
                if isinstance(loaded, list):
                    parsed_args = [str(item) for item in loaded]
            except json.JSONDecodeError:
                parsed_args = [args_env]
        self._bridge_args = parsed_args
        if json_flag is None:
            env_flag = os.getenv("MARKET_DATA_JSON_FLAG", "1").strip().lower()
            self._json_flag = env_flag not in {"0", "false", "no"}
        else:
            self._json_flag = json_flag
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
        command = [self._bridge_bin, *self._bridge_args, operation]
        if self._json_flag:
            command.append("--json")
        try:
            result = self._runner(
                command,
                input=json.dumps(request_payload),
                capture_output=True,
                text=True,
                check=False,
            )
        except (FileNotFoundError, PermissionError) as exc:
            if allow_missing:
                return default
            raise MarketDataBridgeError(
                "MarketData bridge binary not found or not executable. Set MARKET_DATA_BIN to a valid bridge executable."
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

        # Some bridge implementations wrap payloads as {"result": ...}.
        if isinstance(parsed, dict) and "result" in parsed and len(parsed) == 1:
            parsed = parsed["result"]
        return parsed

    def query(self, operation: str, payload: dict[str, Any] | None = None, *, default: Any) -> Any:
        return self.invoke(operation, payload, default=default, allow_missing=True)


__all__ = ["MarketDataBridgeClient", "MarketDataBridgeError"]
