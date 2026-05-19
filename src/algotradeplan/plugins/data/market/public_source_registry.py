"""Public and API-keyed market source registry for live data discovery/fetch."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Callable

JsonGetter = Callable[[str, dict[str, Any]], Any]

_DEFAULT_QUOTE_ASSETS = {"USD", "USDT", "USDC"}
_FALLBACK_EPOCH_MS_BASE = 1_700_000_000_000


@dataclass(frozen=True)
class MarketSourceAdapter:
    source: str
    discover_assets: Callable[[JsonGetter, int], list[str]]
    fetch_datasets: Callable[[JsonGetter, str], dict[str, Any]]
    required_api_key_env: str | None = None


@dataclass(frozen=True)
class MarketSourceResult:
    source: str
    asset_count: int
    selected_asset: str
    datasets: dict[str, Any]


@dataclass(frozen=True)
class MarketSourceIssue:
    source: str
    reason: str


def _select_preferred_asset(symbols: list[str]) -> str:
    for symbol in symbols:
        upper = symbol.upper()
        if "BTC" in upper or "XBT" in upper:
            return symbol
    return symbols[0]


def _attach_derived_funding(symbol: str, datasets: dict[str, Any]) -> dict[str, Any]:
    if datasets.get("funding"):
        return datasets
    copied = dict(datasets)
    copied["funding"] = [{"symbol": symbol, "rate": 0.0, "derived": True}]
    return copied


def _to_epoch_ms(value: str | None, fallback_ms: int) -> int:
    if not value:
        return fallback_ms
    normalized = value.replace(" ", "T")
    try:
        return int(datetime.fromisoformat(normalized).replace(tzinfo=UTC).timestamp() * 1000)
    except ValueError:
        return fallback_ms


def _binance_discover(get_json: JsonGetter, max_symbols: int) -> list[str]:
    payload = get_json("https://fapi.binance.com/fapi/v1/exchangeInfo", {})
    symbols = [
        item["symbol"]
        for item in payload.get("symbols", [])
        if item.get("status") == "TRADING" and item.get("quoteAsset") in _DEFAULT_QUOTE_ASSETS
    ]
    return symbols[:max_symbols]


def _binance_fetch(get_json: JsonGetter, symbol: str) -> dict[str, Any]:
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


def _bybit_discover(get_json: JsonGetter, max_symbols: int) -> list[str]:
    payload = get_json("https://api.bybit.com/v5/market/instruments-info", {"category": "linear"})
    symbols = [
        item["symbol"]
        for item in payload.get("result", {}).get("list", [])
        if item.get("status") == "Trading" and item.get("quoteCoin") in _DEFAULT_QUOTE_ASSETS
    ]
    return symbols[:max_symbols]


def _bybit_fetch(get_json: JsonGetter, symbol: str) -> dict[str, Any]:
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


def _kraken_discover(get_json: JsonGetter, max_symbols: int) -> list[str]:
    payload = get_json("https://api.kraken.com/0/public/AssetPairs", {})
    result = payload.get("result", {})
    symbols = []
    for pair, details in result.items():
        ws_name = str(details.get("wsname", ""))
        quote = ws_name.split("/")[-1].upper() if "/" in ws_name else ""
        if quote in _DEFAULT_QUOTE_ASSETS:
            symbols.append(pair)
    return sorted(symbols)[:max_symbols]


def _kraken_fetch(get_json: JsonGetter, symbol: str) -> dict[str, Any]:
    ticker = get_json("https://api.kraken.com/0/public/Ticker", {"pair": symbol})
    ohlc = get_json("https://api.kraken.com/0/public/OHLC", {"pair": symbol, "interval": 1})
    trades = get_json("https://api.kraken.com/0/public/Trades", {"pair": symbol})
    depth = get_json("https://api.kraken.com/0/public/Depth", {"pair": symbol, "count": 10})
    result = {
        "tick": [ticker.get("result", {})],
        "kline": ohlc.get("result", {}).get(symbol, []),
        "trade": trades.get("result", {}).get(symbol, []),
        "orderbook": [depth.get("result", {}).get(symbol, {})],
        "funding": [],
    }
    return _attach_derived_funding(symbol, result)


def _coinbase_discover(get_json: JsonGetter, max_symbols: int) -> list[str]:
    payload = get_json("https://api.exchange.coinbase.com/products", {})
    symbols = [
        item["id"]
        for item in payload
        if item.get("quote_currency") in _DEFAULT_QUOTE_ASSETS
        and item.get("status", "").lower() == "online"
        and not item.get("trading_disabled", False)
    ]
    return symbols[:max_symbols]


def _coinbase_fetch(get_json: JsonGetter, symbol: str) -> dict[str, Any]:
    return _attach_derived_funding(
        symbol,
        {
            "tick": [get_json(f"https://api.exchange.coinbase.com/products/{symbol}/ticker", {})],
            "kline": get_json(
                f"https://api.exchange.coinbase.com/products/{symbol}/candles",
                {"granularity": 60},
            ),
            "trade": get_json(f"https://api.exchange.coinbase.com/products/{symbol}/trades", {"limit": 25}),
            "orderbook": [
                get_json(
                    f"https://api.exchange.coinbase.com/products/{symbol}/book",
                    {"level": 2},
                )
            ],
            "funding": [],
        },
    )


def _yahoo_discover(get_json: JsonGetter, max_symbols: int) -> list[str]:
    payload = get_json("https://query1.finance.yahoo.com/v1/finance/search", {"q": "crypto"})
    symbols = []
    for row in payload.get("quotes", []):
        symbol = str(row.get("symbol", ""))
        if "USD" in symbol.upper() or "=X" in symbol.upper():
            symbols.append(symbol)
    return symbols[:max_symbols]


def _yahoo_fetch(get_json: JsonGetter, symbol: str) -> dict[str, Any]:
    payload = get_json(
        f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}",
        {"interval": "1m", "range": "1d"},
    )
    result = payload.get("chart", {}).get("result", [{}])[0]
    timestamps = result.get("timestamp", [])
    quote = result.get("indicators", {}).get("quote", [{}])[0]
    opens = quote.get("open", [])
    highs = quote.get("high", [])
    lows = quote.get("low", [])
    closes = quote.get("close", [])

    klines: list[list[Any]] = []
    for index, ts in enumerate(timestamps):
        if index >= len(closes) or closes[index] is None:
            continue
        klines.append(
            [
                int(ts) * 1000,
                str(opens[index] or closes[index]),
                str(highs[index] or closes[index]),
                str(lows[index] or closes[index]),
                str(closes[index]),
            ]
        )

    meta = result.get("meta", {})
    last_close = closes[-1] if closes else 0
    return _attach_derived_funding(
        symbol,
        {
            "tick": [{"symbol": symbol, "price": meta.get("regularMarketPrice", last_close)}],
            "kline": klines,
            "trade": [{"symbol": symbol, "source": "yahoo_chart"}] if klines else [],
            "orderbook": [
                {
                    "bid": meta.get("bid", meta.get("regularMarketPrice", 0)),
                    "ask": meta.get("ask", meta.get("regularMarketPrice", 0)),
                }
            ],
            "funding": [],
        },
    )


def _alpha_vantage_discover(get_json: JsonGetter, max_symbols: int) -> list[str]:
    api_key = os.getenv("ALPHAVANTAGE_API_KEY", "")
    payload = get_json(
        "https://www.alphavantage.co/query",
        {"function": "SYMBOL_SEARCH", "keywords": "bitcoin", "apikey": api_key},
    )
    matches = payload.get("bestMatches", [])
    symbols = [str(row.get("1. symbol", "")) for row in matches if row.get("1. symbol")]
    return symbols[:max_symbols]


def _alpha_vantage_fetch(get_json: JsonGetter, symbol: str) -> dict[str, Any]:
    api_key = os.getenv("ALPHAVANTAGE_API_KEY", "")
    payload = get_json(
        "https://www.alphavantage.co/query",
        {
            "function": "TIME_SERIES_INTRADAY",
            "symbol": symbol,
            "interval": "1min",
            "outputsize": "compact",
            "apikey": api_key,
        },
    )
    points = payload.get("Time Series (1min)", {})
    klines: list[list[Any]] = []
    for index, (ts, row) in enumerate(points.items(), start=1):
        fallback = _FALLBACK_EPOCH_MS_BASE + (index * 60_000)
        klines.append(
            [
                _to_epoch_ms(str(ts), fallback),
                str(row.get("1. open", "0")),
                str(row.get("2. high", "0")),
                str(row.get("3. low", "0")),
                str(row.get("4. close", "0")),
            ]
        )
    return _attach_derived_funding(
        symbol,
        {
            "tick": [{"symbol": symbol, "price": klines[0][4] if klines else "0"}],
            "kline": klines,
            "trade": [{"symbol": symbol, "source": "alphavantage_intraday"}] if klines else [],
            "orderbook": [{"symbol": symbol, "source": "alphavantage"}] if klines else [],
            "funding": [],
        },
    )


def _twelvedata_discover(get_json: JsonGetter, max_symbols: int) -> list[str]:
    api_key = os.getenv("TWELVEDATA_API_KEY", "")
    payload = get_json(
        "https://api.twelvedata.com/symbol_search",
        {"symbol": "BTC", "apikey": api_key},
    )
    symbols = [str(item.get("symbol", "")) for item in payload.get("data", []) if item.get("symbol")]
    return symbols[:max_symbols]


def _twelvedata_fetch(get_json: JsonGetter, symbol: str) -> dict[str, Any]:
    api_key = os.getenv("TWELVEDATA_API_KEY", "")
    payload = get_json(
        "https://api.twelvedata.com/time_series",
        {
            "symbol": symbol,
            "interval": "1min",
            "outputsize": 120,
            "apikey": api_key,
        },
    )
    values = payload.get("values", [])
    klines: list[list[Any]] = []
    for index, row in enumerate(values, start=1):
        fallback = _FALLBACK_EPOCH_MS_BASE + (index * 60_000)
        klines.append(
            [
                _to_epoch_ms(str(row.get("datetime", "")), fallback),
                row.get("open", "0"),
                row.get("high", "0"),
                row.get("low", "0"),
                row.get("close", "0"),
            ]
        )
    tick_payload = (
        [{"symbol": symbol, "price": values[0].get("close", "0")}]
        if values
        else [{"symbol": symbol, "price": "0"}]
    )
    return _attach_derived_funding(
        symbol,
        {
            "tick": tick_payload,
            "kline": klines,
            "trade": [{"symbol": symbol, "source": "twelvedata_time_series"}] if values else [],
            "orderbook": [{"symbol": symbol, "source": "twelvedata"}] if values else [],
            "funding": [],
        },
    )


def _polygon_discover(get_json: JsonGetter, max_symbols: int) -> list[str]:
    api_key = os.getenv("POLYGON_API_KEY", "")
    payload = get_json(
        "https://api.polygon.io/v3/reference/tickers",
        {"market": "stocks", "active": "true", "limit": max_symbols, "apiKey": api_key},
    )
    return [str(item.get("ticker", "")) for item in payload.get("results", []) if item.get("ticker")][:max_symbols]


def _polygon_fetch(get_json: JsonGetter, symbol: str) -> dict[str, Any]:
    api_key = os.getenv("POLYGON_API_KEY", "")
    payload = get_json(
        f"https://api.polygon.io/v2/aggs/ticker/{symbol}/range/1/minute/2025-01-01/2025-01-02",
        {"adjusted": "true", "sort": "asc", "limit": 120, "apiKey": api_key},
    )
    rows = payload.get("results", [])
    klines = [[row.get("t", 0), row.get("o", 0), row.get("h", 0), row.get("l", 0), row.get("c", 0)] for row in rows]
    return _attach_derived_funding(
        symbol,
        {
            "tick": [{"symbol": symbol, "price": rows[-1].get("c", 0)}] if rows else [],
            "kline": klines,
            "trade": [{"symbol": symbol, "source": "polygon_agg"}] if rows else [],
            "orderbook": [{"symbol": symbol, "source": "polygon"}] if rows else [],
            "funding": [],
        },
    )


def _finnhub_discover(get_json: JsonGetter, max_symbols: int) -> list[str]:
    api_key = os.getenv("FINNHUB_API_KEY", "")
    payload = get_json(
        "https://finnhub.io/api/v1/stock/symbol",
        {"exchange": "US", "token": api_key},
    )
    return [str(item.get("symbol", "")) for item in payload if item.get("symbol")][:max_symbols]


def _finnhub_fetch(get_json: JsonGetter, symbol: str) -> dict[str, Any]:
    api_key = os.getenv("FINNHUB_API_KEY", "")
    quote = get_json("https://finnhub.io/api/v1/quote", {"symbol": symbol, "token": api_key})
    candles = get_json(
        "https://finnhub.io/api/v1/stock/candle",
        {"symbol": symbol, "resolution": "1", "count": 120, "token": api_key},
    )
    closes = candles.get("c", [])
    highs = candles.get("h", [])
    lows = candles.get("l", [])
    opens = candles.get("o", [])
    timestamps = candles.get("t", [])
    klines = [
        [timestamps[i] * 1000, opens[i], highs[i], lows[i], closes[i]]
        for i in range(min(len(timestamps), len(closes), len(opens), len(highs), len(lows)))
    ]
    return _attach_derived_funding(
        symbol,
        {
            "tick": [quote],
            "kline": klines,
            "trade": [{"symbol": symbol, "source": "finnhub"}] if klines else [],
            "orderbook": [{"symbol": symbol, "source": "finnhub"}] if klines else [],
            "funding": [],
        },
    )


def _quandl_discover(get_json: JsonGetter, max_symbols: int) -> list[str]:
    api_key = os.getenv("QUANDL_API_KEY", "")
    payload = get_json(
        "https://data.nasdaq.com/api/v3/datasets.json",
        {"query": "futures", "per_page": max_symbols, "api_key": api_key},
    )
    rows = payload.get("datasets", [])
    return [str(item.get("dataset_code", "")) for item in rows if item.get("dataset_code")][:max_symbols]


def _quandl_fetch(get_json: JsonGetter, symbol: str) -> dict[str, Any]:
    api_key = os.getenv("QUANDL_API_KEY", "")
    payload = get_json(
        f"https://data.nasdaq.com/api/v3/datasets/CHRIS/CME_{symbol}.json",
        {"rows": 120, "api_key": api_key},
    )
    data = payload.get("dataset", {}).get("data", [])
    klines = []
    for idx, row in enumerate(data, start=1):
        if len(row) < 5:
            continue
        fallback = _FALLBACK_EPOCH_MS_BASE + (idx * 60_000)
        klines.append([_to_epoch_ms(str(row[0]), fallback), row[1], row[2], row[3], row[4]])
    return _attach_derived_funding(
        symbol,
        {
            "tick": [{"symbol": symbol, "price": klines[0][4]}] if klines else [],
            "kline": klines,
            "trade": [{"symbol": symbol, "source": "quandl"}] if klines else [],
            "orderbook": [{"symbol": symbol, "source": "quandl"}] if klines else [],
            "funding": [],
        },
    )


def _iex_discover(get_json: JsonGetter, max_symbols: int) -> list[str]:
    api_key = os.getenv("IEX_CLOUD_API_KEY", "")
    payload = get_json(
        "https://cloud.iexapis.com/stable/ref-data/symbols",
        {"token": api_key},
    )
    symbols = [str(item.get("symbol", "")) for item in payload if item.get("symbol")]
    return symbols[:max_symbols]


def _iex_fetch(get_json: JsonGetter, symbol: str) -> dict[str, Any]:
    api_key = os.getenv("IEX_CLOUD_API_KEY", "")
    quote = get_json(
        f"https://cloud.iexapis.com/stable/stock/{symbol}/quote",
        {"token": api_key},
    )
    chart = get_json(
        f"https://cloud.iexapis.com/stable/stock/{symbol}/chart/1d",
        {"chartInterval": 1, "token": api_key},
    )
    klines = []
    for idx, row in enumerate(chart, start=1):
        fallback = _FALLBACK_EPOCH_MS_BASE + (idx * 60_000)
        date_text = str(row.get("date", "")).strip()
        minute = str(row.get("minute", "")).strip()
        timestamp = _to_epoch_ms(f"{date_text}T{minute}:00" if date_text and minute else date_text, fallback)
        klines.append([timestamp, row.get("open", 0), row.get("high", 0), row.get("low", 0), row.get("close", 0)])
    return _attach_derived_funding(
        symbol,
        {
            "tick": [quote],
            "kline": klines,
            "trade": [{"symbol": symbol, "source": "iex"}] if klines else [],
            "orderbook": [{"symbol": symbol, "source": "iex"}] if klines else [],
            "funding": [],
        },
    )


def build_market_source_registry() -> list[MarketSourceAdapter]:
    return [
        MarketSourceAdapter("binance_futures", _binance_discover, _binance_fetch),
        MarketSourceAdapter("bybit_linear", _bybit_discover, _bybit_fetch),
        MarketSourceAdapter("kraken_spot", _kraken_discover, _kraken_fetch),
        MarketSourceAdapter("coinbase_spot", _coinbase_discover, _coinbase_fetch),
        MarketSourceAdapter("yahoo_unofficial", _yahoo_discover, _yahoo_fetch),
        MarketSourceAdapter(
            "alpha_vantage",
            _alpha_vantage_discover,
            _alpha_vantage_fetch,
            required_api_key_env="ALPHAVANTAGE_API_KEY",
        ),
        MarketSourceAdapter(
            "twelve_data",
            _twelvedata_discover,
            _twelvedata_fetch,
            required_api_key_env="TWELVEDATA_API_KEY",
        ),
        MarketSourceAdapter(
            "polygon_io",
            _polygon_discover,
            _polygon_fetch,
            required_api_key_env="POLYGON_API_KEY",
        ),
        MarketSourceAdapter(
            "finnhub",
            _finnhub_discover,
            _finnhub_fetch,
            required_api_key_env="FINNHUB_API_KEY",
        ),
        MarketSourceAdapter(
            "quandl",
            _quandl_discover,
            _quandl_fetch,
            required_api_key_env="QUANDL_API_KEY",
        ),
        MarketSourceAdapter(
            "iex_cloud",
            _iex_discover,
            _iex_fetch,
            required_api_key_env="IEX_CLOUD_API_KEY",
        ),
    ]


def collect_market_source_data(
    *,
    get_json: JsonGetter,
    max_symbols: int,
    allow_partial: bool,
) -> tuple[list[MarketSourceResult], list[MarketSourceIssue]]:
    registry = build_market_source_registry()
    results: list[MarketSourceResult] = []
    issues: list[MarketSourceIssue] = []

    for adapter in registry:
        if adapter.required_api_key_env and not os.getenv(adapter.required_api_key_env):
            issues.append(
                MarketSourceIssue(
                    source=adapter.source,
                    reason=f"skipped_missing_api_key:{adapter.required_api_key_env}",
                )
            )
            continue

        try:
            symbols = adapter.discover_assets(get_json, max(1, max_symbols))
            if not symbols:
                raise RuntimeError("discovery returned no symbols")
            selected_asset = _select_preferred_asset(symbols)
            datasets = adapter.fetch_datasets(get_json, selected_asset)
            results.append(
                MarketSourceResult(
                    source=adapter.source,
                    asset_count=len(symbols),
                    selected_asset=selected_asset,
                    datasets=datasets,
                )
            )
        except Exception as exc:
            issues.append(MarketSourceIssue(source=adapter.source, reason=str(exc)))
            if not allow_partial and adapter.required_api_key_env is None:
                raise

    if not results:
        raise RuntimeError("no market source coverage available")

    return results, issues
