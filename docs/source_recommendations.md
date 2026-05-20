# Source Recommendations

Bu doküman DataHub `recommend_sources()` API'sinden üretilir.

## Recommended Sources by Use Case

| Use case | Best sources | Alternatives | API key needed | Notes |
|---|---|---|---|---|
| crypto_spot_kline | coinbase_spot, kraken_spot | coingecko, yahoo_unofficial | No | live kline support for crypto_spot without API key |
| crypto_perp_funding | binance_futures, bybit_linear | offline_fallback | No | live funding support for crypto_perpetual without API key |
| equity_daily_ohlcv | stooq, yahoo_unofficial | alpha_vantage, financial_modeling_prep | No | live kline support for equity without API key; EOD/public-first sources are preferred when available. |
| equity_intraday_ohlcv | stooq, yahoo_unofficial | alpha_vantage, financial_modeling_prep | No | live kline support for equity without API key |
| macro_rates | ecb, frankfurter_fx | kraken_spot, world_bank | No | live tick support for forex, macro without API key; Public FX/reference-rate feeds are preferred. |
| macro_indicators | ecb, frankfurter_fx | world_bank, defillama | No | live macro support for macro, forex without API key |
| public_news | gdelt, hacker_news | sec_edgar, financial_modeling_prep | No | live news support without API key; No-key news/event feeds are preferred for this use case. |
| fundamentals | defillama, sec_edgar | alpha_vantage, financial_modeling_prep | No | partial fundamentals support without API key |
| options | yahoo_unofficial | financial_modeling_prep, polygon_io | No | partial kline support for options without API key; Coverage is often plan-dependent for richer options endpoints. |
| offline_demo | offline_fallback, binance_futures | bybit_linear | No | fallback kline support for crypto_perpetual without API key; offline_fallback should only be used for tutorial/smoke/demo flows. |

### crypto_spot_kline

- `coinbase_spot` — dataset=live, asset=live, api_key=no, reason=live kline support for crypto_spot without API key
- `kraken_spot` — dataset=live, asset=live, api_key=no, reason=live kline support for crypto_spot without API key
- `coingecko` — dataset=partial, asset=partial, api_key=no, reason=partial kline support for crypto_spot without API key
- `yahoo_unofficial` — dataset=partial, asset=partial, api_key=no, reason=partial kline support for crypto_spot without API key
- `finnhub` — dataset=api_key, asset=api_key, api_key=yes, reason=api_key kline support for crypto_spot with API key (FINNHUB_API_KEY)

### crypto_perp_funding

- `binance_futures` — dataset=live, asset=live, api_key=no, reason=live funding support for crypto_perpetual without API key
- `bybit_linear` — dataset=live, asset=live, api_key=no, reason=live funding support for crypto_perpetual without API key
- `offline_fallback` — dataset=fallback, asset=fallback, api_key=no, reason=fallback funding support for crypto_perpetual without API key

### equity_daily_ohlcv

- `stooq` — dataset=live, asset=live, api_key=no, reason=live kline support for equity without API key; EOD/public-first sources are preferred when available.
- `yahoo_unofficial` — dataset=partial, asset=partial, api_key=no, reason=partial kline support for equity without API key; EOD/public-first sources are preferred when available.
- `alpha_vantage` — dataset=api_key, asset=api_key, api_key=yes, reason=api_key kline support for equity with API key (ALPHAVANTAGE_API_KEY); EOD/public-first sources are preferred when available.
- `financial_modeling_prep` — dataset=api_key, asset=api_key, api_key=yes, reason=api_key kline support for equity with API key (FMP_API_KEY); EOD/public-first sources are preferred when available.
- `finnhub` — dataset=api_key, asset=api_key, api_key=yes, reason=api_key kline support for equity with API key (FINNHUB_API_KEY); EOD/public-first sources are preferred when available.

### equity_intraday_ohlcv

- `stooq` — dataset=live, asset=live, api_key=no, reason=live kline support for equity without API key
- `yahoo_unofficial` — dataset=partial, asset=partial, api_key=no, reason=partial kline support for equity without API key
- `alpha_vantage` — dataset=api_key, asset=api_key, api_key=yes, reason=api_key kline support for equity with API key (ALPHAVANTAGE_API_KEY)
- `financial_modeling_prep` — dataset=api_key, asset=api_key, api_key=yes, reason=api_key kline support for equity with API key (FMP_API_KEY)
- `finnhub` — dataset=api_key, asset=api_key, api_key=yes, reason=api_key kline support for equity with API key (FINNHUB_API_KEY)

