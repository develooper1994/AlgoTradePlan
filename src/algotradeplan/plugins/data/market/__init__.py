"""Market data plugin examples."""

from src.algotradeplan.plugins.data.market.ccxt_market_source import (
    CcxtDependencyError,
    CcxtMarketDataAgent,
)
from src.algotradeplan.plugins.data.market.public_source_registry import (
    MarketSourceAdapter,
    MarketSourceIssue,
    MarketSourceResult,
    build_market_source_registry,
    collect_market_source_data,
)
from src.algotradeplan.plugins.data.market.static_market_batch_source import (
    StaticMarketBatchSourcePlugin,
)

__all__ = [
    "StaticMarketBatchSourcePlugin",
    "CcxtMarketDataAgent",
    "CcxtDependencyError",
    "MarketSourceAdapter",
    "MarketSourceResult",
    "MarketSourceIssue",
    "build_market_source_registry",
    "collect_market_source_data",
]
