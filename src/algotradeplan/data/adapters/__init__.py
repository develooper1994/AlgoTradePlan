"""DataHub adapter package."""

from __future__ import annotations

from typing import Any

from src.algotradeplan.data.adapters.base import DataSourceAdapter
from src.algotradeplan.data.adapters.coingecko import CoinGeckoAdapter
from src.algotradeplan.data.adapters.defillama import DefiLlamaAdapter
from src.algotradeplan.data.adapters.ecb import EcbAdapter
from src.algotradeplan.data.adapters.fmp import FinancialModelingPrepAdapter
from src.algotradeplan.data.adapters.frankfurter import FrankfurterAdapter
from src.algotradeplan.data.adapters.fred import FredAdapter
from src.algotradeplan.data.adapters.gdelt import GdeltAdapter
from src.algotradeplan.data.adapters.hacker_news import HackerNewsAdapter
from src.algotradeplan.data.adapters.market_registry_adapter import build_market_registry_adapters
from src.algotradeplan.data.adapters.offline_fallback import OfflineFallbackAdapter
from src.algotradeplan.data.adapters.sec_edgar import SecEdgarAdapter
from src.algotradeplan.data.adapters.stooq import StooqAdapter
from src.algotradeplan.data.adapters.tefas_cli import TefasCliAdapter
from src.algotradeplan.data.adapters.world_bank import WorldBankAdapter
from src.algotradeplan.data.adapters.registry import DataAdapterRegistry


def build_default_adapter_registry(json_getter: Any) -> DataAdapterRegistry:
    adapters: list[DataSourceAdapter] = [
        *build_market_registry_adapters(json_getter),
        FrankfurterAdapter(json_getter),
        HackerNewsAdapter(json_getter),
        OfflineFallbackAdapter(),
        CoinGeckoAdapter(json_getter),
        StooqAdapter(json_getter),
        GdeltAdapter(json_getter),
        WorldBankAdapter(json_getter),
        EcbAdapter(json_getter),
        DefiLlamaAdapter(json_getter),
        FredAdapter(json_getter),
        SecEdgarAdapter(json_getter),
        FinancialModelingPrepAdapter(json_getter),
        TefasCliAdapter(),
    ]
    return DataAdapterRegistry(adapters)


__all__ = ["DataAdapterRegistry", "DataSourceAdapter", "build_default_adapter_registry"]
