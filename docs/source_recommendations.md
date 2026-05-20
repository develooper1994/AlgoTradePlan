# Source Recommendations

Bu doküman DataHub `recommend_sources()` API'sinden üretilir.

## Recommended Sources by Use Case

| Use case | Best sources | Alternatives | API key needed | Notes |
|---|---|---|---|---|
| crypto_spot_kline | coinbase_spot, kraken_spot | coingecko, yahoo_unofficial | No | live kline support for crypto_spot without provider credentials |
| crypto_perp_funding | binance_futures, bybit_linear | offline_fallback | No | live funding support for crypto_perpetual without provider credentials |
| equity_daily_ohlcv | stooq, yahoo_unofficial | alpha_vantage, financial_modeling_prep | No | live kline support for equity without provider credentials; EOD/public-first sources are preferred when available. |
| equity_intraday_ohlcv | stooq, yahoo_unofficial | alpha_vantage, financial_modeling_prep | No | live kline support for equity without provider credentials |
| macro_rates | ecb, frankfurter_fx | kraken_spot, world_bank | No | live tick support for forex, macro without provider credentials; Public FX/reference-rate feeds are preferred. |
| macro_indicators | ecb, frankfurter_fx | world_bank, defillama | No | live macro support for macro, forex without provider credentials |
| public_news | gdelt, hacker_news | sec_edgar, financial_modeling_prep | No | live news support without provider credentials; No-key news/event feeds are preferred for this use case. |
| fundamentals | defillama, sec_edgar | alpha_vantage, financial_modeling_prep | No | partial fundamentals support without provider credentials |
| options | yahoo_unofficial | financial_modeling_prep, polygon_io | No | partial kline support for options without provider credentials; Coverage is often plan-dependent for richer options endpoints. |
| offline_demo | offline_fallback, binance_futures | bybit_linear | No | fallback kline support for crypto_perpetual without provider credentials; offline_fallback should only be used for tutorial/smoke/demo flows. |
| tefas_fund_nav | tefas_public | - | No | partial fund_nav support for mutual_fund, pension_fund without provider credentials |
| tefas_fund_profile | tefas_public | - | No | partial fund_profile support for mutual_fund, pension_fund without provider credentials |
| tefas_fund_returns | tefas_public | - | No | partial fund_return support for mutual_fund, pension_fund without provider credentials |
| tefas_fund_allocation | tefas_public | - | No | partial fund_allocation support for mutual_fund, pension_fund without provider credentials |
| tefas_fund_screener | tefas_public | - | No | partial fund_profile support for mutual_fund, pension_fund without provider credentials; Optional tefas-cli integration is required for live fetch. |
| tefas_fund_research | tefas_public | - | No | partial fund_nav support for mutual_fund, pension_fund without provider credentials; Optional tefas-cli integration is required for live fetch. |

### crypto_spot_kline

- `coinbase_spot` — dataset=live, asset=live, credentials=no, reason=live kline support for crypto_spot without provider credentials
- `kraken_spot` — dataset=live, asset=live, credentials=no, reason=live kline support for crypto_spot without provider credentials
- `coingecko` — dataset=partial, asset=partial, credentials=no, reason=partial kline support for crypto_spot without provider credentials
- `yahoo_unofficial` — dataset=partial, asset=partial, credentials=no, reason=partial kline support for crypto_spot without provider credentials
- `finnhub` — dataset=api_key, asset=api_key, credentials=yes, reason=api_key kline support for crypto_spot with provider credentials

### crypto_perp_funding

- `binance_futures` — dataset=live, asset=live, credentials=no, reason=live funding support for crypto_perpetual without provider credentials
- `bybit_linear` — dataset=live, asset=live, credentials=no, reason=live funding support for crypto_perpetual without provider credentials
- `offline_fallback` — dataset=fallback, asset=fallback, credentials=no, reason=fallback funding support for crypto_perpetual without provider credentials

### equity_daily_ohlcv

- `stooq` — dataset=live, asset=live, credentials=no, reason=live kline support for equity without provider credentials; EOD/public-first sources are preferred when available.
- `yahoo_unofficial` — dataset=partial, asset=partial, credentials=no, reason=partial kline support for equity without provider credentials; EOD/public-first sources are preferred when available.
- `alpha_vantage` — dataset=api_key, asset=api_key, credentials=yes, reason=api_key kline support for equity with provider credentials; EOD/public-first sources are preferred when available.
- `financial_modeling_prep` — dataset=api_key, asset=api_key, credentials=yes, reason=api_key kline support for equity with provider credentials; EOD/public-first sources are preferred when available.
- `finnhub` — dataset=api_key, asset=api_key, credentials=yes, reason=api_key kline support for equity with provider credentials; EOD/public-first sources are preferred when available.

### equity_intraday_ohlcv

- `stooq` — dataset=live, asset=live, credentials=no, reason=live kline support for equity without provider credentials
- `yahoo_unofficial` — dataset=partial, asset=partial, credentials=no, reason=partial kline support for equity without provider credentials
- `alpha_vantage` — dataset=api_key, asset=api_key, credentials=yes, reason=api_key kline support for equity with provider credentials
- `financial_modeling_prep` — dataset=api_key, asset=api_key, credentials=yes, reason=api_key kline support for equity with provider credentials
- `finnhub` — dataset=api_key, asset=api_key, credentials=yes, reason=api_key kline support for equity with provider credentials

