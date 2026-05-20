from __future__ import annotations

import argparse
import json
import pathlib
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.algotradeplan.backtest import RealisticBacktester
from src.algotradeplan.core.intent import OrderIntent, signal_to_intent
from src.algotradeplan.data import DataHub, ETL
from src.algotradeplan.orchestration.trade_flow import TradeFlow
from src.algotradeplan.plugins.connectors.simulated_fill_connector import SimulatedFillExecutionConnectorPlugin
from src.algotradeplan.plugins.risk.engine import RiskEngine
from src.algotradeplan.plugins.strategies.ema_cross_atr_stop import EmaCrossAtrStopStrategyPlugin
from src.algotradeplan.portfolio.manager import PortfolioManager

ARTIFACT_ROOT = REPO_ROOT / "artifacts" / "tutorial"
def _sanitize_output(value: object) -> object:
    if isinstance(value, dict):
        sanitized: dict[object, object] = {}
        for key, item in value.items():
            lowered = str(key).lower()
            if any(token in lowered for token in ("api_key", "token", "password", "secret")):
                sanitized[key] = "<redacted>"
            else:
                sanitized[key] = _sanitize_output(item)
        return sanitized
    if isinstance(value, list):
        return [_sanitize_output(item) for item in value]
    return value


STEP_TITLES = {
    1: "DataHub oluştur ve kaynakları listele",
    2: "Coverage ve capability sorguları",
    3: "Asset discovery",
    4: "Veri ingest",
    5: "Normalize / quality / provenance",
    6: "Feature ve strategy",
    7: "Backtest metrikleri",
    8: "Risk decision",
    9: "Simulated execution fill",
    10: "Portfolio snapshot ve ledger",
    11: "E2E report dosyası",
}


