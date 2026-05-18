"""Optional pydantic schema examples for runtime configuration."""

from __future__ import annotations

try:
    from pydantic import BaseModel, Field
except ImportError:  # pragma: no cover - optional dependency
    BaseModel = object  # type: ignore[assignment]
    Field = None  # type: ignore[assignment]


class RuntimeConfig(BaseModel):
    environment: str
    strategy_id: str
    risk_limit_daily_loss: float = 0.0
