# Strategy Catalog

Bu doküman `src/algotradeplan/strategies/catalog.py` metadata'sını özetler.

| Strategy | Required datasets | Optional datasets | Asset classes | Min records | Supports short | Notes |
|---|---|---|---|---:|---|---|
| ema_cross_atr_stop | kline | funding | crypto_spot, crypto_perpetual, equity, etf, forex, index | 60 | no | Built-in executable strategy plugin available in plugins/strategies. |
| funding_carry | funding | kline | crypto_perpetual | 30 | yes | Research skeleton metadata; use preflight + experiment flows before implementation. |
| news_momentum | news | kline | crypto_spot, equity, etf | 30 | no | Research skeleton metadata for headline/event momentum ideas. |
| macro_regime | macro | kline | macro, forex, equity, etf | 24 | no | Research skeleton metadata for regime overlays and filters. |

## API

```python
from src.algotradeplan.strategies.catalog import (
    list_strategies,
    strategy_summary,
    recommend_strategies,
    strategy_compatibility_matrix,
)
```