### macro_rates

- `ecb` — dataset=live, asset=live, api_key=no, reason=live tick support for forex, macro without API key; Public FX/reference-rate feeds are preferred.
- `frankfurter_fx` — dataset=live, asset=live, api_key=no, reason=live tick support for forex, macro without API key; Public FX/reference-rate feeds are preferred.
- `kraken_spot` — dataset=live, asset=live, api_key=no, reason=live tick support for forex, macro without API key; Public FX/reference-rate feeds are preferred.
- `world_bank` — dataset=live, asset=live, api_key=no, reason=live macro support for forex, macro without API key; Public FX/reference-rate feeds are preferred.
- `defillama` — dataset=partial, asset=partial, api_key=no, reason=partial macro support for forex, macro without API key; Public FX/reference-rate feeds are preferred.

### macro_indicators

- `ecb` — dataset=live, asset=live, api_key=no, reason=live macro support for macro, forex without API key
- `frankfurter_fx` — dataset=live, asset=live, api_key=no, reason=live macro support for macro, forex without API key
- `world_bank` — dataset=live, asset=live, api_key=no, reason=live macro support for macro, forex without API key
- `defillama` — dataset=partial, asset=partial, api_key=no, reason=partial macro support for macro, forex without API key
- `fred` — dataset=api_key, asset=api_key, api_key=yes, reason=api_key macro support for macro, forex with API key (FRED_API_KEY)

### public_news

- `gdelt` — dataset=live, asset=n/a, api_key=no, reason=live news support without API key; No-key news/event feeds are preferred for this use case.
- `hacker_news` — dataset=live, asset=n/a, api_key=no, reason=live news support without API key; No-key news/event feeds are preferred for this use case.
- `sec_edgar` — dataset=partial, asset=n/a, api_key=no, reason=partial news support without API key; No-key news/event feeds are preferred for this use case.
- `financial_modeling_prep` — dataset=api_key, asset=n/a, api_key=yes, reason=api_key news support with API key (FMP_API_KEY); No-key news/event feeds are preferred for this use case.
- `finnhub` — dataset=api_key, asset=n/a, api_key=yes, reason=api_key news support with API key (FINNHUB_API_KEY); No-key news/event feeds are preferred for this use case.

### fundamentals

- `defillama` — dataset=partial, asset=n/a, api_key=no, reason=partial fundamentals support without API key
- `sec_edgar` — dataset=partial, asset=n/a, api_key=no, reason=partial fundamentals support without API key
- `alpha_vantage` — dataset=api_key, asset=n/a, api_key=yes, reason=api_key fundamentals support with API key (ALPHAVANTAGE_API_KEY)
- `financial_modeling_prep` — dataset=api_key, asset=n/a, api_key=yes, reason=api_key fundamentals support with API key (FMP_API_KEY)
- `finnhub` — dataset=api_key, asset=n/a, api_key=yes, reason=api_key fundamentals support with API key (FINNHUB_API_KEY)

### options

- `yahoo_unofficial` — dataset=partial, asset=partial, api_key=no, reason=partial kline support for options without API key; Coverage is often plan-dependent for richer options endpoints.
- `financial_modeling_prep` — dataset=api_key, asset=api_key, api_key=yes, reason=api_key kline support for options with API key (FMP_API_KEY); Coverage is often plan-dependent for richer options endpoints.
- `polygon_io` — dataset=api_key_or_plan, asset=api_key_or_plan, api_key=yes, reason=api_key_or_plan kline support for options with API key (POLYGON_API_KEY); Coverage is often plan-dependent for richer options endpoints.

### offline_demo

- `offline_fallback` — dataset=fallback, asset=fallback, api_key=no, reason=fallback kline support for crypto_perpetual without API key; offline_fallback should only be used for tutorial/smoke/demo flows.
- `binance_futures` — dataset=live, asset=live, api_key=no, reason=live kline support for crypto_perpetual without API key; offline_fallback should only be used for tutorial/smoke/demo flows.
- `bybit_linear` — dataset=live, asset=live, api_key=no, reason=live kline support for crypto_perpetual without API key; offline_fallback should only be used for tutorial/smoke/demo flows.
