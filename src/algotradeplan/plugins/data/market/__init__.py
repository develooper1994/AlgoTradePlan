"""Market data plugin examples."""

from src.algotradeplan.plugins.data.market.ccxt_market_source import (
    CcxtDependencyError,
    CcxtMarketDataAgent,
)
from src.algotradeplan.plugins.data.market.static_market_batch_source import (
    StaticMarketBatchSourcePlugin,
)

__all__ = ["StaticMarketBatchSourcePlugin", "CcxtMarketDataAgent", "CcxtDependencyError"]
