from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ExperimentRecord:
    experiment_id: str
    name: str
    created_at: str
    root: str
    paths: dict[str, str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ExperimentRegistry:
    def __init__(self, root: str | Path = "artifacts/experiments") -> None:
        self.root = Path(root)

    def record(
        self,
        *,
        name: str,
        config: dict[str, Any],
        data_manifest: dict[str, Any],
        backtest: dict[str, Any],
        risk: dict[str, Any],
        portfolio: dict[str, Any],
    ) -> ExperimentRecord:
        now = datetime.now(UTC)
        created_at = now.isoformat()
        experiment_id = f"{now.strftime('%Y%m%dT%H%M%SZ')}_{_slug(name)}"
        experiment_root = self.root / experiment_id
        experiment_root.mkdir(parents=True, exist_ok=True)

        files = {
            "config": config,
            "data_manifest": data_manifest,
            "backtest": backtest,
            "risk": risk,
            "portfolio": portfolio,
        }
        paths: dict[str, str] = {}
        for key, payload in files.items():
            path = experiment_root / f"{key}.json"
            path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
            paths[key] = str(path)

        summary_path = experiment_root / "summary.md"
        summary_path.write_text(
            _render_summary(
                name=name,
                created_at=created_at,
                config=config,
                data_manifest=data_manifest,
                backtest=backtest,
                risk=risk,
                portfolio=portfolio,
            ),
            encoding="utf-8",
        )
        paths["summary"] = str(summary_path)

        return ExperimentRecord(
            experiment_id=experiment_id,
            name=name,
            created_at=created_at,
            root=str(experiment_root),
            paths=paths,
        )

    def list_experiments(self) -> list[dict[str, str]]:
        if not self.root.exists():
            return []
        rows: list[dict[str, str]] = []
        for path in sorted(self.root.iterdir(), reverse=True):
            if not path.is_dir():
                continue
            summary = path / "summary.md"
            rows.append(
                {
                    "experiment_id": path.name,
                    "path": str(path),
                    "has_summary": "yes" if summary.exists() else "no",
                }
            )
        return rows


def _slug(value: str) -> str:
    return "".join(char.lower() if char.isalnum() else "_" for char in value).strip("_") or "experiment"


def _render_summary(
    *,
    name: str,
    created_at: str,
    config: dict[str, Any],
    data_manifest: dict[str, Any],
    backtest: dict[str, Any],
    risk: dict[str, Any],
    portfolio: dict[str, Any],
) -> str:
    return (
        "# Experiment Summary\n\n"
        f"- name: `{name}`\n"
        f"- created_at: `{created_at}`\n"
        f"- source: `{config.get('source')}`\n"
        f"- symbol: `{config.get('symbol')}`\n"
        f"- strategy: `{config.get('strategy')}`\n"
        f"- datasets: `{config.get('datasets')}`\n\n"
        "## Data manifest\n\n"
        f"`{data_manifest}`\n\n"
        "## Backtest\n\n"
        f"`{backtest}`\n\n"
        "## Risk\n\n"
        f"`{risk}`\n\n"
        "## Portfolio\n\n"
        f"`{portfolio}`\n"
    )
