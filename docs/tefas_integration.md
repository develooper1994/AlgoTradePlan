# TEFAS Integration (Optional)

AlgoTradePlan, TEFAS kaynağını opsiyonel olarak `tefas-cli` üzerinden destekler.

## Neden `tefas-cli`?

- TEFAS verileri public web katmanından geliyor.
- `tefas-cli`, Chrome debugger ile doğrulanan yeni endpoint/HTML-parser akışını kapsar.
- Bu entegrasyon **legacy `tefas_scraper` `/api/DB/...` endpointlerine dayanmaz**.

## Runtime Kurulum

```bash
# Preferred (canonical): set `TEFAS_CLI_CMD` to the tefas-cli executable.
export TEFAS_CLI_CMD=/path/to/tefas-cli
# Backward-compatible: `TEFAS_CLI_BIN` is still supported.
export TEFAS_CLI_BIN=/path/to/tefas-cli
export TEFAS_FFI_LIB=/path/to/libtefas_ffi.so
```

Entegre fetch için `TEFAS_CLI_CMD` önerilir; `TEFAS_CLI_BIN` geri uyumluluk içindir. `TEFAS_FFI_LIB` tespit/dokümantasyon için desteklenir.

## Source ve Datasetler

- Source: `tefas_public`
- Datasetler:
  - `fund_nav`
  - `fund_profile`
  - `fund_return`
  - `fund_allocation`
  - `fund_size`
  - `fund_fee`
  - `fund_announcement`
  - `fund_statistics`

## Komut Örnekleri

```bash
python -m algotradeplan explain source tefas_public
python -m algotradeplan recommend --use-case tefas_fund_screener --no-api-key
python -m algotradeplan preflight --source tefas_public --symbol AFT --datasets fund_nav fund_profile --strategy fund_momentum
python -m algotradeplan health --source tefas_public --symbol AFT --datasets fund_nav fund_profile --allow-partial
```

## Dependency Yoksa Davranış

- Framework crash etmez.
- `tefas_public` görünür kalır.
- Ingest/preflight `optional_dependency_missing:tefas-cli` ile anlamlı issue döndürür.
-- Öneri: `Build tefas-cli and set TEFAS_CLI_CMD` (or `TEFAS_CLI_BIN` for backward compatibility) `or TEFAS_FFI_LIB`.

## Sınırlamalar

- Official API değildir.
- Public web JSON endpoint + HTML parser entegrasyonudur.
- Endpoint/page formatı değişebilir.
- TEFAS dependency optionaldır.
- Cache/rate-limit friendly kullanım önerilir.
