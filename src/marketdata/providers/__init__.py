"""MarketData provider adapter compatibility exports."""

from src.algotradeplan.data.adapters import (
    DataAdapterRegistry,
    DataSourceAdapter,
    build_default_adapter_registry,
)
from src.algotradeplan.plugins.data.market import (
    MarketSourceAdapter,
    MarketSourceIssue,
    MarketSourceResult,
    build_market_source_registry,
    collect_market_source_data,
)

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
