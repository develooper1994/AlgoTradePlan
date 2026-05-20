from __future__ import annotations

import pathlib
import sys
from collections import defaultdict
from pathlib import Path

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.algotradeplan.data import DataHub


DOC_PATH = Path("docs/data_source_coverage.md")
COLUMNS = [
    "Source",
    "Asset classes",
    "Asset discovery",
    "Ticker",
    "OHLCV/Kline",
    "Trades",
    "Orderbook",
    "Funding",
    "Equity",
    "ETF",
    "Forex",
    "Index",
    "Futures",
    "Options",
    "Macro",
    "News",
    "Fundamentals",
    "Corporate actions",
    "Requires API key",
    "Implementation status",
    "Notes",
]
DATASETS = ["tick", "kline", "trade", "orderbook", "funding", "macro", "news", "fundamentals", "corporate_actions"]


def _markdown_table(rows: list[dict[str, str]], columns: list[str]) -> str:
    header = "| " + " | ".join(columns) + " |"
    sep = "|" + "|".join(["---"] * len(columns)) + "|"
    body = [
        "| " + " | ".join(str(row.get(column, "")).replace("\n", " ") for column in columns) + " |"
        for row in rows
    ]
    return "\n".join([header, sep, *body])


def _bullet_list(items: list[str]) -> str:
    return "\n".join(f"- `{item}`" for item in items) if items else "- _none_"


def generate(path: Path = DOC_PATH) -> str:
    hub = DataHub()
    rows = hub.coverage_table()
    summaries = [hub.source_summary(source) for source in hub.sources()]
    dataset_index: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
    asset_index: dict[str, list[str]] = defaultdict(list)
    for source in hub.sources():
        summary = hub.source_summary(source)
        for dataset, status in summary["dataset_statuses"].items():
            if status != "unsupported":
                dataset_index[dataset][status].append(source)
        for asset_class, status in summary["asset_statuses"].items():
            if status != "unsupported":
                asset_index[asset_class].append(f"{source} ({status})")

    live_sources = [summary["source"] for summary in summaries if summary["implementation_status"] == "live"]
    api_key_sources = [summary["source"] for summary in summaries if summary["requires_api_key"]]
    metadata_only_sources = [
        summary["source"]
        for summary in summaries
        if summary["implementation_status"] == "metadata_only" or summary["metadata_only_datasets"]
    ]
    fallback_sources = [summary["source"] for summary in summaries if summary["implementation_status"] == "fallback"]
    notes = [summary["notes"] for summary in summaries if summary["notes"]]

    dataset_rows = []
    for dataset in sorted(dataset_index):
        statuses = dataset_index[dataset]
        dataset_rows.append(
            {
                "Dataset": dataset,
                "live": ", ".join(sorted(statuses.get("live", []))) or "-",
                "partial": ", ".join(sorted(statuses.get("partial", []))) or "-",
                "fallback": ", ".join(sorted(statuses.get("fallback", []))) or "-",
                "api_key/api_key_or_plan": ", ".join(sorted(statuses.get("api_key", []) + statuses.get("api_key_or_plan", []))) or "-",
                "metadata_only": ", ".join(sorted(statuses.get("metadata_only", []))) or "-",
            }
        )
    dataset_table = _markdown_table(
        dataset_rows,
        ["Dataset", "live", "partial", "fallback", "api_key/api_key_or_plan", "metadata_only"],
    )
    asset_rows = [{"Asset class": asset, "Sources": ", ".join(sorted(asset_index[asset]))} for asset in sorted(asset_index)]
    asset_table = _markdown_table(asset_rows, ["Asset class", "Sources"])
    full_matrix = _markdown_table(rows, COLUMNS)
    best_kline = hub.best_sources_for(dataset="kline", asset_class="crypto_spot", allow_api_key=False, limit=5)
    best_funding = hub.best_sources_for(dataset="funding", asset_class="crypto_perpetual", allow_api_key=False, limit=5)
    best_macro = hub.best_sources_for(dataset="macro", asset_class="macro", include_metadata_only=True, limit=5)
    best_news = hub.best_sources_for(dataset="news", include_metadata_only=True, limit=5)

    def _best_rows(items: list[dict[str, str]]) -> str:
        if not items:
            return "- _none_"
        return "\n".join(
            f"- `{item['source']}` (dataset={item['dataset_status']}, asset={item['asset_status']}, api_key={item['requires_api_key']})"
            for item in items
        )

    content = (
        "# Data Source Coverage\n\n"
        "Bu doküman `scripts/generate_data_coverage_doc.py` ile üretilir.\n\n"
        "## Status values\n\n"
        "- `live`: adapter fetch'i framework içinde çalışıyor.\n"
        "- `partial`: source/dataset kısmen uygulanmış veya bazı alanlar türetiliyor.\n"
        "- `api_key`: framework adapter var ama API key gerekiyor.\n"
        "- `api_key_or_plan`: API key + plan kapsamı sonucu etkiliyor.\n"
        "- `metadata_only`: capability biliniyor ama framework fetch'i yok.\n"
        "- `fallback`: deterministic/offline fallback source.\n"
        "- `unsupported`: source bu dataset/asset class için uygun değil.\n\n"
        "## Full matrix\n\n"
        f"{full_matrix}\n\n"
        "## Dataset → Sources index\n\n"
        f"{dataset_table}\n\n"
        "## Asset class → Sources index\n\n"
        f"{asset_table}\n\n"
        "## Best sources examples\n\n"
        "### best crypto spot kline sources\n\n"
        f"{_best_rows(best_kline)}\n\n"
        "### best crypto perpetual funding sources\n\n"
        f"{_best_rows(best_funding)}\n\n"
        "### best macro sources\n\n"
        f"{_best_rows(best_macro)}\n\n"
        "### best news sources\n\n"
        f"{_best_rows(best_news)}\n\n"
        "## Live fetch sources\n\n"
        f"{_bullet_list(live_sources)}\n\n"
        "## API-key required sources\n\n"
        f"{_bullet_list(api_key_sources)}\n\n"
        "## Metadata-only sources\n\n"
        f"{_bullet_list(metadata_only_sources)}\n\n"
        "## Fallback sources\n\n"
        f"{_bullet_list(fallback_sources)}\n\n"
        "## Important notes\n\n"
        "- CoinGecko OHLCV çıktısı synthetic_ohlcv metadata ile close-based market_chart bucket üzerinden üretilir.\n"
        "- API-key / paid-plan kaynaklarda gerçek kapsam plan seviyesine göre değişebilir.\n"
        "- offline_fallback kaynağı deterministic smoke/backtest fallback amaçlıdır.\n"
        + "\n".join(f"- {note}" for note in sorted(set(notes)))
        + "\n"
    )
    path.write_text(content, encoding="utf-8")
    return content


if __name__ == "__main__":
    generate()
    print(f"data_coverage_doc_generated path={DOC_PATH}")
