"""Normalize raw source payloads into canonical schema records."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import UTC, datetime
from typing import Any

from src.algotradeplan.core.canonical import (
    FundingRateRecord,
    MacroSnapshot,
    NewsItem,
    OHLCVRecord,
    OrderbookSnapshot,
    TradeRecord,
)
from src.algotradeplan.plugins.data.contracts import DataRecord


OHLCV_METADATA_INDEX = 6


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _to_int(value: Any, default: int) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _to_epoch_ms(value: Any, default: int) -> int:
    if isinstance(value, (int, float)):
        return _to_int(value, default)
    if isinstance(value, str):
        text = value.strip()
        for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S"):
            try:
                return int(datetime.strptime(text, fmt).replace(tzinfo=UTC).timestamp() * 1000)
            except ValueError:
                continue
    return _to_int(value, default)


def _to_optional_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _pick(mapping: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in mapping and mapping[key] not in (None, ""):
            return mapping[key]
    return None


def _to_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "evet", "yes"}:
            return True
        if normalized in {"false", "0", "hayir", "hayır", "no"}:
            return False
    return None


def _exchange_name(source: str) -> str:
    if source.endswith("_spot"):
        return source.removesuffix("_spot")
    if source.endswith("_futures"):
        return source.removesuffix("_futures")
    if source.endswith("_fx"):
        return source.removesuffix("_fx")
    return source.split("_", 1)[0]


def _now_ms() -> int:
    return int(datetime.now(UTC).timestamp() * 1000)


def normalize_ohlcv(source: str, symbol: str, rows: list[Any]) -> list[OHLCVRecord]:
    exchange = _exchange_name(source)
    normalized: list[OHLCVRecord] = []
    for row in rows:
        if not isinstance(row, list) or len(row) < 5:
            continue
        timestamp_ms = _to_epoch_ms(row[0], _now_ms())
        metadata = row[OHLCV_METADATA_INDEX] if len(row) > OHLCV_METADATA_INDEX and isinstance(row[OHLCV_METADATA_INDEX], dict) else {}
        normalized.append(
            OHLCVRecord(
                symbol=symbol,
                exchange=exchange,
                timestamp_ms=timestamp_ms,
                open=_to_float(row[1]),
                high=_to_float(row[2]),
                low=_to_float(row[3]),
                close=_to_float(row[4]),
                volume=_to_float(row[5], 0.0) if len(row) > 5 else 0.0,
                source=source,
                metadata=metadata,
            )
        )
    return normalized


def normalize_trade(source: str, symbol: str, rows: list[Any]) -> list[TradeRecord]:
    exchange = _exchange_name(source)
    normalized: list[TradeRecord] = []
    for index, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            continue
        normalized.append(
            TradeRecord(
                symbol=symbol,
                exchange=exchange,
                trade_id=str(row.get("id") or row.get("trade_id") or row.get("i") or index),
                timestamp_ms=_to_epoch_ms(row.get("time") or row.get("T") or row.get("timestamp"), _now_ms() + index),
                price=_to_float(row.get("price") or row.get("p") or row.get("lastPrice")),
                quantity=_to_float(row.get("qty") or row.get("size") or row.get("q") or 0.0),
                side=str(row.get("side") or row.get("S") or "buy").lower(),
                source=source,
                metadata={"raw": row},
            )
        )
    return normalized


def normalize_orderbook(source: str, symbol: str, rows: list[Any]) -> list[OrderbookSnapshot]:
    exchange = _exchange_name(source)
    normalized: list[OrderbookSnapshot] = []
    for index, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            continue
        bids = row.get("bids") or row.get("b") or []
        asks = row.get("asks") or row.get("a") or []
        if not bids and row.get("bid") is not None:
            bids = [[row.get("bid"), 0.0]]
        if not asks and row.get("ask") is not None:
            asks = [[row.get("ask"), 0.0]]
        normalized.append(
            OrderbookSnapshot(
                symbol=symbol,
                exchange=exchange,
                timestamp_ms=_to_epoch_ms(row.get("timestamp") or row.get("ts"), _now_ms() + index),
                bids=[[_to_float(level[0]), _to_float(level[1], 0.0)] for level in bids if isinstance(level, list) and len(level) >= 2],
                asks=[[_to_float(level[0]), _to_float(level[1], 0.0)] for level in asks if isinstance(level, list) and len(level) >= 2],
                source=source,
            )
        )
    return normalized


def normalize_funding(source: str, symbol: str, rows: list[Any]) -> list[FundingRateRecord]:
    exchange = _exchange_name(source)
    normalized: list[FundingRateRecord] = []
    for index, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            continue
        normalized.append(
            FundingRateRecord(
                symbol=symbol,
                exchange=exchange,
                timestamp_ms=_to_epoch_ms(row.get("fundingTime") or row.get("timestamp"), _now_ms() + index),
                rate=_to_float(row.get("fundingRate") or row.get("rate") or 0.0),
                next_funding_timestamp_ms=_to_epoch_ms(row.get("nextFundingTime"), 0) or None,
                derived=bool(row.get("derived", False)),
                source=source,
                metadata={"raw": row},
            )
        )
    return normalized


def normalize_tick(source: str, symbol: str, rows: list[Any]) -> list[dict[str, Any]]:
    exchange = _exchange_name(source)
    normalized: list[dict[str, Any]] = []
    for index, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            continue
        normalized.append(
            {
                "symbol": str(row.get("symbol") or symbol),
                "exchange": exchange,
                "timestamp_ms": _to_epoch_ms(row.get("time") or row.get("timestamp"), _now_ms() + index),
                "price": _to_float(row.get("price") or row.get("lastPrice") or row.get("c"), 0.0),
                "source": source,
                "metadata": {"raw": row},
            }
        )
    return normalized


def normalize_news(source: str, asset: str, rows: list[Any]) -> list[NewsItem]:
    normalized: list[NewsItem] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        normalized.append(
            NewsItem(
                title=str(row.get("title") or row.get("headline") or asset),
                url=str(row.get("url") or row.get("story_url") or ""),
                source=source,
                published_at=str(row.get("created_at") or row.get("publishedDate") or row.get("published_at") or datetime.now(UTC).isoformat()),
                assets=[asset.upper()] if asset else [],
                metadata={"raw": row},
            )
        )
    return normalized


def normalize_macro(source: str, base_currency: str, payload: dict[str, Any]) -> list[MacroSnapshot]:
    if not isinstance(payload, dict):
        return []
    timestamp = str(payload.get("date") or payload.get("timestamp") or datetime.now(UTC).date().isoformat())
    rates = {str(key): _to_float(value) for key, value in payload.get("rates", {}).items()}
    return [
        MacroSnapshot(
            base_currency=str(payload.get("base") or base_currency),
            timestamp=timestamp,
            rates=rates,
            source=source,
            metadata={"raw": payload},
        )
    ]


def normalize_fundamentals(source: str, symbol: str, payload: Any) -> list[dict[str, Any]]:
    rows = payload if isinstance(payload, list) else [payload]
    normalized: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        normalized.append(
            {
                "symbol": symbol,
                "source": source,
                "timestamp_ms": _now_ms(),
                "fields": row,
            }
        )
    return normalized


def normalize_corporate_actions(source: str, symbol: str, payload: Any) -> list[dict[str, Any]]:
    rows = payload if isinstance(payload, list) else [payload]
    normalized: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        normalized.append(
            {
                "symbol": symbol,
                "source": source,
                "timestamp_ms": _now_ms(),
                "action": row.get("form") or row.get("label") or row.get("type") or "unknown_action",
                "fields": row,
            }
        )
    return normalized


def _tefas_dict_rows(payload: Any) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if isinstance(payload, list):
        for item in payload:
            if isinstance(item, dict) and "data" in item and "operation" in item:
                rows.extend(_tefas_dict_rows(item.get("data")))
            elif isinstance(item, dict):
                rows.append(item)
        return rows
    if isinstance(payload, dict):
        for key in ("resultList", "rows", "items", "data"):
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
        return [payload]
    return []


def normalize_tefas_fund_nav(source: str, symbol: str, payload: Any) -> list[dict[str, Any]]:
    rows = _tefas_dict_rows(payload)
    normalized: list[dict[str, Any]] = []
    for index, row in enumerate(rows, start=1):
        timestamp_ms = _to_epoch_ms(_pick(row, "timestamp_ms", "tarih", "date", "timestamp"), _now_ms() + index)
        normalized.append(
            {
                "date": str(_pick(row, "tarih", "date") or ""),
                "timestamp_ms": timestamp_ms,
                "fund_code": str(_pick(row, "fonKodu", "fund_code", "symbol") or symbol).upper(),
                "fund_name": str(_pick(row, "fonUnvan", "fund_name", "name") or symbol),
                "nav": _to_float(_pick(row, "fiyat", "nav", "price"), 0.0),
                "currency": str(_pick(row, "dovizCinsi", "currency") or "TRY"),
                "source": source,
            }
        )
    return normalized


def normalize_tefas_fund_profile(source: str, symbol: str, payload: Any) -> list[dict[str, Any]]:
    rows = _tefas_dict_rows(payload)
    normalized: list[dict[str, Any]] = []
    for row in rows:
        normalized.append(
            {
                "fund_code": str(_pick(row, "fonKodu", "fund_code", "symbol") or symbol).upper(),
                "fund_name": str(_pick(row, "fonUnvan", "fund_name", "name") or symbol),
                "isin": str(_pick(row, "isin_kodu", "isin", "isinCode") or ""),
                "category": str(_pick(row, "kategori", "category") or ""),
                "risk_value": _to_optional_float(_pick(row, "fon_risk_degeri", "risk_value", "risk")),
                "investor_count": _to_int(_pick(row, "yatirimci_sayisi", "investor_count") or 0, 0),
                "total_value_try": _to_optional_float(_pick(row, "fon_toplam_deger_tl", "total_value_try", "total_value")),
                "kap_url": str(_pick(row, "kap_bilgi_adresi", "kap_url") or ""),
                "platform_tradable": _to_bool(_pick(row, "platform_islem_goruyor", "platform_tradable")),
                "source": source,
            }
        )
    return normalized


def normalize_tefas_fund_return(source: str, symbol: str, payload: Any) -> list[dict[str, Any]]:
    rows = _tefas_dict_rows(payload)
    normalized: list[dict[str, Any]] = []
    for row in rows:
        normalized.append(
            {
                "fund_code": str(_pick(row, "fonKodu", "fund_code", "symbol") or symbol).upper(),
                "return_1m_pct": _to_optional_float(_pick(row, "return_1m_pct", "getiri_1a", "Aylik", "bir_ay")),
                "return_3m_pct": _to_optional_float(_pick(row, "return_3m_pct", "getiri_3a", "UcAylik", "uc_ay")),
                "return_6m_pct": _to_optional_float(_pick(row, "return_6m_pct", "getiri_6a", "AltiAylik", "alti_ay")),
                "return_1y_pct": _to_optional_float(_pick(row, "return_1y_pct", "getiri_1y", "BirYillik", "bir_yil")),
                "return_3y_pct": _to_optional_float(_pick(row, "return_3y_pct", "getiri_3y", "UcYillik", "uc_yil")),
                "return_5y_pct": _to_optional_float(_pick(row, "return_5y_pct", "getiri_5y", "BesYillik", "bes_yil")),
                "source": source,
            }
        )
    return normalized


def normalize_tefas_fund_allocation(source: str, symbol: str, payload: Any) -> list[dict[str, Any]]:
    rows = _tefas_dict_rows(payload)
    normalized: list[dict[str, Any]] = []
    for row in rows:
        normalized.append(
            {
                "fund_code": str(_pick(row, "fonKodu", "fund_code", "symbol") or symbol).upper(),
                "asset_type": str(_pick(row, "asset_type", "varlikTuru", "dagilimGrubu", "name") or ""),
                "weight_pct": _to_optional_float(_pick(row, "weight_pct", "oran", "yuzde", "weight")),
                "date": str(_pick(row, "tarih", "date") or ""),
                "source": source,
            }
        )
    return normalized


def normalize_tefas_fund_size(source: str, symbol: str, payload: Any) -> list[dict[str, Any]]:
    rows = _tefas_dict_rows(payload)
    normalized: list[dict[str, Any]] = []
    for row in rows:
        normalized.append(
            {
                "fund_code": str(_pick(row, "fonKodu", "fund_code", "symbol") or symbol).upper(),
                "date": str(_pick(row, "tarih", "date") or ""),
                "aum_try": _to_optional_float(_pick(row, "aum_try", "fon_toplam_deger_tl", "buyukluk", "value")),
                "share_count": _to_optional_float(_pick(row, "share_count", "pay_sayisi", "shares")),
                "source": source,
            }
        )
    return normalized


def normalize_tefas_fund_fee(source: str, symbol: str, payload: Any) -> list[dict[str, Any]]:
    rows = _tefas_dict_rows(payload)
    normalized: list[dict[str, Any]] = []
    for row in rows:
        normalized.append(
            {
                "fund_code": str(_pick(row, "fonKodu", "fund_code", "symbol") or symbol).upper(),
                "management_fee_pct": _to_optional_float(_pick(row, "management_fee_pct", "yonetim_ucreti", "managementFee")),
                "expense_ratio_pct": _to_optional_float(_pick(row, "expense_ratio_pct", "gider_orani", "expenseRatio")),
                "source": source,
            }
        )
    return normalized


def normalize_tefas_announcements(source: str, symbol: str, payload: Any) -> list[dict[str, Any]]:
    rows = _tefas_dict_rows(payload)
    normalized: list[dict[str, Any]] = []
    for row in rows:
        normalized.append(
            {
                "fund_code": str(_pick(row, "fonKodu", "fund_code", "symbol") or symbol).upper(),
                "title": str(_pick(row, "title", "duyuruBaslik", "baslik") or ""),
                "kap_url": str(_pick(row, "kap_url", "kap_bilgi_adresi", "url") or ""),
                "announcement_id": str(_pick(row, "announcement_id", "duyuruId", "id") or ""),
                "source": source,
            }
        )
    return normalized


def normalize_tefas_statistics(source: str, symbol: str, payload: Any) -> list[dict[str, Any]]:
    rows = _tefas_dict_rows(payload)
    normalized: list[dict[str, Any]] = []
    for row in rows:
        fund_code = str(_pick(row, "fonKodu", "fund_code", "symbol") or symbol).upper()
        metric = _pick(row, "metric", "metrik", "name")
        value = _pick(row, "value", "deger")
        if metric is not None and value is not None:
            normalized.append(
                {
                    "fund_code": fund_code,
                    "metric": str(metric),
                    "value": value,
                    "period": str(_pick(row, "period", "donem", "date") or ""),
                    "currency": str(_pick(row, "currency", "dovizCinsi") or ""),
                    "source": source,
                }
            )
            continue
        for key, raw_value in row.items():
            if key in {"fonKodu", "fund_code", "symbol", "date", "tarih", "period", "donem", "currency", "dovizCinsi"}:
                continue
            if isinstance(raw_value, (dict, list)):
                continue
            normalized.append(
                {
                    "fund_code": fund_code,
                    "metric": str(key),
                    "value": raw_value,
                    "period": str(_pick(row, "period", "donem", "date", "tarih") or ""),
                    "currency": str(_pick(row, "currency", "dovizCinsi") or ""),
                    "source": source,
                }
            )
    return normalized


def normalize_dataset(dataset: str, source: str, symbol: str, payload: Any) -> list[Any]:
    if dataset == "tick":
        rows = payload if isinstance(payload, list) else [payload]
        return normalize_tick(source, symbol, rows)
    if dataset == "kline":
        return normalize_ohlcv(source, symbol, payload if isinstance(payload, list) else [])
    if dataset == "trade":
        return normalize_trade(source, symbol, payload if isinstance(payload, list) else [])
    if dataset == "orderbook":
        rows = payload if isinstance(payload, list) else [payload]
        return normalize_orderbook(source, symbol, rows)
    if dataset == "funding":
        return normalize_funding(source, symbol, payload if isinstance(payload, list) else [])
    if dataset == "news":
        return normalize_news(source, symbol, payload if isinstance(payload, list) else [])
    if dataset == "macro":
        return normalize_macro(source, symbol, payload if isinstance(payload, dict) else {})
    if dataset == "fundamentals":
        return normalize_fundamentals(source, symbol, payload)
    if dataset == "corporate_actions":
        return normalize_corporate_actions(source, symbol, payload)
    if dataset == "fund_nav":
        return normalize_tefas_fund_nav(source, symbol, payload)
    if dataset == "fund_profile":
        return normalize_tefas_fund_profile(source, symbol, payload)
    if dataset == "fund_return":
        return normalize_tefas_fund_return(source, symbol, payload)
    if dataset == "fund_allocation":
        return normalize_tefas_fund_allocation(source, symbol, payload)
    if dataset == "fund_size":
        return normalize_tefas_fund_size(source, symbol, payload)
    if dataset == "fund_fee":
        return normalize_tefas_fund_fee(source, symbol, payload)
    if dataset == "fund_announcement":
        return normalize_tefas_announcements(source, symbol, payload)
    if dataset == "fund_statistics":
        return normalize_tefas_statistics(source, symbol, payload)
    return []


def to_data_records(dataset: str, source: str, asset_type: str, items: list[Any]) -> list[DataRecord]:
    records: list[DataRecord] = []
    for index, item in enumerate(items, start=1):
        payload = asdict(item) if is_dataclass(item) else dict(item)
        timestamp_ms = int(payload.get("timestamp_ms") or _now_ms() + index)
        symbol = str(payload.get("symbol") or payload.get("base_currency") or payload.get("title") or source)
        records.append(
            DataRecord(
                key=f"{source}:{dataset}:{symbol}:{timestamp_ms}:{index}",
                observed_at=datetime.fromtimestamp(timestamp_ms / 1000, tz=UTC).isoformat(),
                domain="market" if dataset in {"kline", "trade", "orderbook", "funding", "tick"} else dataset,
                source=source,
                asset_type=asset_type,
                payload=payload,
                metadata={"dataset": dataset, "join_key": symbol, "canonical": True},
            )
        )
    return records