### macro_rates

- `ecb` — dataset=live, asset=live, credentials=no, reason=live tick support for forex, macro without provider credentials; Public FX/reference-rate feeds are preferred.
- `frankfurter_fx` — dataset=live, asset=live, credentials=no, reason=live tick support for forex, macro without provider credentials; Public FX/reference-rate feeds are preferred.
- `kraken_spot` — dataset=live, asset=live, credentials=no, reason=live tick support for forex, macro without provider credentials; Public FX/reference-rate feeds are preferred.
- `world_bank` — dataset=live, asset=live, credentials=no, reason=live macro support for forex, macro without provider credentials; Public FX/reference-rate feeds are preferred.
- `defillama` — dataset=partial, asset=partial, credentials=no, reason=partial macro support for forex, macro without provider credentials; Public FX/reference-rate feeds are preferred.

### macro_indicators

- `ecb` — dataset=live, asset=live, credentials=no, reason=live macro support for macro, forex without provider credentials
- `frankfurter_fx` — dataset=live, asset=live, credentials=no, reason=live macro support for macro, forex without provider credentials
- `world_bank` — dataset=live, asset=live, credentials=no, reason=live macro support for macro, forex without provider credentials
- `defillama` — dataset=partial, asset=partial, credentials=no, reason=partial macro support for macro, forex without provider credentials
- `fred` — dataset=api_key, asset=api_key, credentials=yes, reason=api_key macro support for macro, forex with provider credentials

### public_news

- `gdelt` — dataset=live, asset=n/a, credentials=no, reason=live news support without provider credentials; No-key news/event feeds are preferred for this use case.
- `hacker_news` — dataset=live, asset=n/a, credentials=no, reason=live news support without provider credentials; No-key news/event feeds are preferred for this use case.
- `sec_edgar` — dataset=partial, asset=n/a, credentials=no, reason=partial news support without provider credentials; No-key news/event feeds are preferred for this use case.
- `financial_modeling_prep` — dataset=api_key, asset=n/a, credentials=yes, reason=api_key news support with provider credentials; No-key news/event feeds are preferred for this use case.
- `finnhub` — dataset=api_key, asset=n/a, credentials=yes, reason=api_key news support with provider credentials; No-key news/event feeds are preferred for this use case.

### fundamentals

- `defillama` — dataset=partial, asset=n/a, credentials=no, reason=partial fundamentals support without provider credentials
- `sec_edgar` — dataset=partial, asset=n/a, credentials=no, reason=partial fundamentals support without provider credentials
- `alpha_vantage` — dataset=api_key, asset=n/a, credentials=yes, reason=api_key fundamentals support with provider credentials
- `financial_modeling_prep` — dataset=api_key, asset=n/a, credentials=yes, reason=api_key fundamentals support with provider credentials
- `finnhub` — dataset=api_key, asset=n/a, credentials=yes, reason=api_key fundamentals support with provider credentials

### options

- `yahoo_unofficial` — dataset=partial, asset=partial, credentials=no, reason=partial kline support for options without provider credentials; Coverage is often plan-dependent for richer options endpoints.
- `financial_modeling_prep` — dataset=api_key, asset=api_key, credentials=yes, reason=api_key kline support for options with provider credentials; Coverage is often plan-dependent for richer options endpoints.
- `polygon_io` — dataset=api_key_or_plan, asset=api_key_or_plan, credentials=yes, reason=api_key_or_plan kline support for options with provider credentials; Coverage is often plan-dependent for richer options endpoints.

### offline_demo

- `offline_fallback` — dataset=fallback, asset=fallback, credentials=no, reason=fallback kline support for crypto_perpetual without provider credentials; offline_fallback should only be used for tutorial/smoke/demo flows.
- `binance_futures` — dataset=live, asset=live, credentials=no, reason=live kline support for crypto_perpetual without provider credentials; offline_fallback should only be used for tutorial/smoke/demo flows.
- `bybit_linear` — dataset=live, asset=live, credentials=no, reason=live kline support for crypto_perpetual without provider credentials; offline_fallback should only be used for tutorial/smoke/demo flows.

### tefas_fund_nav

- `tefas_public` — dataset=partial, asset=partial, credentials=no, reason=partial fund_nav support for mutual_fund, pension_fund without provider credentials

### tefas_fund_profile

- `tefas_public` — dataset=partial, asset=partial, credentials=no, reason=partial fund_profile support for mutual_fund, pension_fund without provider credentials

### tefas_fund_returns

- `tefas_public` — dataset=partial, asset=partial, credentials=no, reason=partial fund_return support for mutual_fund, pension_fund without provider credentials

### tefas_fund_allocation

- `tefas_public` — dataset=partial, asset=partial, credentials=no, reason=partial fund_allocation support for mutual_fund, pension_fund without provider credentials

### tefas_fund_screener

- `tefas_public` — dataset=partial, asset=partial, credentials=no, reason=partial fund_profile support for mutual_fund, pension_fund without provider credentials; Optional tefas-cli integration is required for live fetch.

### tefas_fund_research

- `tefas_public` — dataset=partial, asset=partial, credentials=no, reason=partial fund_nav support for mutual_fund, pension_fund without provider credentials; Optional tefas-cli integration is required for live fetch.
