"""SEC EDGAR metadata adapter."""

from __future__ import annotations

from typing import Any, Callable

JsonGetter = Callable[[str, dict[str, Any]], Any]


class SecEdgarAdapter:
    source = "sec_edgar"

    def __init__(self, json_getter: JsonGetter) -> None:
        self._json_getter = json_getter
        self._ticker_cache: dict[str, dict[str, Any]] | None = None

    def discover_assets(self, limit: int = 10, **filters: Any) -> list[str]:
        requested = [str(item).upper() for item in filters.get("symbols", []) if str(item).strip()]
        if requested:
            return requested[:limit]
        return sorted(self._ticker_map())[:limit]

    def fetch_raw(
        self,
        symbol: str,
        datasets: list[str],
        *,
        timeframe: str = "1m",  # noqa: ARG002
        limit: int = 500,
    ) -> dict[str, Any]:
        entry = self._ticker_map().get(symbol.upper())
        if not entry:
            return {dataset: [] for dataset in datasets}
        cik = str(entry.get("cik_str", "")).zfill(10)
        submissions = self._json_getter(f"https://data.sec.gov/submissions/CIK{cik}.json", {})
        recent = submissions.get("filings", {}).get("recent", {})
        count = min(limit, len(recent.get("accessionNumber", [])))
        filings = [
            {
                "symbol": symbol.upper(),
                "form": recent.get("form", [""] * count)[index],
                "filed_at": recent.get("filingDate", [""] * count)[index],
                "accession": recent.get("accessionNumber", [""] * count)[index],
                "primary_document": recent.get("primaryDocument", [""] * count)[index],
                "company": entry.get("title", symbol.upper()),
                "url": _filing_url(cik, recent.get("accessionNumber", [""] * count)[index], recent.get("primaryDocument", [""] * count)[index]),
            }
            for index in range(count)
        ]
        result: dict[str, Any] = {}
        if "fundamentals" in datasets:
            companyfacts = self._json_getter(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json", {})
            result["fundamentals"] = [
                {
                    "symbol": symbol.upper(),
                    "company": entry.get("title", symbol.upper()),
                    "cik": cik,
                    "facts_keys": sorted(companyfacts.get("facts", {}).keys()),
                    "entity_name": companyfacts.get("entityName", entry.get("title", symbol.upper())),
                }
            ]
        if "news" in datasets:
            result["news"] = [
                {
                    "title": f"{item['company']} {item['form']} filing",
                    "url": item["url"],
                    "created_at": item["filed_at"],
                    "form": item["form"],
                }
                for item in filings
                if item.get("form")
            ]
        if "corporate_actions" in datasets:
            result["corporate_actions"] = filings
        return result

    def _ticker_map(self) -> dict[str, dict[str, Any]]:
        if self._ticker_cache is None:
            payload = self._json_getter("https://www.sec.gov/files/company_tickers.json", {})
            self._ticker_cache = {
                str(value.get("ticker", "")).upper(): value
                for value in payload.values()
                if isinstance(value, dict) and value.get("ticker")
            }
        return self._ticker_cache


def _filing_url(cik: str, accession: str, document: str) -> str:
    if not accession or not document:
        return ""
    cleaned_accession = accession.replace("-", "")
    try:
        cik_number = int(cik)
    except (TypeError, ValueError):
        return ""
    return f"https://www.sec.gov/Archives/edgar/data/{cik_number}/{cleaned_accession}/{document}"
