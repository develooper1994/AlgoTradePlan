"""Runtime config loader scaffold."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppConfig:
    environment: str
    strategy_id: str
    risk_limit_daily_loss: float = 0.0


def load_runtime_config(path: str | Path) -> AppConfig:
    content = json.loads(Path(path).read_text(encoding="utf-8"))
    return AppConfig(
        environment=str(content["environment"]),
        strategy_id=str(content["strategy_id"]),
        risk_limit_daily_loss=float(content.get("risk_limit_daily_loss", 0.0)),
    )
