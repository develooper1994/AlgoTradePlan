# Data Source Coverage

Bu doküman `scripts/generate_data_coverage_doc.py` ile üretilir.

## Status values

- `live`: adapter fetch'i framework içinde çalışıyor.
- `partial`: source/dataset kısmen uygulanmış veya bazı alanlar türetiliyor.
- `api_key`: framework adapter var ama API key gerekiyor.
- `api_key_or_plan`: API key + plan kapsamı sonucu etkiliyor.
- `metadata_only`: capability biliniyor ama framework fetch'i yok.
- `fallback`: deterministic/offline fallback source.
- `unsupported`: source bu dataset/asset class için uygun değil.

## Full matrix

| Source | Asset classes | Asset discovery | Ticker | OHLCV/Kline | Trades | Orderbook | Funding | Equity | ETF | Forex | Index | Futures | Options | Macro | News | Fundamentals | Corporate actions | Requires API key | Implementation status | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| alpha_vantage | equity, etf, forex | live | api_key | api_key | unsupported | unsupported | unsupported | api_key | api_key | api_key | unsupported | unsupported | unsupported | unsupported | unsupported | api_key | unsupported | yes | api_key | Framework fetches GLOBAL_QUOTE, intraday/daily kline, and Company Overview fundamentals when ALPHAVANTAGE_API_KEY is available; ingest reports api_key_required when the key is missing. |
| binance_futures | crypto_perpetual | live | live | live | live | live | live | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | no | live | Public futures REST endpoints; respect exchange burst limits. |
| bybit_linear | crypto_perpetual | live | live | live | live | live | live | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | no | live | Public linear market endpoints; funding available. |
| coinbase_spot | crypto_spot | live | live | live | live | live | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | no | live | Public exchange endpoints; no funding feed. |
| coingecko | crypto_spot | live | partial | partial | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | metadata_only | unsupported | unsupported | no | partial | OHLCV is synthesized from market_chart close/volume buckets; pro tiers can widen endpoint coverage. |
| defillama | crypto_spot, macro | live | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | partial | metadata_only | partial | unsupported | no | partial | Protocol catalog is cached in-process to avoid repeated list fetches; macro tracks TVL time-series and fundamentals track protocol-level snapshot fields. |
| ecb | macro, forex | live | live | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | live | unsupported | unsupported | unsupported | live | unsupported | unsupported | unsupported | no | live | FX fetches are parameterized by quote symbol such as USD, GBP, or JPY. |
| financial_modeling_prep | equity, etf, options | live | api_key | api_key | unsupported | unsupported | unsupported | api_key | api_key | unsupported | unsupported | unsupported | api_key | unsupported | api_key | api_key | api_key | yes | api_key | Minimal adapter is available through the DataHub registry; endpoint scope still depends on API plan. |
| finnhub | equity, etf, forex, crypto_spot | live | api_key | api_key | unsupported | unsupported | unsupported | api_key | api_key | api_key | unsupported | unsupported | unsupported | unsupported | api_key | api_key | unsupported | yes | api_key | Framework fetches quote/candles plus company-news and profile skeletons when FINNHUB_API_KEY is available; ingest reports api_key_required when token is missing. |
| frankfurter_fx | forex, macro | live | live | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | live | unsupported | unsupported | unsupported | live | unsupported | unsupported | unsupported | no | live | Public FX reference rates. |
| fred | macro | live | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | api_key | unsupported | unsupported | unsupported | yes | api_key | Provides macro series such as FEDFUNDS, CPIAUCSL, UNRATE, DGS10, and GDP. |
| gdelt | news | live | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | live | unsupported | unsupported | no | live | News/event metadata feed. |
| hacker_news | news | live | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | live | unsupported | unsupported | no | live | Public story search used as a smoke-news source. |
| iex_cloud | equity, etf | live | api_key | api_key | api_key | unsupported | unsupported | api_key | api_key | unsupported | unsupported | unsupported | unsupported | unsupported | api_key | unsupported | api_key | yes | api_key | Framework fetches quote/chart plus news and dividend-style corporate action skeletons when IEX_CLOUD_API_KEY is available; ingest reports api_key_required when token is missing. |
| kraken_spot | crypto_spot, forex | live | live | live | live | live | unsupported | unsupported | unsupported | live | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | no | live | Public spot endpoints; funding derived as unsupported. |
| offline_fallback | crypto_perpetual | live | fallback | fallback | fallback | fallback | fallback | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | no | fallback | Deterministic fallback used only when live public sources are unreachable. |
| polygon_io | equity, etf, options, forex, crypto_spot | live | api_key_or_plan | api_key_or_plan | api_key_or_plan | unsupported | unsupported | api_key_or_plan | api_key_or_plan | api_key_or_plan | unsupported | unsupported | api_key_or_plan | unsupported | api_key_or_plan | unsupported | api_key_or_plan | yes | api_key_or_plan | Aggregates/quotes are fetchable and news/splits skeleton fetches are available; options richness and some endpoints remain API-plan dependent. |
| quandl | futures, macro, equity | live | unsupported | api_key | unsupported | unsupported | unsupported | api_key | unsupported | unsupported | unsupported | api_key | unsupported | api_key | unsupported | metadata_only | unsupported | yes | api_key | Current registry adapter focuses on historical futures/price series and exposes a macro-style skeleton for dataset snapshots. |
| sec_edgar | equity | live | unsupported | unsupported | unsupported | unsupported | unsupported | partial | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | partial | partial | partial | no | partial | Uses public SEC ticker, submissions, and company facts endpoints for filing/news-style metadata. |
| stooq | equity, etf, index, forex | live | unsupported | live | unsupported | unsupported | unsupported | live | live | live | live | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | no | live | Symbols/datasets are typically user-provided (e.g. aapl.us); timestamps are normalized from source dates to epoch-ms. |
| twelve_data | equity, etf, forex, index, crypto_spot | live | api_key | api_key | unsupported | unsupported | unsupported | api_key | api_key | api_key | api_key | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | yes | api_key | API-keyed intraday time series provider. |
| world_bank | macro | live | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | live | unsupported | unsupported | unsupported | no | live | Pass `country=` to target WLD, TUR, USA, or other ISO/World Bank country codes. |
| yahoo_unofficial | crypto_spot, equity, etf, forex, index, options | live | partial | partial | unsupported | unsupported | unsupported | partial | partial | partial | partial | unsupported | partial | unsupported | unsupported | unsupported | unsupported | no | partial | Discovery + tick/kline available via unofficial chart/search responses; options coverage remains example-level metadata. |

