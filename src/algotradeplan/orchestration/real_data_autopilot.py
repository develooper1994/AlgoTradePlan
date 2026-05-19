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
from src.algotradeplan.plugins.data.market.static_market_batch_source import (
    StaticMarketBatchSourcePlugin,
)
from src.algotradeplan.plugins.data.pipeline import DataIngestionPipeline
from src.algotradeplan.plugins.risk.notional_guard import NotionalGuardRiskPlugin
from src.algotradeplan.plugins.strategies.autopilot_signal_strategy import (
    AutopilotSignalStrategyPlugin,
)

JsonGetter = Callable[[str, dict[str, Any]], Any]
_ALLOWED_API_PREFIXES = (
    "https://fapi.binance.com/",
    "https://api.bybit.com/",
    "https://hn.algolia.com/",
    "https://api.frankfurter.dev/",
)
DEFAULT_ORDER_QUANTITY = 0.01
DEFAULT_MAX_NOTIONAL = 1_000.0
DEFAULT_STARTING_CASH = 10_000.0
MIN_KLINE_FIELD_COUNT = 5
EMA_WINDOW_CANDIDATES: tuple[tuple[int, int], ...] = ((3, 9), (5, 13), (8, 21), (13, 34))


class RealDataSmokeError(RuntimeError):
    """Raised when real-data smoke validation fails."""


@dataclass(frozen=True)
class SourceCoverage:
    source: str
    asset_count: int
    selected_asset: str
    datasets: dict[str, int]


@dataclass(frozen=True)
class BacktestResult:
    short_window: int
    long_window: int
    score: float
    signal: str


@dataclass(frozen=True)
class PipelineReport:
    generated_at: str
    market_sources: list[SourceCoverage]
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


def _discover_binance_symbols(get_json: JsonGetter, max_symbols: int) -> list[str]:
    payload = get_json("https://fapi.binance.com/fapi/v1/exchangeInfo", {})
    symbols = [
        item["symbol"]
        for item in payload.get("symbols", [])
        if item.get("status") == "TRADING" and item.get("quoteAsset") in {"USDT", "USD"}
    ]
    return symbols[:max_symbols]


def _fetch_binance_datasets(get_json: JsonGetter, symbol: str) -> dict[str, Any]:
    return {
        "tick": [get_json("https://fapi.binance.com/fapi/v1/ticker/price", {"symbol": symbol})],
        "kline": get_json(
            "https://fapi.binance.com/fapi/v1/klines",
            {"symbol": symbol, "interval": "1m", "limit": 180},
        ),
        "trade": get_json("https://fapi.binance.com/fapi/v1/trades", {"symbol": symbol, "limit": 25}),
        "orderbook": [
            get_json("https://fapi.binance.com/fapi/v1/depth", {"symbol": symbol, "limit": 10})
        ],
        "funding": get_json(
            "https://fapi.binance.com/fapi/v1/fundingRate", {"symbol": symbol, "limit": 5}
        ),
    }


def _discover_bybit_symbols(get_json: JsonGetter, max_symbols: int) -> list[str]:
    payload = get_json("https://api.bybit.com/v5/market/instruments-info", {"category": "linear"})
    items = payload.get("result", {}).get("list", [])
    symbols = [
        item["symbol"]
        for item in items
        if item.get("status") == "Trading" and item.get("quoteCoin") in {"USDT", "USDC", "USD"}
    ]
    return symbols[:max_symbols]


def _fetch_bybit_datasets(get_json: JsonGetter, symbol: str) -> dict[str, Any]:
    return {
        "tick": get_json(
            "https://api.bybit.com/v5/market/tickers",
            {"category": "linear", "symbol": symbol},
        )
        .get("result", {})
        .get("list", []),
        "kline": get_json(
            "https://api.bybit.com/v5/market/kline",
            {"category": "linear", "symbol": symbol, "interval": 1, "limit": 180},
        )
        .get("result", {})
        .get("list", []),
        "trade": get_json(
            "https://api.bybit.com/v5/market/recent-trade",
            {"category": "linear", "symbol": symbol, "limit": 25},
        )
        .get("result", {})
        .get("list", []),
        "orderbook": [
            get_json(
                "https://api.bybit.com/v5/market/orderbook",
                {"category": "linear", "symbol": symbol, "limit": 10},
            )
            .get("result", {})
        ],
        "funding": get_json(
            "https://api.bybit.com/v5/market/funding/history",
            {"category": "linear", "symbol": symbol, "limit": 5},
        )
        .get("result", {})
        .get("list", []),
    }


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
        if "BTC" in symbol.upper():
            return symbol
    return symbols[0]


def _require_dataset_coverage(source: str, datasets: dict[str, Any], allow_partial: bool) -> dict[str, int]:
    sizes = {name: len(value) if isinstance(value, list) else int(bool(value)) for name, value in datasets.items()}
    missing = [name for name, size in sizes.items() if size == 0]
    if missing and not allow_partial:
        raise RealDataSmokeError(f"{source} missing dataset coverage: {', '.join(sorted(missing))}")
    return sizes


def _records_from_binance_klines(symbol: str, klines: list[list[Any]]) -> list[DataRecord]:
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
                source="binance_futures_public",
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


def _ema(values: list[float], window: int) -> list[float]:
    if not values:
        return []
    alpha = 2 / (window + 1)
    series = [values[0]]
    for value in values[1:]:
        series.append((value * alpha) + (series[-1] * (1 - alpha)))
    return series


