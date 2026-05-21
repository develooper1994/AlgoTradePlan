"""Autonomous real-data smoke pipeline covering discovery->intent->risk->portfolio."""

from __future__ import annotations

import json
import ssl
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from src.algotradeplan.data import DataHub
from src.algotradeplan.data.provenance import provenance_to_dict
from src.algotradeplan.observability import InMemoryMetricsSink, StructuredLogger
from src.algotradeplan.orchestration.trade_flow import TradeFlow
from src.algotradeplan.plugins.connectors.simulated_fill_connector import (
    SimulatedFillExecutionConnectorPlugin,
)
from src.algotradeplan.plugins.risk.engine import RiskEngine
from src.algotradeplan.plugins.strategies.ema_cross_atr_stop import (
    EmaCrossAtrStopStrategyPlugin,
)
from src.algotradeplan.portfolio.manager import PortfolioManager

JsonGetter = Callable[[str, dict[str, Any]], Any]
_ALLOWED_API_PREFIXES = (
    "https://fapi.binance.com/",
    "https://api.bybit.com/",
    "https://api.kraken.com/",
    "https://api.exchange.coinbase.com/",
    "https://query1.finance.yahoo.com/",
    "https://www.alphavantage.co/",
    "https://api.twelvedata.com/",
    "https://api.polygon.io/",
    "https://finnhub.io/",
    "https://data.nasdaq.com/",
    "https://cloud.iexapis.com/",
    "https://hn.algolia.com/",
    "https://api.frankfurter.dev/",
)
DEFAULT_ORDER_QUANTITY = 0.01
DEFAULT_MAX_NOTIONAL = 1_000.0
DEFAULT_STARTING_CASH = 10_000.0


class RealDataSmokeError(RuntimeError):
    """Raised when real-data smoke validation fails."""


@dataclass(frozen=True)
class SourceCoverage:
    source: str
    asset_count: int
    selected_asset: str
    datasets: dict[str, int]


@dataclass(frozen=True)
class PipelineReport:
    generated_at: str
    market_sources: list[SourceCoverage]
    coverage_table: list[dict[str, str]]
    source_issues: list[dict[str, str]]
    source_inventory: list[str]
    news_story_count: int
    macro_series_count: int
    feature_count: int
    dataset_coverage: dict[str, int]
    data_quality: dict[str, Any]
    provenance_manifest: dict[str, Any]
    normalized_record_count: int
    signal: dict[str, Any]
    intent: dict[str, Any]
    risk_decision: dict[str, Any]
    execution_fill: dict[str, Any]
    portfolio: dict[str, Any]
    ledger: list[dict[str, Any]]
    metrics: dict[str, float]
    backtest: dict[str, Any] = field(default_factory=dict)


