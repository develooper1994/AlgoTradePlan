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
WALKTHROUGH_DOC_PATH = ARTIFACT_ROOT / "tutorial_walkthrough.md"
PRINTABLE_DATASETS = ["tick", "kline", "trade", "orderbook", "funding", "macro", "fundamentals", "news"]
FALLBACK_CANDLE = {"high": 101.0, "low": 99.0, "close": 100.0}
FALLBACK_CANDLE_COUNT = 25


def _redact_sensitive_fields(value: object) -> object:
    if isinstance(value, dict):
        sanitized: dict[object, object] = {}
        for key, item in value.items():
            lowered = str(key).lower()
            if any(token in lowered for token in ("api_key", "token", "password", "secret")):
                if isinstance(item, str):
                    text = item.strip()
                    if text in {"yes", "no", "", "api_key", "api_key_or_plan"} or text.endswith("_API_KEY"):
                        sanitized[key] = text
                    else:
                        sanitized[key] = "<redacted>"
                else:
                    sanitized[key] = _redact_sensitive_fields(item)
            else:
                sanitized[key] = _redact_sensitive_fields(item)
        return sanitized
    if isinstance(value, list):
        return [_redact_sensitive_fields(item) for item in value]
    return value


STEP_TITLES = {
    1: "DataHub oluştur ve kaynakları listele",
    2: "Coverage, capability ve source recommendation sorguları",
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
    preferred = [name for name in PRINTABLE_DATASETS if name in implemented]
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
        "candles": candle_rows[-60:] if candle_rows else [FALLBACK_CANDLE] * FALLBACK_CANDLE_COUNT,
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
        "recommendations": {
            "crypto_spot_kline": hub.recommend_sources("crypto_spot_kline", allow_api_key=False, limit=3),
            "crypto_perp_funding": hub.recommend_sources("crypto_perp_funding", allow_api_key=False, limit=3),
            "macro_indicators": hub.recommend_sources("macro_indicators", allow_api_key=False, limit=3),
            "public_news": hub.recommend_sources("public_news", allow_api_key=False, limit=3),
        },
        "best_equity_kline_no_api_key": hub.best_sources_for(
            dataset="kline",
            asset_class="equity",
            allow_api_key=False,
            limit=3,
        ),
        "explain_coingecko": hub.explain_source("coingecko"),
        "explain_funding": hub.explain_dataset("funding"),
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
    print(json.dumps(_redact_sensitive_fields(steps), indent=2, default=str))


def _render_pretty(steps: list[dict[str, Any]]) -> str:
    sanitized_steps = _redact_sensitive_fields(steps)
    lines: list[str] = []
    for step in sanitized_steps:
        lines.append(f"=== Step {step['step']}: {step['title']} ===")
        output = step["output"]
        if isinstance(output, dict):
            for key, value in output.items():
                lines.append(f"- {key}: {value}")
        else:
            lines.append(str(output))
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def _render_markdown(steps: list[dict[str, Any]]) -> str:
    sanitized_steps = _redact_sensitive_fields(steps)
    step_map = {step["step"]: step for step in sanitized_steps}
    selected_source = step_map[1]["output"]["source"]
    selected_symbol = step_map[3]["output"]["selected_symbol"]
    capability = step_map[2]["output"]
    coverage = step_map[4]["output"]
    quality_block = step_map[5]["output"]
    strategy = step_map[6]["output"]["signal"]
    backtest = step_map[7]["output"]
    risk_decision = step_map[8]["output"]
    execution_fill = step_map[9]["output"]
    portfolio = step_map[10]["output"]
    report_path = step_map[11]["output"]["report_path"]
    recommendation_preview = {
        name: [item["source"] for item in values]
        for name, values in capability["recommendations"].items()
    }
    best_equity_sources = [item["source"] for item in capability["best_equity_kline_no_api_key"]]
    source_summary = capability["source_summary"]
    funding_summary = capability["explain_funding"]
    return (
        "# Tutorial Walkthrough\n\n"
        f"- selected source: `{selected_source}`\n"
        f"- selected symbol: `{selected_symbol}`\n\n"
        "## Coverage / Capability Queries\n\n"
        f"- dataset_status: `{capability['dataset_status']}`\n"
        f"- sources_for_kline: `{capability['sources_for_kline']}`\n"
        f"- source_summary: `{{'source': '{source_summary['source']}', 'implementation_status': '{source_summary['implementation_status']}', 'implemented_datasets': {source_summary['implemented_datasets']}}}`\n\n"
        "## Source Recommendation Examples\n\n"
        f"- recommendations: `{recommendation_preview}`\n"
        f"- best_equity_kline_no_api_key: `{best_equity_sources}`\n"
        f"- explain_coingecko: `{{'source': '{capability['explain_coingecko']['source']}', 'notes': '{capability['explain_coingecko']['notes']}'}}`\n"
        f"- explain_funding: `{{'dataset': '{funding_summary['dataset']}', 'best_sources_no_api_key': {[item['source'] for item in funding_summary['best_sources_no_api_key']]}}}`\n\n"
        "## Ingest Dataset Coverage\n\n"
        f"- requested_datasets: `{coverage['requested_datasets']}`\n"
        f"- dataset_coverage: `{coverage['dataset_coverage']}`\n\n"
        "## Quality / Provenance Summary\n\n"
        f"- quality: `{quality_block['quality']}`\n"
        f"- provenance: `{quality_block['provenance']}`\n"
        f"- source_issues: `{quality_block['source_issues']}`\n\n"
        "## Strategy Signal\n\n"
        f"`{strategy}`\n\n"
        "## Backtest Metrics\n\n"
        f"`{backtest}`\n\n"
        "## Risk Decision\n\n"
        f"`{risk_decision}`\n\n"
        "## Execution Fill\n\n"
        f"`{execution_fill}`\n\n"
        "## Portfolio Snapshot\n\n"
        f"`{portfolio['portfolio']}`\n\n"
        "## Ledger Preview\n\n"
        f"`{portfolio['ledger'][:5]}`\n\n"
        "## Report Path\n\n"
        f"- `{report_path}`\n"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--step", type=int)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--pretty", action="store_true")
    parser.add_argument("--markdown", action="store_true")
    parser.add_argument("--write-doc", action="store_true")
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
        if args.pretty:
            print(_render_pretty(matched), end="")
            return
        if args.markdown:
            print(_render_markdown(matched), end="")
            return
        _print_steps(matched)
        return
    markdown_output = _render_markdown(steps)
    if args.write_doc:
        WALKTHROUGH_DOC_PATH.parent.mkdir(parents=True, exist_ok=True)
        WALKTHROUGH_DOC_PATH.write_text(markdown_output, encoding="utf-8")
    if args.pretty:
        print(_render_pretty(steps), end="")
        return
    if args.markdown:
        print(markdown_output, end="")
        return
    _print_steps(steps)


if __name__ == "__main__":
    main()
