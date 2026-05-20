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

| Source | Asset classes | Asset discovery | Ticker | OHLCV/Kline | Trades | Orderbook | Funding | Equity | ETF | Forex | Index | Futures | Options | Macro | News | Fundamentals | Corporate actions | Requires API key | API key env | Implementation status | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| alpha_vantage | equity, etf, forex | live | api_key | api_key | unsupported | unsupported | unsupported | api_key | api_key | api_key | unsupported | unsupported | unsupported | unsupported | unsupported | metadata_only | unsupported | yes | ALPHAVANTAGE_API_KEY | api_key | Framework fetches tick/kline via the market registry adapter; fundamentals remain capability metadata only. |
| binance_futures | crypto_perpetual | live | live | live | live | live | live | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | no |  | live | Public futures REST endpoints; respect exchange burst limits. |
| bybit_linear | crypto_perpetual | live | live | live | live | live | live | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | no |  | live | Public linear market endpoints; funding available. |
| coinbase_spot | crypto_spot | live | live | live | live | live | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | no |  | live | Public exchange endpoints; no funding feed. |
| coingecko | crypto_spot | live | partial | partial | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | metadata_only | unsupported | unsupported | no |  | partial | OHLCV is synthesized from market_chart close/volume buckets; pro tiers can widen endpoint coverage. |
| defillama | crypto_spot, macro | live | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | partial | metadata_only | partial | unsupported | no |  | partial | Protocol catalog is cached in-process to avoid repeated list fetches. |
| ecb | macro, forex | live | live | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | live | unsupported | unsupported | unsupported | live | unsupported | unsupported | unsupported | no |  | live | FX fetches are parameterized by quote symbol such as USD, GBP, or JPY. |
| financial_modeling_prep | equity, etf, options | live | api_key | api_key | unsupported | unsupported | unsupported | api_key | api_key | unsupported | unsupported | unsupported | api_key | unsupported | api_key | api_key | api_key | yes | FMP_API_KEY | api_key | Minimal adapter is available through the DataHub registry; endpoint scope still depends on API plan. |
| finnhub | equity, etf, forex, crypto_spot | live | api_key | api_key | unsupported | unsupported | unsupported | api_key | api_key | api_key | unsupported | unsupported | unsupported | unsupported | metadata_only | metadata_only | unsupported | yes | FINNHUB_API_KEY | api_key | Framework exposes market data fetches; fundamentals/news are capability metadata for future adapter expansion. |
| frankfurter_fx | forex, macro | live | live | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | live | unsupported | unsupported | unsupported | live | unsupported | unsupported | unsupported | no |  | live | Public FX reference rates. |
| fred | macro | live | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | api_key | unsupported | unsupported | unsupported | yes | FRED_API_KEY | api_key | Provides macro series such as FEDFUNDS, CPIAUCSL, UNRATE, DGS10, and GDP. |
| gdelt | news | live | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | live | unsupported | unsupported | no |  | live | News/event metadata feed. |
| hacker_news | news | live | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | live | unsupported | unsupported | no |  | live | Public story search used as a smoke-news source. |
| iex_cloud | equity, etf | live | api_key | api_key | api_key | unsupported | unsupported | api_key | api_key | unsupported | unsupported | unsupported | unsupported | unsupported | metadata_only | unsupported | metadata_only | yes | IEX_CLOUD_API_KEY | api_key | Market data is implemented through the registry adapter; richer datasets remain roadmap items. |
| kraken_spot | crypto_spot, forex | live | live | live | live | live | unsupported | unsupported | unsupported | live | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | no |  | live | Public spot endpoints; funding derived as unsupported. |
| offline_fallback | crypto_perpetual | live | fallback | fallback | fallback | fallback | fallback | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | no |  | fallback | Deterministic fallback used only when live public sources are unreachable. |
| polygon_io | equity, etf, options, forex, crypto_spot | live | api_key_or_plan | api_key_or_plan | api_key_or_plan | unsupported | unsupported | api_key_or_plan | api_key_or_plan | api_key_or_plan | unsupported | unsupported | api_key_or_plan | unsupported | metadata_only | unsupported | metadata_only | yes | POLYGON_API_KEY | api_key_or_plan | Core market datasets are fetchable; advanced datasets depend on plan coverage and remain metadata-only in the framework. |
| quandl | futures, macro, equity | live | unsupported | api_key | unsupported | unsupported | unsupported | api_key | unsupported | unsupported | unsupported | api_key | unsupported | metadata_only | unsupported | metadata_only | unsupported | yes | QUANDL_API_KEY | api_key | Current registry adapter focuses on historical price series. |
| sec_edgar | equity | live | unsupported | unsupported | unsupported | unsupported | unsupported | partial | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | partial | partial | partial | no |  | partial | Uses public SEC ticker, submissions, and company facts endpoints for filing/news-style metadata. |
| stooq | equity, etf, index, forex | live | unsupported | live | unsupported | unsupported | unsupported | live | live | live | live | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | no |  | live | Symbols/datasets are typically user-provided (e.g. aapl.us); timestamps are normalized from source dates to epoch-ms. |
| twelve_data | equity, etf, forex, index, crypto_spot | live | api_key | api_key | unsupported | unsupported | unsupported | api_key | api_key | api_key | api_key | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | yes | TWELVEDATA_API_KEY | api_key | API-keyed intraday time series provider. |
| world_bank | macro | live | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | live | unsupported | unsupported | unsupported | no |  | live | Pass `country=` to target WLD, TUR, USA, or other ISO/World Bank country codes. |
| yahoo_unofficial | crypto_spot, equity, etf, forex, index, options | live | partial | partial | unsupported | unsupported | unsupported | partial | partial | partial | partial | unsupported | partial | unsupported | unsupported | unsupported | unsupported | no |  | partial | Discovery + tick/kline available via unofficial chart/search responses; options coverage remains example-level metadata. |

