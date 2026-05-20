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
| alpha_vantage | equity, etf, forex | live | api_key | api_key | unsupported | unsupported | unsupported | api_key | api_key | api_key | unsupported | unsupported | unsupported | unsupported | unsupported | metadata_only | unsupported | yes | api_key | Framework fetches tick/kline via the market registry adapter; fundamentals remain capability metadata only and ingest reports api_key_required when the key is missing. |
| binance_futures | crypto_perpetual | live | live | live | live | live | live | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | no | live | Public futures REST endpoints; respect exchange burst limits. |
| bybit_linear | crypto_perpetual | live | live | live | live | live | live | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | no | live | Public linear market endpoints; funding available. |
| coinbase_spot | crypto_spot | live | live | live | live | live | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | no | live | Public exchange endpoints; no funding feed. |
| coingecko | crypto_spot | live | partial | partial | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | metadata_only | unsupported | unsupported | no | partial | OHLCV is synthesized from market_chart close/volume buckets; pro tiers can widen endpoint coverage. |
| defillama | crypto_spot, macro | live | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | partial | metadata_only | partial | unsupported | no | partial | Protocol catalog is cached in-process to avoid repeated list fetches; macro tracks TVL time-series and fundamentals track protocol-level snapshot fields. |
| ecb | macro, forex | live | live | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | live | unsupported | unsupported | unsupported | live | unsupported | unsupported | unsupported | no | live | FX fetches are parameterized by quote symbol such as USD, GBP, or JPY. |
| financial_modeling_prep | equity, etf, options | live | api_key | api_key | unsupported | unsupported | unsupported | api_key | api_key | unsupported | unsupported | unsupported | api_key | unsupported | api_key | api_key | api_key | yes | api_key | Minimal adapter is available through the DataHub registry; endpoint scope still depends on API plan. |
| finnhub | equity, etf, forex, crypto_spot | live | api_key | api_key | unsupported | unsupported | unsupported | api_key | api_key | api_key | unsupported | unsupported | unsupported | unsupported | metadata_only | metadata_only | unsupported | yes | api_key | Framework exposes market data fetches; fundamentals/news are capability metadata for future adapter expansion and ingest reports api_key_required when token is missing. |
| frankfurter_fx | forex, macro | live | live | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | live | unsupported | unsupported | unsupported | live | unsupported | unsupported | unsupported | no | live | Public FX reference rates. |
| fred | macro | live | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | api_key | unsupported | unsupported | unsupported | yes | api_key | Provides macro series such as FEDFUNDS, CPIAUCSL, UNRATE, DGS10, and GDP. |
| gdelt | news | live | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | live | unsupported | unsupported | no | live | News/event metadata feed. |
| hacker_news | news | live | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | live | unsupported | unsupported | no | live | Public story search used as a smoke-news source. |
| iex_cloud | equity, etf | live | api_key | api_key | api_key | unsupported | unsupported | api_key | api_key | unsupported | unsupported | unsupported | unsupported | unsupported | metadata_only | unsupported | metadata_only | yes | api_key | Market data is implemented through the registry adapter; richer datasets remain roadmap items and ingest reports api_key_required when token is missing. |
| kraken_spot | crypto_spot, forex | live | live | live | live | live | unsupported | unsupported | unsupported | live | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | no | live | Public spot endpoints; funding derived as unsupported. |
| offline_fallback | crypto_perpetual | live | fallback | fallback | fallback | fallback | fallback | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | no | fallback | Deterministic fallback used only when live public sources are unreachable. |
| polygon_io | equity, etf, options, forex, crypto_spot | live | api_key_or_plan | api_key_or_plan | api_key_or_plan | unsupported | unsupported | api_key_or_plan | api_key_or_plan | api_key_or_plan | unsupported | unsupported | api_key_or_plan | unsupported | metadata_only | unsupported | metadata_only | yes | api_key_or_plan | Core market datasets are fetchable; advanced datasets depend on plan coverage and remain metadata-only in the framework. |
| quandl | futures, macro, equity | live | unsupported | api_key | unsupported | unsupported | unsupported | api_key | unsupported | unsupported | unsupported | api_key | unsupported | metadata_only | unsupported | metadata_only | unsupported | yes | api_key | Current registry adapter focuses on historical price series. |
| sec_edgar | equity | live | unsupported | unsupported | unsupported | unsupported | unsupported | partial | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | partial | partial | partial | no | partial | Uses public SEC ticker, submissions, and company facts endpoints for filing/news-style metadata. |
| stooq | equity, etf, index, forex | live | unsupported | live | unsupported | unsupported | unsupported | live | live | live | live | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | no | live | Symbols/datasets are typically user-provided (e.g. aapl.us); timestamps are normalized from source dates to epoch-ms. |
| twelve_data | equity, etf, forex, index, crypto_spot | live | api_key | api_key | unsupported | unsupported | unsupported | api_key | api_key | api_key | api_key | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | yes | api_key | API-keyed intraday time series provider. |
| world_bank | macro | live | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | live | unsupported | unsupported | unsupported | no | live | Pass `country=` to target WLD, TUR, USA, or other ISO/World Bank country codes. |
| yahoo_unofficial | crypto_spot, equity, etf, forex, index, options | live | partial | partial | unsupported | unsupported | unsupported | partial | partial | partial | partial | unsupported | partial | unsupported | unsupported | unsupported | unsupported | no | partial | Discovery + tick/kline available via unofficial chart/search responses; options coverage remains example-level metadata. |