def _default_json_getter(url: str, params: dict[str, Any]) -> Any:
    if not url.startswith(_ALLOWED_API_PREFIXES):
        raise RealDataSmokeError(f"URL not in allowlist: {url}")
    query = urlencode({k: v for k, v in params.items() if v is not None})
    request_url = f"{url}?{query}" if query else url
    request = Request(
        request_url,
        headers={
            "Accept": "application/json",
            "User-Agent": "AlgoTradePlanRealSmoke/1.0",
        },
    )
    ssl_context = ssl.create_default_context()
    try:
        with urlopen(request, timeout=20, context=ssl_context) as response:  # nosec B310
            return json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError) as exc:
        raise RealDataSmokeError(f"HTTP failure for {request_url}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise RealDataSmokeError(f"Invalid JSON from {request_url}: {exc}") from exc


def _discover_news_assets(get_json: JsonGetter, max_assets: int) -> list[str]:
    payload = get_json("https://hn.algolia.com/api/v1/search", {"query": "bitcoin", "tags": "story"})
    assets: list[str] = []
    for hit in payload.get("hits", []):
        title = str(hit.get("title") or "")
        if "bitcoin" in title.lower():
            assets.append("BITCOIN")
        if "ethereum" in title.lower():
            assets.append("ETHEREUM")
    if not assets:
        assets.append("BITCOIN")
    return sorted(set(assets))[:max_assets]


def _fetch_news(get_json: JsonGetter, asset: str) -> list[dict[str, Any]]:
    payload = get_json(
        "https://hn.algolia.com/api/v1/search",
        {"query": asset.lower(), "tags": "story", "hitsPerPage": 20},
    )
    return payload.get("hits", [])


def _discover_macro_series(get_json: JsonGetter, max_series: int) -> list[str]:
    payload = get_json("https://api.frankfurter.dev/v1/currencies", {})
    symbols = sorted(payload.keys())
    return symbols[:max_series]


def _fetch_macro_snapshot(get_json: JsonGetter, base_currency: str) -> dict[str, Any]:
    return get_json("https://api.frankfurter.dev/v1/latest", {"base": base_currency})


def _select_preferred_asset(symbols: list[str]) -> str:
    for symbol in symbols:
        if "BTC" in symbol.upper() or "XBT" in symbol.upper():
            return symbol
    return symbols[0]


def _require_dataset_coverage(source: str, datasets: dict[str, Any], allow_partial: bool) -> dict[str, int]:
    sizes = {name: len(value) if isinstance(value, list) else int(bool(value)) for name, value in datasets.items()}
    missing = [name for name, size in sizes.items() if size == 0]
    if missing and not allow_partial:
        raise RealDataSmokeError(f"{source} missing dataset coverage: {', '.join(sorted(missing))}")
    return sizes


def _collect_market_sources(
    *,
    hub: DataHub,
    max_symbols_per_source: int,
    allow_partial: bool,
    json_getter: JsonGetter | None,  # noqa: ARG002
) -> tuple[list[SourceCoverage], dict[str, dict[str, Any]], list[dict[str, str]]]:
    source_coverages: list[SourceCoverage] = []
    datasets_by_source: dict[str, dict[str, Any]] = {}
    source_issues: list[dict[str, str]] = []
    for source_name in ("binance_futures", "bybit_linear", "kraken_spot", "coinbase_spot", "yahoo_unofficial"):
        capability = hub.capability(source_name)
        requested_datasets = [item for item in ("tick", "kline", "trade", "orderbook", "funding") if item in capability.datasets]
        try:
            symbols = hub.discover_assets(source_name, limit=max_symbols_per_source)
            if not symbols:
                raise RealDataSmokeError(f"{source_name} discovery returned no symbols")
            selected_asset = _select_preferred_asset(symbols)
            ingest_result = hub.ingest(
                source=source_name,
                symbol=selected_asset,
                datasets=requested_datasets,
                allow_partial=True,
                store=False,
            )
            source_issues.extend(ingest_result.source_issues)
            datasets = {item: ingest_result.normalized.get(item, []) for item in requested_datasets}
            sizes = _require_dataset_coverage(source_name, datasets, allow_partial)
            source_coverages.append(
                SourceCoverage(
                    source=source_name,
                    asset_count=len(symbols),
                    selected_asset=selected_asset,
                    datasets=sizes,
                )
            )
            datasets_by_source[source_name] = datasets
        except Exception as exc:
            source_issues.append({"source": source_name, "reason": str(exc)})
            if allow_partial:
                continue
            raise RealDataSmokeError(str(exc)) from exc

    if not source_coverages and allow_partial:
        offline_symbol = "BTCUSDT"
        offline_klines = [
            [1_700_000_000_000 + (index * 60_000), "100", "101", "99", str(100 + index * 0.2), "10"]
            for index in range(120)
        ]
        offline_datasets = {
            "tick": [{"symbol": offline_symbol, "price": "123.45"}],
            "kline": offline_klines,
            "trade": [{"id": 1, "price": "123.45", "qty": "0.25", "time": 1_700_000_000_001}],
            "orderbook": [{"bids": [["123.40", "1"]], "asks": [["123.50", "1"]]}],
            "funding": [{"fundingRate": "0.0001", "fundingTime": 1_700_000_000_002, "derived": True}],
        }
        source_issues.append(
            {
                "source": "market_registry",
                "reason": "offline_fallback:no_public_market_sources",
            }
        )
        source_coverages.append(
            SourceCoverage(
                source="offline_fallback",
                asset_count=1,
                selected_asset=offline_symbol,
                datasets=_require_dataset_coverage("offline_fallback", offline_datasets, True),
            )
        )
        datasets_by_source["offline_fallback"] = offline_datasets
    if not source_coverages:
        raise RealDataSmokeError("no market source coverage available")
    return source_coverages, datasets_by_source, source_issues


def run_real_data_autopilot(
    *,
    report_path: Path,
    max_symbols_per_source: int = 5,
    allow_partial: bool = False,
    json_getter: JsonGetter | None = None,
) -> PipelineReport:
    get_json = json_getter or _default_json_getter
    logger = StructuredLogger(correlation_id=f"real-smoke-{datetime.now(UTC).timestamp()}")
    metrics = InMemoryMetricsSink()
    hub = DataHub(json_getter=get_json, artifact_root=report_path.parent / "datahub")

    source_coverages, datasets_by_source, source_issues = _collect_market_sources(
        hub=hub,
        max_symbols_per_source=max_symbols_per_source,
        allow_partial=allow_partial,
        json_getter=json_getter,
    )

    news_result = None
    try:
        news_assets = hub.discover_assets("hacker_news", limit=max_symbols_per_source)
        news_symbol = news_assets[0] if news_assets else "BITCOIN"
        news_result = hub.ingest(
            source="hacker_news",
            symbol=news_symbol,
            datasets=["news"],
            limit=max_symbols_per_source,
            allow_partial=allow_partial,
        )
        source_issues.extend(news_result.source_issues)
        if not news_result.records and not allow_partial:
            raise RealDataSmokeError("news source returned no stories")
    except Exception as exc:
        source_issues.append({"source": "hacker_news", "reason": str(exc)})
        if not allow_partial:
            raise RealDataSmokeError(f"news source failure: {exc}") from exc

    macro_result = None
    macro_snapshot: dict[str, Any] = {"rates": {}}
    try:
        macro_series = hub.discover_assets("frankfurter_fx", limit=max_symbols_per_source)
        if not macro_series:
            raise RealDataSmokeError("macro source returned no series")
        macro_result = hub.ingest(
            source="frankfurter_fx",
            symbol=macro_series[0],
            datasets=["macro"],
            allow_partial=allow_partial,
        )
        source_issues.extend(macro_result.source_issues)
        macro_snapshot = macro_result.records[0].payload if macro_result.records else {"rates": {}}
        if not macro_snapshot.get("rates") and not allow_partial:
            raise RealDataSmokeError("macro source returned no rates")
    except Exception as exc:
        source_issues.append({"source": "frankfurter", "reason": str(exc)})
        if not allow_partial:
            raise RealDataSmokeError(f"macro source failure: {exc}") from exc

    selected_coverage = source_coverages[0]
    market_result = hub.ingest(
        source=selected_coverage.source,
        symbol=selected_coverage.selected_asset,
        datasets=["kline", "trade", "orderbook", "funding"],
        limit=500,
        allow_partial=allow_partial,
    )
    source_issues.extend(market_result.source_issues)
    if not market_result.records:
        raise RealDataSmokeError("no normalized market records produced from selected datasets")

    selected_candles = [
        record.payload
        for record in market_result.records
        if record.metadata.get("dataset") == "kline"
    ]
    if not selected_candles:
        raise RealDataSmokeError("no normalized kline records available for strategy evaluation")

    strategy = EmaCrossAtrStopStrategyPlugin()
    signal = strategy.generate_signal({"candles": selected_candles})
    action = str(signal.get("action", "hold")).lower()
    latest_price = (
        float(selected_candles[-1].get("close", 0.0)) if selected_candles else 0.0
    )
    highs = [float(candle.get("high", candle.get("close", 0.0))) for candle in selected_candles]
    lows = [float(candle.get("low", candle.get("close", 0.0))) for candle in selected_candles]
    closes = [float(candle.get("close", 0.0)) for candle in selected_candles]
    _, backtest_summary_obj = strategy.optimize(closes, highs, lows)
    backtest_summary = backtest_summary_obj.to_dict()
    intent = {
        "symbol": selected_coverage.selected_asset,
        "action": action,
        "quantity": DEFAULT_ORDER_QUANTITY,
        "price": latest_price,
        "strategy": signal.get("strategy", {}),
        "features": signal.get("features", {}),
        "backtest": backtest_summary,
    }

    risk_engine = RiskEngine(max_notional=DEFAULT_MAX_NOTIONAL, max_position_size=1.0)
    risk_engine.update_drawdown(float(backtest_summary.get("max_drawdown", 0.0)))
    flow = TradeFlow(
        strategy=strategy,
        risk=risk_engine,
        execution=SimulatedFillExecutionConnectorPlugin(),
    )
    flow_result = flow.run(
        {
            "symbol": intent["symbol"],
            "price": intent["price"],
            "quantity": intent["quantity"],
            "candles": selected_candles,
        }
    )
    portfolio = PortfolioManager(starting_cash=DEFAULT_STARTING_CASH)
    portfolio_snapshot = portfolio.apply_execution(
        flow_result.execution,
    )
    portfolio_snapshot = portfolio.snapshot({selected_coverage.selected_asset: latest_price})
    quality_report = asdict(market_result.quality_report)
    news_story_count = len(news_result.records) if news_result is not None else 0
    macro_series_count = len(macro_snapshot.get("rates", {}))
    feature_count = len(signal.get("features", {}))

    for coverage in source_coverages:
        metrics.record("market_symbols_discovered", coverage.asset_count, source=coverage.source)
    metrics.record("source_issues", len(source_issues), source="market_registry")
    metrics.record("news_stories", news_story_count, source="hn")
    metrics.record("macro_rates", macro_series_count, source="frankfurter")
    metrics.record("feature_rows", feature_count, source="feature")
    metrics.record("backtest_net_pnl", float(backtest_summary.get("net_pnl", 0.0)), source="ema_atr")
    metrics.record("normalized_records", len(market_result.records), source=selected_coverage.source)

    logger.info(
        "real_data_autopilot_completed",
        market_sources=[coverage.source for coverage in source_coverages],
        source_issues=source_issues,
        selected_symbol=selected_coverage.selected_asset,
        signal=action,
        approved=flow_result.risk_decision.get("approved"),
    )

    source_inventory = hub.sources()
    report = PipelineReport(
        generated_at=datetime.now(UTC).isoformat(),
        market_sources=source_coverages,
        coverage_table=hub.coverage_table(),
        source_issues=source_issues,
        source_inventory=source_inventory,
        news_story_count=news_story_count,
        macro_series_count=macro_series_count,
        feature_count=feature_count,
        dataset_coverage=dict(market_result.dataset_coverage),
        data_quality=quality_report,
        provenance_manifest=provenance_to_dict(market_result.provenance),
        normalized_record_count=len(market_result.records),
        signal=signal,
        intent=flow_result.order_intent or intent,
        risk_decision=flow_result.risk_decision,
        execution_fill=flow_result.execution or {},
        portfolio=portfolio_snapshot,
        ledger=portfolio.ledger(),
        backtest=backtest_summary,
        metrics={
                "market_symbols_total": metrics.total("market_symbols_discovered"),
                "source_issue_count": metrics.total("source_issues"),
                "news_stories": metrics.total("news_stories"),
                "macro_rates": metrics.total("macro_rates"),
                "feature_rows": metrics.total("feature_rows"),
                "backtest_net_pnl": metrics.total("backtest_net_pnl"),
                "normalized_record_count": metrics.total("normalized_records"),
            },
        )

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(
            {
                "generated_at": report.generated_at,
                "market_sources": [
                    {
                        "source": item.source,
                        "asset_count": item.asset_count,
                        "selected_asset": item.selected_asset,
                        "datasets": item.datasets,
                    }
                    for item in report.market_sources
                ],
                "coverage_table": report.coverage_table,
                "source_issues": report.source_issues,
                "source_inventory": report.source_inventory,
                "news_story_count": report.news_story_count,
                "macro_series_count": report.macro_series_count,
                "feature_count": report.feature_count,
                "dataset_coverage": report.dataset_coverage,
                "data_quality": report.data_quality,
                "provenance_manifest": report.provenance_manifest,
                "normalized_record_count": report.normalized_record_count,
                "signal": report.signal,
                "intent": report.intent,
                "risk_decision": report.risk_decision,
                "execution_fill": report.execution_fill,
                "portfolio": report.portfolio,
                "ledger": report.ledger,
                "backtest": report.backtest,
                "metrics": report.metrics,
                "logs": [entry.to_json() for entry in logger.entries],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    return report
