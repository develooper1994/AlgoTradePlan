"""Autonomous real-data smoke pipeline covering discovery->intent->risk->portfolio."""

from __future__ import annotations

import json
import ssl
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from src.algotradeplan.observability import InMemoryMetricsSink, StructuredLogger
from src.algotradeplan.orchestration.trade_flow import TradeFlow
from src.algotradeplan.plugins.connectors.simulated_fill_connector import (
    SimulatedFillExecutionConnectorPlugin,
)
from src.algotradeplan.plugins.data.contracts import DataRecord, DataRequest
from src.algotradeplan.plugins.data.curated.feature_view import ExampleFeatureViewPlugin
from src.algotradeplan.plugins.data.example_data_storage import InMemoryDataStoragePlugin
from src.algotradeplan.plugins.data.example_provenance import ExampleProvenancePlugin
from src.algotradeplan.plugins.data.example_quality_check import RequiredFieldsQualityPlugin
from src.algotradeplan.plugins.data.market import (
    CcxtDependencyError,
    CcxtMarketDataAgent,
    build_market_source_registry,
    collect_market_source_data,
)
from src.algotradeplan.plugins.data.market.static_market_batch_source import (
    StaticMarketBatchSourcePlugin,
)
from src.algotradeplan.plugins.data.pipeline import DataIngestionPipeline
from src.algotradeplan.plugins.risk.notional_guard import NotionalGuardRiskPlugin
from src.algotradeplan.plugins.strategies.ema_cross_atr_stop import (
    EmaCrossAtrStopStrategyPlugin,
)

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
MIN_KLINE_FIELD_COUNT = 5


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
    source_issues: list[dict[str, str]]
    source_inventory: list[str]
    news_story_count: int
    macro_series_count: int
    feature_count: int
    intent: dict[str, Any]
    risk_decision: dict[str, Any]
    portfolio: dict[str, Any]
    metrics: dict[str, float]


class _PortfolioManager:
    def __init__(self, starting_cash: float) -> None:
        self.cash = starting_cash
        self.positions: dict[str, float] = {}

    def apply_execution(self, execution: dict[str, Any] | None) -> dict[str, Any]:
        if not execution:
            return self.snapshot()

        symbol = str(execution.get("symbol"))
        quantity = float(execution.get("quantity", 0.0))
        price = float(execution.get("price", 0.0))
        notional = quantity * price
        action = str(execution.get("action", "")).lower()

        if action == "buy":
            self.cash -= notional
            self.positions[symbol] = self.positions.get(symbol, 0.0) + quantity
        elif action == "sell":
            self.cash += notional
            self.positions[symbol] = self.positions.get(symbol, 0.0) - quantity

        return self.snapshot()

    def snapshot(self) -> dict[str, Any]:
        return {"cash": round(self.cash, 6), "positions": dict(self.positions)}


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


def _records_from_klines(symbol: str, source: str, klines: list[list[Any]]) -> list[DataRecord]:
    records: list[DataRecord] = []
    for row in klines:
        if len(row) < MIN_KLINE_FIELD_COUNT:
            continue
        open_time_ms = int(row[0])
        records.append(
            DataRecord(
                key=f"{symbol}-kline-{open_time_ms}",
                observed_at=datetime.fromtimestamp(open_time_ms / 1000, tz=UTC).isoformat(),
                domain="market",
                source=source,
                asset_type="perpetual",
                payload={
                    "symbol": symbol,
                    "open": float(row[1]),
                    "high": float(row[2]),
                    "low": float(row[3]),
                    "close": float(row[4]),
                },
                metadata={"join_key": symbol, "dataset": "kline", "lake_zone": "raw"},
            )
        )
    return records


