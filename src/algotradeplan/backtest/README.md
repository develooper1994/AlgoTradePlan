# Backtest Module

- Replay parity harness: `/src/algotradeplan/backtest/replay.py`
- Realistic fee/slippage/latency backtester: `/src/algotradeplan/backtest/realistic.py`
- Runtime demo: `python scripts/e2e_real_data_smoke.py --interactive`
- Extension note: implement new execution cost models by extending `RealisticBacktester`.
