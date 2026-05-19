"""Machine-readable source capability metadata for the public data API."""

from __future__ import annotations

from dataclasses import dataclass

_DATASET_ALIASES = {
    "ohlcv": "kline",
    "ticker": "tick",
    "trades": "trade",
    "book": "orderbook",
    "macro_snapshot": "macro",
    "macro_series": "macro",
}


@dataclass(frozen=True)
class SourceCapability:
    source: str
    asset_classes: list[str]
    datasets: list[str]
    supports_discovery: bool
    supports_history: bool
    supports_realtime: bool
    requires_api_key: bool = False
    api_key_env: str | None = None
    rate_limit_notes: str = ""
    quality_level: str = "community"


CAPABILITIES: tuple[SourceCapability, ...] = (
    SourceCapability(
        source="binance_futures",
        asset_classes=["crypto_perpetual"],
        datasets=["tick", "kline", "trade", "orderbook", "funding"],
        supports_discovery=True,
        supports_history=True,
        supports_realtime=True,
        rate_limit_notes="Public futures REST endpoints; respect exchange burst limits.",
        quality_level="production",
    ),
    SourceCapability(
        source="bybit_linear",
        asset_classes=["crypto_perpetual"],
        datasets=["tick", "kline", "trade", "orderbook", "funding"],
        supports_discovery=True,
        supports_history=True,
        supports_realtime=True,
        rate_limit_notes="Public linear market endpoints; funding available.",
        quality_level="production",
    ),
    SourceCapability(
        source="kraken_spot",
        asset_classes=["crypto_spot", "forex"],
        datasets=["tick", "kline", "trade", "orderbook"],
        supports_discovery=True,
        supports_history=True,
        supports_realtime=False,
        rate_limit_notes="Public spot endpoints; funding derived as unsupported.",
        quality_level="production",
    ),
    SourceCapability(
        source="coinbase_spot",
        asset_classes=["crypto_spot"],
        datasets=["tick", "kline", "trade", "orderbook"],
        supports_discovery=True,
        supports_history=True,
        supports_realtime=False,
        rate_limit_notes="Public exchange endpoints; no funding feed.",
        quality_level="production",
    ),
    SourceCapability(
        source="yahoo_unofficial",
        asset_classes=["crypto_spot", "equity", "etf", "forex", "index"],
        datasets=["tick", "kline"],
        supports_discovery=True,
        supports_history=True,
        supports_realtime=False,
        rate_limit_notes="Unofficial Yahoo chart/search endpoints.",
        quality_level="best_effort",
    ),
    SourceCapability(
        source="alpha_vantage",
        asset_classes=["equity", "etf", "forex"],
        datasets=["tick", "kline", "fundamentals"],
        supports_discovery=True,
        supports_history=True,
        supports_realtime=False,
        requires_api_key=True,
        api_key_env="ALPHAVANTAGE_API_KEY",
        rate_limit_notes="Free tier is heavily rate limited.",
        quality_level="production",
    ),
    SourceCapability(
        source="twelve_data",
        asset_classes=["equity", "etf", "forex", "index", "crypto_spot"],
        datasets=["tick", "kline"],
        supports_discovery=True,
        supports_history=True,
        supports_realtime=False,
        requires_api_key=True,
        api_key_env="TWELVEDATA_API_KEY",
        rate_limit_notes="API-keyed intraday time series provider.",
        quality_level="production",
    ),
    SourceCapability(
        source="polygon_io",
        asset_classes=["equity", "etf", "options", "forex", "crypto_spot"],
        datasets=["tick", "kline", "trade", "news", "corporate_actions"],
        supports_discovery=True,
        supports_history=True,
        supports_realtime=True,
        requires_api_key=True,
        api_key_env="POLYGON_API_KEY",
        rate_limit_notes="Plan-dependent market coverage.",
        quality_level="production",
    ),
    SourceCapability(
        source="finnhub",
        asset_classes=["equity", "etf", "forex", "crypto_spot"],
        datasets=["tick", "kline", "news", "fundamentals"],
        supports_discovery=True,
        supports_history=True,
        supports_realtime=True,
        requires_api_key=True,
        api_key_env="FINNHUB_API_KEY",
        rate_limit_notes="Token-based provider with broad fundamentals/news coverage.",
        quality_level="production",
    ),
    SourceCapability(
        source="quandl",
        asset_classes=["futures", "macro", "equity"],
        datasets=["kline", "macro", "fundamentals"],
        supports_discovery=True,
        supports_history=True,
        supports_realtime=False,
        requires_api_key=True,
        api_key_env="QUANDL_API_KEY",
        rate_limit_notes="Historical and economic data only.",
        quality_level="production",
    ),
    SourceCapability(
        source="iex_cloud",
        asset_classes=["equity", "etf"],
        datasets=["tick", "kline", "trade", "news", "corporate_actions"],
        supports_discovery=True,
        supports_history=True,
        supports_realtime=True,
        requires_api_key=True,
        api_key_env="IEX_CLOUD_API_KEY",
        rate_limit_notes="Token required; plan-specific endpoints.",
        quality_level="production",
    ),
    SourceCapability(
        source="frankfurter_fx",
        asset_classes=["forex", "macro"],
        datasets=["macro", "tick"],
        supports_discovery=True,
        supports_history=True,
        supports_realtime=False,
        rate_limit_notes="Public FX reference rates.",
        quality_level="production",
    ),
    SourceCapability(
        source="coingecko",
        asset_classes=["crypto_spot"],
        datasets=["tick", "kline", "news"],
        supports_discovery=True,
        supports_history=True,
        supports_realtime=False,
        rate_limit_notes="Public crypto market metadata and pricing.",
        quality_level="best_effort",
    ),
    SourceCapability(
        source="stooq",
        asset_classes=["equity", "etf", "index", "forex"],
        datasets=["kline"],
        supports_discovery=False,
        supports_history=True,
        supports_realtime=False,
        rate_limit_notes="End-of-day style market coverage.",
        quality_level="best_effort",
    ),
    SourceCapability(
        source="fred",
        asset_classes=["macro"],
        datasets=["macro"],
        supports_discovery=True,
        supports_history=True,
        supports_realtime=False,
        rate_limit_notes="Macro time series provider.",
        quality_level="production",
    ),
    SourceCapability(
        source="gdelt",
        asset_classes=["news"],
        datasets=["news"],
        supports_discovery=True,
        supports_history=True,
        supports_realtime=False,
        rate_limit_notes="News/event metadata feed.",
        quality_level="best_effort",
    ),
    SourceCapability(
        source="financial_modeling_prep",
        asset_classes=["equity", "etf", "options"],
        datasets=["tick", "kline", "fundamentals", "corporate_actions", "news"],
        supports_discovery=True,
        supports_history=True,
        supports_realtime=False,
        rate_limit_notes="Optional provider for fundamentals and corporate actions.",
        quality_level="best_effort",
    ),
    SourceCapability(
        source="sec_edgar",
        asset_classes=["equity"],
        datasets=["fundamentals", "news", "corporate_actions"],
        supports_discovery=True,
        supports_history=True,
        supports_realtime=False,
        rate_limit_notes="Filing metadata and disclosures.",
        quality_level="production",
    ),
    SourceCapability(
        source="world_bank",
        asset_classes=["macro"],
        datasets=["macro"],
        supports_discovery=True,
        supports_history=True,
        supports_realtime=False,
        rate_limit_notes="Global macro indicators and development statistics.",
        quality_level="production",
    ),
    SourceCapability(
        source="ecb",
        asset_classes=["macro", "forex"],
        datasets=["macro", "tick"],
        supports_discovery=True,
        supports_history=True,
        supports_realtime=False,
        rate_limit_notes="ECB market and macro reference series.",
        quality_level="production",
    ),
    SourceCapability(
        source="defillama",
        asset_classes=["crypto_spot", "macro"],
        datasets=["fundamentals", "macro", "news"],
        supports_discovery=True,
        supports_history=True,
        supports_realtime=False,
        rate_limit_notes="DeFi TVL and protocol metadata.",
        quality_level="best_effort",
    ),
    SourceCapability(
        source="hacker_news",
        asset_classes=["news"],
        datasets=["news"],
        supports_discovery=True,
        supports_history=True,
        supports_realtime=False,
        rate_limit_notes="Public story search used as a smoke-news source.",
        quality_level="best_effort",
    ),
    SourceCapability(
        source="offline_fallback",
        asset_classes=["crypto_perpetual"],
        datasets=["tick", "kline", "trade", "orderbook", "funding"],
        supports_discovery=True,
        supports_history=True,
        supports_realtime=False,
        rate_limit_notes="Deterministic fallback used only when live public sources are unreachable.",
        quality_level="fallback",
    ),
)


def canonical_dataset_name(dataset: str) -> str:
    return _DATASET_ALIASES.get(dataset.lower(), dataset.lower())


def capability_map() -> dict[str, SourceCapability]:
    return {item.source: item for item in CAPABILITIES}