def _collect_market_sources(
    *,
    max_symbols_per_source: int,
    allow_partial: bool,
    json_getter: JsonGetter | None,
    market_agent: CcxtMarketDataAgent | None,
) -> tuple[list[SourceCoverage], dict[str, dict[str, Any]], list[dict[str, str]]]:
    source_coverages: list[SourceCoverage] = []
    datasets_by_source: dict[str, dict[str, Any]] = {}
    source_issues: list[dict[str, str]] = []

    if json_getter:
        try:
            results, issues = collect_market_source_data(
                get_json=json_getter,
                max_symbols=max_symbols_per_source,
                allow_partial=allow_partial,
            )
        except Exception as exc:
            raise RealDataSmokeError(str(exc)) from exc

        for issue in issues:
            source_issues.append({"source": issue.source, "reason": issue.reason})

        for item in results:
            sizes = _require_dataset_coverage(item.source, item.datasets, allow_partial)
            source_coverages.append(
                SourceCoverage(
                    source=item.source,
                    asset_count=item.asset_count,
                    selected_asset=item.selected_asset,
                    datasets=sizes,
                )
            )
            datasets_by_source[item.source] = item.datasets

        if not source_coverages:
            raise RealDataSmokeError("no market source coverage available")
        return source_coverages, datasets_by_source, source_issues

    agent = market_agent or CcxtMarketDataAgent()
    ccxt_sources = (
        ("binanceusdm", "binance_futures"),
        ("bybit", "bybit_linear"),
        ("kraken", "kraken_spot"),
        ("coinbase", "coinbase_spot"),
    )
    for exchange_id, source_name in ccxt_sources:
        try:
            symbols = agent.discover_assets(exchange_id, max_symbols_per_source)
            if not symbols:
                raise RealDataSmokeError(f"{exchange_id} discovery returned no symbols")
            selected_asset = _select_preferred_asset(symbols)
            datasets = agent.fetch_exchange_datasets(exchange_id, selected_asset)
            if source_name in {"kraken_spot", "coinbase_spot"} and not datasets.get("funding"):
                datasets = dict(datasets)
                datasets["funding"] = [{"symbol": selected_asset, "rate": 0.0, "derived": True}]
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
        except CcxtDependencyError as exc:
            raise RealDataSmokeError(str(exc)) from exc
        except Exception as exc:
            source_issues.append({"source": source_name, "reason": str(exc)})
            if allow_partial:
                continue
            raise RealDataSmokeError(str(exc)) from exc
    if not source_coverages:
        raise RealDataSmokeError("no market source coverage available")
    return source_coverages, datasets_by_source, source_issues


