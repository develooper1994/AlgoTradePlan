from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class StrategyCapability:
    strategy_id: str
    display_name: str
    required_datasets: list[str]
    optional_datasets: list[str]
    supported_asset_classes: list[str]
    min_records: int
    supports_short: bool
    default_timeframe: str
    notes: str


_CATALOG: tuple[StrategyCapability, ...] = (
    StrategyCapability(
        strategy_id="ema_cross_atr_stop",
        display_name="EMA Cross + ATR Stop",
        required_datasets=["kline"],
        optional_datasets=["funding"],
        supported_asset_classes=["crypto_spot", "crypto_perpetual", "equity", "etf", "forex", "index"],
        min_records=60,
        supports_short=False,
        default_timeframe="1m",
        notes="Built-in executable strategy plugin available in plugins/strategies.",
    ),
    StrategyCapability(
        strategy_id="funding_carry",
        display_name="Funding Carry (metadata)",
        required_datasets=["funding"],
        optional_datasets=["kline"],
        supported_asset_classes=["crypto_perpetual"],
        min_records=30,
        supports_short=True,
        default_timeframe="8h",
        notes="Research skeleton metadata; use preflight + experiment flows before implementation.",
    ),
    StrategyCapability(
        strategy_id="news_momentum",
        display_name="News Momentum (metadata)",
        required_datasets=["news"],
        optional_datasets=["kline"],
        supported_asset_classes=["crypto_spot", "equity", "etf"],
        min_records=30,
        supports_short=False,
        default_timeframe="1d",
        notes="Research skeleton metadata for headline/event momentum ideas.",
    ),
    StrategyCapability(
        strategy_id="macro_regime",
        display_name="Macro Regime (metadata)",
        required_datasets=["macro"],
        optional_datasets=["kline"],
        supported_asset_classes=["macro", "forex", "equity", "etf"],
        min_records=24,
        supports_short=False,
        default_timeframe="1d",
        notes="Research skeleton metadata for regime overlays and filters.",
    ),
)

_CATALOG_MAP: dict[str, StrategyCapability] = {item.strategy_id: item for item in _CATALOG}


def _catalog_map() -> dict[str, StrategyCapability]:
    return _CATALOG_MAP


def list_strategies() -> list[str]:
    return sorted(item.strategy_id for item in _CATALOG)


def strategy_summary(strategy_id: str) -> dict[str, object]:
    catalog = _catalog_map()
    key = strategy_id.lower().strip()
    if key not in catalog:
        raise KeyError(f"Unknown strategy: {strategy_id}")
    return asdict(catalog[key])


def recommend_strategies(*, asset_class: str | None = None, datasets: list[str] | None = None) -> list[dict[str, object]]:
    asset = asset_class.lower().strip() if asset_class else None
    requested = {item.lower().strip() for item in (datasets or []) if item}
    rows: list[dict[str, object]] = []
    for capability in _CATALOG:
        required = set(capability.required_datasets)
        if asset and asset not in capability.supported_asset_classes:
            continue
        if requested and not required.issubset(requested):
            continue
        rows.append(asdict(capability))
    return rows


def strategy_compatibility_matrix() -> list[dict[str, object]]:
    matrix: list[dict[str, object]] = []
    for capability in _CATALOG:
        matrix.append(
            {
                "strategy_id": capability.strategy_id,
                "display_name": capability.display_name,
                "required_datasets": list(capability.required_datasets),
                "optional_datasets": list(capability.optional_datasets),
                "asset_classes": list(capability.supported_asset_classes),
                "min_records": capability.min_records,
                "supports_short": capability.supports_short,
                "default_timeframe": capability.default_timeframe,
                "notes": capability.notes,
            }
        )
    return matrix
