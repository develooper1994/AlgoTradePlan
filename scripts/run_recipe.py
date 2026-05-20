from __future__ import annotations

import argparse
import ast
import json
import os
import pathlib
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.algotradeplan.data import DataHub
from src.algotradeplan.research import (
    ExperimentRegistry,
    PreflightChecker,
    generate_data_health_report,
    write_data_health_markdown,
)

from scripts.run_experiment import _run_strategy_flow


def _parse_value(value: str) -> Any:
    text = value.strip()
    if not text:
        return ""
    if text.lower() in {"true", "false"}:
        return text.lower() == "true"
    if text.lower() == "null":
        return None
    if text.startswith("[") and text.endswith("]"):
        try:
            return ast.literal_eval(text)
        except (ValueError, SyntaxError):
            inner = text[1:-1].strip()
            if not inner:
                return []
            return [_parse_value(item) for item in inner.split(",")]
    if text.startswith("{") and text.endswith("}"):
        return ast.literal_eval(text)
    numeric_candidate = text.replace(".", "", 1).replace("-", "", 1)
    try:
        if numeric_candidate.isdigit() and "." in text:
            return float(text)
        if numeric_candidate.isdigit():
            return int(text)
    except ValueError:
        pass
    return text.strip('"').strip("'")


def _load_recipe(path: Path) -> dict[str, Any]:
    suffix = path.suffix.lower()
    raw = path.read_text(encoding="utf-8")
    if suffix == ".json":
        return json.loads(raw)
    yaml_disabled = os.getenv("ALGOTRADEPLAN_DISABLE_YAML", "").lower() in {"1", "true", "yes"}
    try:
        if yaml_disabled:
            raise ImportError("YAML parser disabled by ALGOTRADEPLAN_DISABLE_YAML")
        import yaml  # type: ignore

        loaded = yaml.safe_load(raw)
        if isinstance(loaded, dict):
            return loaded
    except Exception:
        pass

    recipe: dict[str, Any] = {}
    current_map: dict[str, Any] | None = None
    current_key: str | None = None
    for line in raw.splitlines():
        if not line.strip() or line.strip().startswith("#"):
            continue
        if line.startswith("  ") and (current_map is None or not current_key):
            raise ValueError(
                f"Unexpected nested recipe line: {line}. Nested keys must follow a parent key like 'risk:'"
            )
        if line.startswith("  ") and current_map is not None and current_key:
            if ":" not in line:
                raise ValueError(
                    f"Invalid nested recipe line: {line}. Expected format: '  key: value'"
                )
            child_key, child_value = line.strip().split(":", 1)
            current_map[child_key.strip()] = _parse_value(child_value)
            continue
        if ":" not in line:
            raise ValueError(
                f"Invalid recipe line: {line}. Expected format: 'key: value'"
            )
        key, value = line.split(":", 1)
        key = key.strip()
        parsed = _parse_value(value)
        if parsed == "":
            current_map = {}
            recipe[key] = current_map
            current_key = key
            continue
        recipe[key] = parsed
        current_map = None
        current_key = None
    return recipe


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("recipe")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    recipe_path = Path(args.recipe)
    if not recipe_path.is_absolute():
        recipe_path = REPO_ROOT / recipe_path
    recipe = _load_recipe(recipe_path)

    source = "offline_fallback" if recipe.get("offline") else recipe.get("source")
    symbol = str(recipe.get("symbol", "BTCUSDT"))
    datasets = [str(item) for item in recipe.get("datasets", ["kline"])]
    strategy = str(recipe.get("strategy", "ema_cross_atr_stop"))
    allow_partial = bool(recipe.get("allow_partial", False) or recipe.get("offline", False))
    hub = DataHub()

    preflight = PreflightChecker(hub).check(
        source=str(source),
        symbol=symbol,
        datasets=datasets,
        strategy=strategy,
        allow_api_key=not bool(recipe.get("offline", False)),
    )

    health = generate_data_health_report(
        hub=hub,
        source=str(source),
        symbol=symbol,
        datasets=datasets,
        allow_partial=allow_partial,
    )
    health_path = write_data_health_markdown(health)

    payload: dict[str, Any] = {
        "recipe": recipe,
        "preflight": preflight.to_dict(),
        "data_health": {**health.to_dict(), "artifact_path": str(health_path)},
    }

    if args.dry_run:
        print(json.dumps(payload, indent=2, default=str))
        return

    if not preflight.can_run:
        raise SystemExit(f"preflight_failed: {preflight.blocking_issues}")

    flow = _run_strategy_flow(
        hub=hub,
        source=str(source),
        symbol=symbol,
        strategy_id=strategy,
        datasets=datasets,
        allow_partial=allow_partial,
    )
    registry = ExperimentRegistry(root=REPO_ROOT / "artifacts" / "experiments")
    record = registry.record(
        name=str(recipe.get("name") or f"recipe_{strategy}_{symbol}"),
        config={**flow["config"], "recipe": str(recipe_path)},
        data_manifest={**flow["data_manifest"], "health_score": health.health_score, "health_artifact": str(health_path)},
        backtest=flow["backtest"],
        risk={**flow["risk"], "recipe_risk": recipe.get("risk", {})},
        portfolio={**flow["portfolio"], "recipe_portfolio": recipe.get("portfolio", {})},
    )
    payload.update({"experiment": record.to_dict(), **flow})

    print(json.dumps(payload, indent=2, default=str))


if __name__ == "__main__":
    main()