def build_tutorial_results(
    *,
    source: str | None = None,
    symbol: str | None = None,
    allow_partial: bool = False,
    offline: bool = False,
) -> list[dict[str, Any]]:
    selected_source = "offline_fallback" if offline else (source or "offline_fallback")
    artifact_root = ARTIFACT_ROOT / selected_source
    hub = DataHub(artifact_root=artifact_root)
    etl = ETL(hub)

    discovered_assets = hub.discover_assets(selected_source, limit=5)
    selected_symbol = symbol or (discovered_assets[0] if discovered_assets else "BTCUSDT")
    implemented = hub.available_datasets(selected_source, implemented_only=True)
    preferred = [name for name in ["tick", "kline", "trade", "orderbook", "funding", "macro", "fundamentals", "news"] if name in implemented]
    if not preferred:
        raise SystemExit(f"Tutorial source {selected_source} does not have implemented datasets.")

    ingest = hub.ingest(
        source=selected_source,
        symbol=selected_symbol,
        datasets=preferred,
        allow_partial=allow_partial or offline,
        store=True,
    )
    candles = ingest.to_feature_frame(dataset="kline")
    candle_rows = candles.to_dict(orient="records") if hasattr(candles, "to_dict") else list(candles)
    strategy = EmaCrossAtrStopStrategyPlugin()
    context = {
        "symbol": selected_symbol,
        "price": float(candle_rows[-1]["close"] if candle_rows else 100.0),
        "quantity": 0.25,
        "candles": candle_rows[-60:] if candle_rows else [{"high": 101.0, "low": 99.0, "close": 100.0}] * 25,
    }
    signal = strategy.generate_signal(context)
    trade_intent = signal_to_intent(
        signal,
        symbol=selected_symbol,
        quantity=float(context["quantity"]),
        strategy_id=strategy.plugin_id,
        price=float(context["price"]),
    )
    order_intent = OrderIntent.from_trade_intent(trade_intent, metadata={"tutorial": True}) if trade_intent else None
    risk_engine = RiskEngine(max_notional=10_000.0)
    risk_decision = risk_engine.evaluate(order_intent.to_dict()) if order_intent else {"approved": False, "reason": "hold_signal"}
    execution_plugin = SimulatedFillExecutionConnectorPlugin()
    execution_fill = execution_plugin.send_order(order_intent.to_dict()) if order_intent and risk_decision.get("approved") else None
    flow = TradeFlow(strategy=strategy, risk=risk_engine, execution=execution_plugin)
    flow_result = flow.run(context)
    portfolio = PortfolioManager(starting_cash=10_000.0)
    portfolio_snapshot = portfolio.apply_execution(execution_fill or flow_result.execution)
    backtest = RealisticBacktester().run(
        [float(row["close"]) for row in context["candles"]],
        [1 if float(row["close"]) >= float(context["candles"][0]["close"]) else 0 for row in context["candles"]],
    )
    report_path = artifact_root / "tutorial_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_payload = {
        "source": selected_source,
        "symbol": selected_symbol,
        "signal": signal,
        "risk_decision": risk_decision,
        "execution_fill": execution_fill or flow_result.execution,
        "portfolio": portfolio_snapshot,
        "ledger": portfolio.ledger(),
        "source_issues": ingest.source_issues,
    }
    report_path.write_text(json.dumps(report_payload, indent=2), encoding="utf-8")

    capability_example = {
        "dataset_status": hub.dataset_status(selected_source, preferred[0]),
        "sources_for_kline": hub.sources_for(dataset="kline")[:5],
        "source_summary": hub.source_summary(selected_source),
    }
    steps = [
        {"step": 1, "title": STEP_TITLES[1], "output": {"source": selected_source, "sources": hub.sources()[:10]}},
        {"step": 2, "title": STEP_TITLES[2], "output": capability_example},
        {"step": 3, "title": STEP_TITLES[3], "output": {"assets": discovered_assets, "selected_symbol": selected_symbol}},
        {"step": 4, "title": STEP_TITLES[4], "output": {"requested_datasets": preferred, "dataset_coverage": ingest.dataset_coverage}},
        {
            "step": 5,
            "title": STEP_TITLES[5],
            "output": {
                "quality": ingest.quality_report.__dict__,
                "provenance": ingest.provenance.__dict__ if ingest.provenance else None,
                "source_issues": ingest.source_issues,
            },
        },
        {"step": 6, "title": STEP_TITLES[6], "output": {"signal": signal, "feature_rows": len(candle_rows)}},
        {"step": 7, "title": STEP_TITLES[7], "output": {"signal_backtest": signal.get("backtest", {}), "tutorial_backtest": backtest.to_dict()}},
        {"step": 8, "title": STEP_TITLES[8], "output": risk_decision},
        {"step": 9, "title": STEP_TITLES[9], "output": execution_fill or flow_result.execution},
        {"step": 10, "title": STEP_TITLES[10], "output": {"portfolio": portfolio_snapshot, "ledger": portfolio.ledger()}},
        {"step": 11, "title": STEP_TITLES[11], "output": {"report_path": str(report_path), "report_preview": report_payload}},
    ]
    return steps


def _print_steps(steps: list[dict[str, Any]]) -> None:
    print(json.dumps(_sanitize_output(steps), indent=2, default=str))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--step", type=int)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--source")
    parser.add_argument("--symbol")
    parser.add_argument("--allow-partial", action="store_true")
    args = parser.parse_args()

    if args.list or (not args.all and args.step is None):
        for number, title in STEP_TITLES.items():
            print(f"{number}. {title}")
        return

    steps = build_tutorial_results(
        source=args.source,
        symbol=args.symbol,
        allow_partial=args.allow_partial,
        offline=args.offline,
    )
    if args.step is not None:
        matched = [step for step in steps if step["step"] == args.step]
        if not matched:
            raise SystemExit(f"Unknown tutorial step: {args.step}")
        _print_steps(matched)
        return
    _print_steps(steps)


if __name__ == "__main__":
    main()
