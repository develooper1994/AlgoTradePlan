"""Provider adapters moved to MarketData; kept for import compatibility."""


class DataSourceAdapter:  # pragma: no cover - compatibility stub
    pass


class DataAdapterRegistry:  # pragma: no cover - compatibility stub
    pass


class MarketSourceAdapter:  # pragma: no cover - compatibility stub
    pass


class MarketSourceResult:  # pragma: no cover - compatibility stub
    pass


class MarketSourceIssue:  # pragma: no cover - compatibility stub
    pass


def build_default_adapter_registry(*_args, **_kwargs):
    return DataAdapterRegistry()


def build_market_source_registry(*_args, **_kwargs):
    return []


def collect_market_source_data(*_args, **_kwargs):
    return {}


__all__ = [
    "DataSourceAdapter",
    "DataAdapterRegistry",
    "build_default_adapter_registry",
    "MarketSourceAdapter",
    "MarketSourceResult",
    "MarketSourceIssue",
    "build_market_source_registry",
    "collect_market_source_data",
]