## Dataset → Sources index

| Dataset | live | partial | fallback | api_key/api_key_or_plan | metadata_only |
|---|---|---|---|---|---|
| corporate_actions | - | sec_edgar | - | financial_modeling_prep | iex_cloud, polygon_io |
| fundamentals | - | defillama, sec_edgar | - | financial_modeling_prep | alpha_vantage, finnhub, quandl |
| funding | binance_futures, bybit_linear | - | offline_fallback | - | - |
| kline | binance_futures, bybit_linear, coinbase_spot, kraken_spot, stooq | coingecko, yahoo_unofficial | offline_fallback | alpha_vantage, financial_modeling_prep, finnhub, iex_cloud, polygon_io, quandl, twelve_data | - |
| macro | ecb, frankfurter_fx, world_bank | defillama | - | fred | quandl |
| news | gdelt, hacker_news | sec_edgar | - | financial_modeling_prep | coingecko, defillama, finnhub, iex_cloud, polygon_io |
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

## Best sources examples

### best crypto spot kline sources

- `coinbase_spot` (dataset=live, asset=live, api_key=no)
- `kraken_spot` (dataset=live, asset=live, api_key=no)
- `coingecko` (dataset=partial, asset=partial, api_key=no)
- `yahoo_unofficial` (dataset=partial, asset=partial, api_key=no)

### best crypto perpetual funding sources

- `binance_futures` (dataset=live, asset=live, api_key=no)
- `bybit_linear` (dataset=live, asset=live, api_key=no)
- `offline_fallback` (dataset=fallback, asset=fallback, api_key=no)

### best macro sources

- `ecb` (dataset=live, asset=live, api_key=no)
- `frankfurter_fx` (dataset=live, asset=live, api_key=no)
- `world_bank` (dataset=live, asset=live, api_key=no)
- `defillama` (dataset=partial, asset=partial, api_key=no)
- `fred` (dataset=api_key, asset=api_key, api_key=yes)

### best news sources

- `gdelt` (dataset=live, asset=n/a, api_key=no)
- `hacker_news` (dataset=live, asset=n/a, api_key=no)
- `sec_edgar` (dataset=partial, asset=n/a, api_key=no)
- `financial_modeling_prep` (dataset=api_key, asset=n/a, api_key=yes)
- `coingecko` (dataset=metadata_only, asset=n/a, api_key=no)

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

## API-key required sources

- `alpha_vantage`
- `financial_modeling_prep`
- `finnhub`
- `fred`
- `iex_cloud`
- `polygon_io`
- `quandl`
- `twelve_data`

## Metadata-only sources

- `alpha_vantage`
- `coingecko`
- `defillama`
- `finnhub`
- `iex_cloud`
- `polygon_io`
- `quandl`

## Fallback sources

- `offline_fallback`

## Important notes

- CoinGecko OHLCV çıktısı synthetic_ohlcv metadata ile close-based market_chart bucket üzerinden üretilir.
- API-key / paid-plan kaynaklarda gerçek kapsam plan seviyesine göre değişebilir.
- offline_fallback kaynağı deterministic smoke/backtest fallback amaçlıdır.
- API-keyed intraday time series provider.
- Core market datasets are fetchable; advanced datasets depend on plan coverage and remain metadata-only in the framework.
- Current registry adapter focuses on historical price series.
- Deterministic fallback used only when live public sources are unreachable.
- Discovery + tick/kline available via unofficial chart/search responses; options coverage remains example-level metadata.
- FX fetches are parameterized by quote symbol such as USD, GBP, or JPY.
- Framework exposes market data fetches; fundamentals/news are capability metadata for future adapter expansion and ingest reports api_key_required when token is missing.
- Framework fetches tick/kline via the market registry adapter; fundamentals remain capability metadata only and ingest reports api_key_required when the key is missing.
- Market data is implemented through the registry adapter; richer datasets remain roadmap items and ingest reports api_key_required when token is missing.
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