def run_real_data_autopilot(
    *,
    report_path: Path,
    max_symbols_per_source: int = 5,
    allow_partial: bool = False,
    json_getter: JsonGetter | None = None,
    market_agent: CcxtMarketDataAgent | None = None,
) -> PipelineReport:
    get_json = json_getter or _default_json_getter
    logger = StructuredLogger(correlation_id=f"real-smoke-{datetime.now(UTC).timestamp()}")
    metrics = InMemoryMetricsSink()

    source_coverages, datasets_by_source, source_issues = _collect_market_sources(
        max_symbols_per_source=max_symbols_per_source,
        allow_partial=allow_partial,
        json_getter=json_getter,
        market_agent=market_agent,
    )

    news_assets = _discover_news_assets(get_json, max_symbols_per_source)
    news_rows = _fetch_news(get_json, news_assets[0])
    if not news_rows and not allow_partial:
        raise RealDataSmokeError("news source returned no stories")

    macro_series = _discover_macro_series(get_json, max_symbols_per_source)
    if not macro_series:
        raise RealDataSmokeError("macro source returned no series")
    macro_snapshot = _fetch_macro_snapshot(get_json, macro_series[0])
    if not macro_snapshot.get("rates") and not allow_partial:
        raise RealDataSmokeError("macro source returned no rates")

    market_records: list[DataRecord] = []
    for coverage in source_coverages:
        source_datasets = datasets_by_source[coverage.source]
        market_records.extend(
            _records_from_klines(
                symbol=coverage.selected_asset,
                source=f"{coverage.source}_public",
                klines=source_datasets["kline"],
            )
        )

    if not market_records:
        raise RealDataSmokeError("no normalized market records produced from kline datasets")

    selected_coverage = source_coverages[0]
    pipeline = DataIngestionPipeline(
        source=StaticMarketBatchSourcePlugin(market_records),
        storage=InMemoryDataStoragePlugin(),
        quality=RequiredFieldsQualityPlugin(),
        provenance=ExampleProvenancePlugin(),
    )
    ingestion_result = pipeline.ingest(
        DataRequest(dataset="kline", symbol=selected_coverage.selected_asset)
    )
    feature_result = ExampleFeatureViewPlugin().build(ingestion_result.records, ingestion_result.provenance)

    selected_candles = [
        record.payload
        for record in ingestion_result.records
        if record.payload.get("symbol") == selected_coverage.selected_asset
    ]
    strategy = EmaCrossAtrStopStrategyPlugin()
    signal = strategy.generate_signal({"candles": selected_candles})
    action = str(signal.get("action", "hold")).lower()
    latest_price = (
        float(selected_candles[-1].get("close", 0.0)) if selected_candles else 0.0
    )
    intent = {
        "symbol": selected_coverage.selected_asset,
        "action": action,
        "quantity": DEFAULT_ORDER_QUANTITY,
        "price": latest_price,
        "strategy": signal.get("strategy", {}),
        "features": signal.get("features", {}),
        "backtest": signal.get("backtest", {}),
    }

    flow = TradeFlow(
        strategy=strategy,
        risk=NotionalGuardRiskPlugin(max_notional=DEFAULT_MAX_NOTIONAL),
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
    portfolio = _PortfolioManager(starting_cash=DEFAULT_STARTING_CASH)
    portfolio_snapshot = portfolio.apply_execution(flow_result.execution)

    for coverage in source_coverages:
        metrics.record("market_symbols_discovered", coverage.asset_count, source=coverage.source)
    metrics.record("source_issues", len(source_issues), source="market_registry")
    metrics.record("news_stories", len(news_rows), source="hn")
    metrics.record("macro_rates", len(macro_snapshot.get("rates", {})), source="frankfurter")
    metrics.record("feature_rows", len(feature_result.feature_records), source="feature")
    metrics.record("backtest_net_pnl", float(intent["backtest"].get("net_pnl", 0.0)), source="ema_atr")

    logger.info(
        "real_data_autopilot_completed",
        market_sources=[coverage.source for coverage in source_coverages],
        source_issues=source_issues,
        selected_symbol=selected_coverage.selected_asset,
        signal=action,
        approved=flow_result.risk_decision.get("approved"),
    )

    source_inventory = [adapter.source for adapter in build_market_source_registry()]
    report = PipelineReport(
        generated_at=datetime.now(UTC).isoformat(),
        market_sources=source_coverages,
        source_issues=source_issues,
        source_inventory=source_inventory,
        news_story_count=len(news_rows),
        macro_series_count=len(macro_snapshot.get("rates", {})),
        feature_count=len(feature_result.feature_records),
        intent=intent,
        risk_decision=flow_result.risk_decision,
        portfolio=portfolio_snapshot,
        metrics={
                "market_symbols_total": metrics.total("market_symbols_discovered"),
                "source_issue_count": metrics.total("source_issues"),
                "news_stories": metrics.total("news_stories"),
                "macro_rates": metrics.total("macro_rates"),
                "feature_rows": metrics.total("feature_rows"),
                "backtest_net_pnl": metrics.total("backtest_net_pnl"),
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
                "source_issues": report.source_issues,
                "source_inventory": report.source_inventory,
                "news_story_count": report.news_story_count,
                "macro_series_count": report.macro_series_count,
                "feature_count": report.feature_count,
                "intent": report.intent,
                "risk_decision": report.risk_decision,
                "portfolio": report.portfolio,
                "metrics": report.metrics,
                "logs": [entry.to_json() for entry in logger.entries],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    return report