## Dataset → Sources index

| Dataset | Sources |
|---|---|
| corporate_actions | financial_modeling_prep (api_key), iex_cloud (metadata_only), polygon_io (metadata_only), sec_edgar (partial) |
| fundamentals | alpha_vantage (metadata_only), defillama (partial), financial_modeling_prep (api_key), finnhub (metadata_only), quandl (metadata_only), sec_edgar (partial) |
| funding | binance_futures (live), bybit_linear (live), offline_fallback (fallback) |
| kline | alpha_vantage (api_key), binance_futures (live), bybit_linear (live), coinbase_spot (live), coingecko (partial), financial_modeling_prep (api_key), finnhub (api_key), iex_cloud (api_key), kraken_spot (live), offline_fallback (fallback), polygon_io (api_key_or_plan), quandl (api_key), stooq (live), twelve_data (api_key), yahoo_unofficial (partial) |
| macro | defillama (partial), ecb (live), frankfurter_fx (live), fred (api_key), quandl (metadata_only), world_bank (live) |
| news | coingecko (metadata_only), defillama (metadata_only), financial_modeling_prep (api_key), finnhub (metadata_only), gdelt (live), hacker_news (live), iex_cloud (metadata_only), polygon_io (metadata_only), sec_edgar (partial) |
| orderbook | binance_futures (live), bybit_linear (live), coinbase_spot (live), kraken_spot (live), offline_fallback (fallback) |
| tick | alpha_vantage (api_key), binance_futures (live), bybit_linear (live), coinbase_spot (live), coingecko (partial), ecb (live), financial_modeling_prep (api_key), finnhub (api_key), frankfurter_fx (live), iex_cloud (api_key), kraken_spot (live), offline_fallback (fallback), polygon_io (api_key_or_plan), twelve_data (api_key), yahoo_unofficial (partial) |
| trade | binance_futures (live), bybit_linear (live), coinbase_spot (live), iex_cloud (api_key), kraken_spot (live), offline_fallback (fallback), polygon_io (api_key_or_plan) |

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

- CoinGecko OHLCV çıktısı close-based synthetic bucket olarak üretilir.
- API-key / paid-plan kaynaklarda gerçek kapsam plan seviyesine göre değişebilir.
- API-keyed intraday time series provider.
- Core market datasets are fetchable; advanced datasets depend on plan coverage and remain metadata-only in the framework.
- Current registry adapter focuses on historical price series.
- Deterministic fallback used only when live public sources are unreachable.
- Discovery + tick/kline available via unofficial chart/search responses; options coverage remains example-level metadata.
- FX fetches are parameterized by quote symbol such as USD, GBP, or JPY.
- Framework exposes market data fetches; fundamentals/news are capability metadata for future adapter expansion.
- Framework fetches tick/kline via the market registry adapter; fundamentals remain capability metadata only.
- Market data is implemented through the registry adapter; richer datasets remain roadmap items.
- Minimal adapter is available through the DataHub registry; endpoint scope still depends on API plan.
- News/event metadata feed.
- OHLCV is synthesized from market_chart close/volume buckets; pro tiers can widen endpoint coverage.
- Pass `country=` to target WLD, TUR, USA, or other ISO/World Bank country codes.
- Protocol catalog is cached in-process to avoid repeated list fetches.
- Provides macro series such as FEDFUNDS, CPIAUCSL, UNRATE, DGS10, and GDP.
- Public FX reference rates.
- Public exchange endpoints; no funding feed.
- Public futures REST endpoints; respect exchange burst limits.
- Public linear market endpoints; funding available.
- Public spot endpoints; funding derived as unsupported.
- Public story search used as a smoke-news source.
- Symbols/datasets are typically user-provided (e.g. aapl.us); timestamps are normalized from source dates to epoch-ms.
- Uses public SEC ticker, submissions, and company facts endpoints for filing/news-style metadata.