## Dataset → Sources index

| Dataset | live | partial | fallback | api_key/api_key_or_plan | metadata_only |
|---|---|---|---|---|---|
| corporate_actions | - | sec_edgar | - | financial_modeling_prep, iex_cloud, polygon_io | - |
| fundamentals | - | defillama, sec_edgar | - | alpha_vantage, financial_modeling_prep, finnhub | quandl |
| funding | binance_futures, bybit_linear | - | offline_fallback | - | - |
| kline | binance_futures, bybit_linear, coinbase_spot, kraken_spot, stooq | coingecko, yahoo_unofficial | offline_fallback | alpha_vantage, financial_modeling_prep, finnhub, iex_cloud, polygon_io, quandl, twelve_data | - |
| macro | ecb, frankfurter_fx, world_bank | defillama | - | fred, quandl | - |
| news | gdelt, hacker_news | sec_edgar | - | financial_modeling_prep, finnhub, iex_cloud, polygon_io | coingecko, defillama |
| orderbook | binance_futures, bybit_linear, coinbase_spot, kraken_spot | - | offline_fallback | - | - |
| tick | binance_futures, bybit_linear, coinbase_spot, ecb, frankfurter_fx, kraken_spot | coingecko, yahoo_unofficial | offline_fallback | alpha_vantage, financial_modeling_prep, finnhub, iex_cloud, polygon_io, twelve_data | - |
| trade | binance_futures, bybit_linear, coinbase_spot, kraken_spot | - | offline_fallback | iex_cloud, polygon_io | - |

## Asset class → Sources index