def _evaluate_ema_strategy(closes: list[float], short_window: int, long_window: int) -> BacktestResult:
    short_series = _ema(closes, short_window)
    long_series = _ema(closes, long_window)
    if len(closes) < 2:
        return BacktestResult(short_window=short_window, long_window=long_window, score=0.0, signal="hold")

    score = 0.0
    for index in range(1, len(closes) - 1):
        side = 1.0 if short_series[index] >= long_series[index] else -1.0
        score += (closes[index + 1] - closes[index]) * side

    latest_signal = "buy" if short_series[-1] >= long_series[-1] else "sell"
    return BacktestResult(
        short_window=short_window,
        long_window=long_window,
        score=round(score, 8),
        signal=latest_signal,
    )


def _optimize_ema(closes: list[float]) -> BacktestResult:
    valid_pairs = [(s, l) for s, l in EMA_WINDOW_CANDIDATES if l < len(closes) and s < l]
    if not valid_pairs:
        return BacktestResult(short_window=1, long_window=2, score=0.0, signal="hold")

    best = _evaluate_ema_strategy(closes, valid_pairs[0][0], valid_pairs[0][1])
    for short_window, long_window in valid_pairs[1:]:
        current = _evaluate_ema_strategy(closes, short_window, long_window)
        if current.score > best.score:
            best = current
    return best


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

    source_coverages: list[SourceCoverage] = []

    binance_symbols = _discover_binance_symbols(get_json, max_symbols_per_source)
    if not binance_symbols:
        raise RealDataSmokeError("binance discovery returned no symbols")
    binance_asset = _select_preferred_asset(binance_symbols)
    binance_data = _fetch_binance_datasets(get_json, binance_asset)
    binance_sizes = _require_dataset_coverage("binance", binance_data, allow_partial)
    source_coverages.append(
        SourceCoverage(
            source="binance_futures",
            asset_count=len(binance_symbols),
            selected_asset=binance_asset,
            datasets=binance_sizes,
        )
    )

    bybit_symbols = _discover_bybit_symbols(get_json, max_symbols_per_source)
    if not bybit_symbols:
        raise RealDataSmokeError("bybit discovery returned no symbols")
    bybit_asset = _select_preferred_asset(bybit_symbols)
    bybit_data = _fetch_bybit_datasets(get_json, bybit_asset)
    bybit_sizes = _require_dataset_coverage("bybit", bybit_data, allow_partial)
    source_coverages.append(
        SourceCoverage(
            source="bybit_linear",
            asset_count=len(bybit_symbols),
            selected_asset=bybit_asset,
            datasets=bybit_sizes,
        )
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

    market_records = _records_from_binance_klines(binance_asset, binance_data["kline"])
    pipeline = DataIngestionPipeline(
        source=StaticMarketBatchSourcePlugin(market_records),
        storage=InMemoryDataStoragePlugin(),
        quality=RequiredFieldsQualityPlugin(),
        provenance=ExampleProvenancePlugin(),
    )
    ingestion_result = pipeline.ingest(DataRequest(dataset="kline", symbol=binance_asset))
    feature_result = ExampleFeatureViewPlugin().build(ingestion_result.records, ingestion_result.provenance)

    closes = [float(record.payload["close"]) for record in ingestion_result.records]
    optimized = _optimize_ema(closes)
    intent = {
        "symbol": binance_asset,
        "action": optimized.signal,
        "quantity": DEFAULT_ORDER_QUANTITY,
        "price": closes[-1] if closes else 0.0,
        "strategy": {
            "short_window": optimized.short_window,
            "long_window": optimized.long_window,
            "score": optimized.score,
        },
    }

    flow = TradeFlow(
        strategy=AutopilotSignalStrategyPlugin(optimized.signal),
        risk=NotionalGuardRiskPlugin(max_notional=DEFAULT_MAX_NOTIONAL),
        execution=SimulatedFillExecutionConnectorPlugin(),
    )
    flow_result = flow.run(
        {
            "symbol": intent["symbol"],
            "price": intent["price"],
            "quantity": intent["quantity"],
        }
    )
    portfolio = _PortfolioManager(starting_cash=DEFAULT_STARTING_CASH)
    portfolio_snapshot = portfolio.apply_execution(flow_result.execution)

    metrics.record("market_symbols_discovered", len(binance_symbols), source="binance")
    metrics.record("market_symbols_discovered", len(bybit_symbols), source="bybit")
    metrics.record("news_stories", len(news_rows), source="hn")
    metrics.record("macro_rates", len(macro_snapshot.get("rates", {})), source="frankfurter")
    metrics.record("feature_rows", len(feature_result.feature_records), source="feature")
    metrics.record("backtest_score", optimized.score, source="ema")

    logger.info(
        "real_data_autopilot_completed",
        market_sources=[coverage.source for coverage in source_coverages],
        selected_symbol=binance_asset,
        signal=optimized.signal,
        approved=flow_result.risk_decision.get("approved"),
    )

    report = PipelineReport(
        generated_at=datetime.now(UTC).isoformat(),
        market_sources=source_coverages,
        news_story_count=len(news_rows),
        macro_series_count=len(macro_snapshot.get("rates", {})),
        feature_count=len(feature_result.feature_records),
        intent=intent,
        risk_decision=flow_result.risk_decision,
        portfolio=portfolio_snapshot,
        metrics={
            "market_symbols_total": metrics.total("market_symbols_discovered"),
            "news_stories": metrics.total("news_stories"),
            "macro_rates": metrics.total("macro_rates"),
            "feature_rows": metrics.total("feature_rows"),
            "backtest_score": metrics.total("backtest_score"),
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
