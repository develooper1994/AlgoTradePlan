from __future__ import annotations

import argparse
import json
import pathlib
import sys
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.algotradeplan.backtest import RealisticBacktester
from src.algotradeplan.core.intent import OrderIntent, signal_to_intent
from src.algotradeplan.data import DataHub
from src.algotradeplan.plugins.risk.engine import RiskEngine
from src.algotradeplan.plugins.strategies.ema_cross_atr_stop import EmaCrossAtrStopStrategyPlugin
from src.algotradeplan.portfolio.manager import PortfolioManager
from src.algotradeplan.research import ExperimentRegistry, PreflightChecker
from src.algotradeplan.strategies.catalog import strategy_summary


def _run_strategy_flow(
    *,
    hub: DataHub,
    source: str,
    symbol: str,
    strategy_id: str,
    datasets: list[str],
    allow_partial: bool,
) -> dict[str, Any]:
    ingest = hub.ingest(source=source, symbol=symbol, datasets=datasets, allow_partial=allow_partial, store=False)
    candles = ingest.to_feature_frame(dataset="kline")
    rows = candles.to_dict(orient="records") if hasattr(candles, "to_dict") else list(candles)
    closes = [float(row.get("close", 0.0)) for row in rows if row.get("close") is not None]

    strategy_plugin = EmaCrossAtrStopStrategyPlugin()
    signal = strategy_plugin.generate_signal(
        {
            "symbol": symbol,
            "price": closes[-1] if closes else 100.0,
            "quantity": 0.25,
            "candles": rows[-120:] if rows else [{"high": 101.0, "low": 99.0, "close": 100.0}] * 60,
        }
    )

    backtest = dict(signal.get("backtest", {}))
    if not backtest and closes:
        positions = [1 if close >= closes[0] else 0 for close in closes]
        backtest = RealisticBacktester().run(closes, positions).to_dict()

    trade_intent = signal_to_intent(
        signal,
        symbol=symbol,
        quantity=0.25,
        strategy_id=strategy_id,
        price=closes[-1] if closes else 100.0,
    )
    risk_engine = RiskEngine(max_notional=10_000.0)
    risk = {"approved": False, "reason": "hold_signal"}
    portfolio = PortfolioManager(starting_cash=10_000.0)

    if trade_intent is not None:
        order_intent = OrderIntent.from_trade_intent(trade_intent)
        risk = risk_engine.evaluate(order_intent.to_dict())
        if risk.get("approved"):
            execution = {
                "status": "filled",
                "symbol": symbol,
                "action": str(order_intent.action),
                "quantity": float(order_intent.quantity),
                "filled_quantity": float(order_intent.quantity),
                "price": float(order_intent.price),
                "fill_price": float(order_intent.price),
                "fee": float(order_intent.price) * float(order_intent.quantity) * 0.001,
            }
            portfolio.apply_execution(execution)

    return {
        "config": {
            "source": source,
            "symbol": symbol,
            "strategy": strategy_id,
            "datasets": datasets,
            "allow_partial": allow_partial,
        },
        "data_manifest": {
            "dataset_coverage": ingest.dataset_coverage,
            "record_count": len(ingest.records),
            "source_issues": ingest.source_issues,
            "quality": ingest.quality_report.__dict__,
        },
        "backtest": backtest,
        "risk": risk,
        "portfolio": portfolio.snapshot(),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source")
    parser.add_argument("--symbol")
    parser.add_argument("--strategy", default="ema_cross_atr_stop")
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--allow-partial", action="store_true")
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    registry = ExperimentRegistry(root=REPO_ROOT / "artifacts" / "experiments")
    if args.list:
        print(json.dumps(registry.list_experiments(), indent=2))
        return

    if not args.source and not args.offline:
        raise SystemExit("--source is required unless --offline is used")
    if not args.symbol:
        raise SystemExit("--symbol is required")

    strategy = strategy_summary(args.strategy)
    hub = DataHub()
    source = "offline_fallback" if args.offline else str(args.source)
    datasets = list(strategy["required_datasets"])

    preflight = PreflightChecker(hub).check(
        source=source,
        symbol=args.symbol,
        datasets=datasets,
        strategy=args.strategy,
        allow_api_key=not args.offline,
    )
    if not preflight.can_run:
        raise SystemExit(f"preflight_failed: {preflight.blocking_issues}")

    run = _run_strategy_flow(
        hub=hub,
        source=source,
        symbol=args.symbol,
        strategy_id=str(args.strategy),
        datasets=datasets,
        allow_partial=args.allow_partial or args.offline,
    )
    record = registry.record(
        name=f"{source}_{args.symbol}_{args.strategy}",
        config=run["config"],
        data_manifest=run["data_manifest"],
        backtest=run["backtest"],
        risk=run["risk"],
        portfolio=run["portfolio"],
    )
    payload = {"experiment": record.to_dict(), "preflight": preflight.to_dict(), **run}
    if args.json:
        print(json.dumps(payload, indent=2, default=str))
        return
    print(json.dumps(payload, indent=2, default=str))


if __name__ == "__main__":
    main()