| Asset class | Sources |
|---|---|
| crypto_perpetual | binance_futures (live), bybit_linear (live), offline_fallback (fallback) |
| crypto_spot | coinbase_spot (live), coingecko (partial), defillama (partial), finnhub (api_key), kraken_spot (live), polygon_io (api_key_or_plan), twelve_data (api_key), yahoo_unofficial (partial) |
| equity | alpha_vantage (api_key), financial_modeling_prep (api_key), finnhub (api_key), iex_cloud (api_key), polygon_io (api_key_or_plan), quandl (api_key), sec_edgar (partial), stooq (live), twelve_data (api_key), yahoo_unofficial (partial) |
| etf | alpha_vantage (api_key), financial_modeling_prep (api_key), finnhub (api_key), iex_cloud (api_key), polygon_io (api_key_or_plan), stooq (live), twelve_data (api_key), yahoo_unofficial (partial) |
| forex | alpha_vantage (api_key), ecb (live), finnhub (api_key), frankfurter_fx (live), kraken_spot (live), polygon_io (api_key_or_plan), stooq (live), twelve_data (api_key), yahoo_unofficial (partial) |
| futures | quandl (api_key) |
| index | stooq (live), twelve_data (api_key), yahoo_unofficial (partial) |
| macro | defillama (partial), ecb (live), frankfurter_fx (live), fred (api_key), quandl (api_key), world_bank (live) |
| news | gdelt (live), hacker_news (live) |
| options | financial_modeling_prep (api_key), polygon_io (api_key_or_plan), yahoo_unofficial (partial) |

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

## Live fetch sources

- `binance_futures`
- `bybit_linear`
- `coinbase_spot`
- `ecb`
- `frankfurter_fx`
- `gdelt`
- `hacker_news`
- `kraken_spot`
- `stooq`
- `world_bank`

## Public / no-key providers

- `binance_futures`
- `bybit_linear`
- `coinbase_spot`
- `coingecko`
- `defillama`
- `ecb`
- `frankfurter_fx`
- `gdelt`
- `hacker_news`
- `kraken_spot`
- `offline_fallback`
- `sec_edgar`
- `stooq`
- `world_bank`
- `yahoo_unofficial`

## API-key providers

- `alpha_vantage`
- `financial_modeling_prep`
- `finnhub`
- `fred`
- `iex_cloud`
- `polygon_io`
- `quandl`
- `twelve_data`

## Metadata-only sources

- `coingecko`
- `defillama`
- `quandl`

## Fallback / offline providers

- `offline_fallback`

## Important notes

- CoinGecko OHLCV çıktısı synthetic_ohlcv metadata ile close-based market_chart bucket üzerinden üretilir.
- API-key / paid-plan kaynaklarda gerçek kapsam plan seviyesine göre değişebilir.
- offline_fallback kaynağı deterministic smoke/backtest/demo amaçlıdır.
- API-keyed intraday time series provider.
- Aggregates/quotes are fetchable and news/splits skeleton fetches are available; options richness and some endpoints remain API-plan dependent.
- Current registry adapter focuses on historical futures/price series and exposes a macro-style skeleton for dataset snapshots.
- Deterministic fallback used only when live public sources are unreachable.
- Discovery + tick/kline available via unofficial chart/search responses; options coverage remains example-level metadata.
- FX fetches are parameterized by quote symbol such as USD, GBP, or JPY.
- Framework fetches GLOBAL_QUOTE, intraday/daily kline, and Company Overview fundamentals when ALPHAVANTAGE_API_KEY is available; ingest reports api_key_required when the key is missing.
- Framework fetches quote/candles plus company-news and profile skeletons when FINNHUB_API_KEY is available; ingest reports api_key_required when token is missing.
- Framework fetches quote/chart plus news and dividend-style corporate action skeletons when IEX_CLOUD_API_KEY is available; ingest reports api_key_required when token is missing.
- Minimal adapter is available through the DataHub registry; endpoint scope still depends on API plan.
- News/event metadata feed.
- OHLCV is synthesized from market_chart close/volume buckets; pro tiers can widen endpoint coverage.
- Pass `country=` to target WLD, TUR, USA, or other ISO/World Bank country codes.
- Protocol catalog is cached in-process to avoid repeated list fetches; macro tracks TVL time-series and fundamentals track protocol-level snapshot fields.
- Provides macro series such as FEDFUNDS, CPIAUCSL, UNRATE, DGS10, and GDP.
- Public FX reference rates.
- Public exchange endpoints; no funding feed.
- Public futures REST endpoints; respect exchange burst limits.
- Public linear market endpoints; funding available.
- Public spot endpoints; funding derived as unsupported.
- Public story search used as a smoke-news source.
- Symbols/datasets are typically user-provided (e.g. aapl.us); timestamps are normalized from source dates to epoch-ms.
- Uses public SEC ticker, submissions, and company facts endpoints for filing/news-style metadata.
