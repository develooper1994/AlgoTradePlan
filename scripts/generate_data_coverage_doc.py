from __future__ import annotations

import pathlib
import sys
from collections import defaultdict
from pathlib import Path

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.algotradeplan.data import DataHub


DOC_PATH = Path("docs/data_source_coverage.md")
SOURCE_RECOMMENDATIONS_DOC_PATH = Path("docs/source_recommendations.md")
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
    "API key env",
    "Implementation status",
    "Notes",
]
DATASETS = ["tick", "kline", "trade", "orderbook", "funding", "macro", "news", "fundamentals", "corporate_actions"]
USE_CASES = [
    "crypto_spot_kline",
    "crypto_perp_funding",
    "equity_daily_ohlcv",
    "equity_intraday_ohlcv",
    "macro_rates",
    "macro_indicators",
    "public_news",
    "fundamentals",
    "options",
    "offline_demo",
]


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


def _format_sources(items: list[dict[str, str]], limit: int = 2) -> str:
    sources = [item["source"] for item in items[:limit]]
    return ", ".join(sources) if sources else "-"


def _api_key_label(items: list[dict[str, str]]) -> str:
    if not items:
        return "-"
    if all(item["requires_api_key"] == "no" for item in items):
        return "No"
    if all(item["requires_api_key"] == "yes" for item in items):
        return "Yes"
    return "Optional"


def _recommendation_table_rows(hub: DataHub) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for use_case in USE_CASES:
        all_recommendations = hub.recommend_sources(use_case, allow_api_key=True, limit=6)
        public_recommendations = hub.recommend_sources(use_case, allow_api_key=False, limit=6)
        best = public_recommendations[:2] or all_recommendations[:2]
        alternatives = [
            item for item in all_recommendations if item["source"] not in {row["source"] for row in best}
        ][:2]
        if best:
            notes = best[0]["reason"]
        elif all_recommendations:
            notes = all_recommendations[0]["reason"]
        else:
            notes = "No current recommendation."
        row = {
            "Use case": use_case,
            "Best sources": _format_sources(best),
            "Alternatives": _format_sources(alternatives),
            "API key needed": _api_key_label(best or all_recommendations),
            "Notes": notes,
        }
        rows.append(row)
    return rows


def generate_source_recommendations(path: Path = SOURCE_RECOMMENDATIONS_DOC_PATH) -> str:
    hub = DataHub()
    rows = _recommendation_table_rows(hub)
    table = _markdown_table(rows, ["Use case", "Best sources", "Alternatives", "API key needed", "Notes"])
    detail_lines = ["# Source Recommendations", "", "Bu doküman DataHub `recommend_sources()` API'sinden üretilir.", "", "## Recommended Sources by Use Case", "", table, ""]
    for use_case in USE_CASES:
        recommendations = hub.recommend_sources(use_case, allow_api_key=True, limit=5)
        detail_lines.extend([f"### {use_case}", ""])
        if not recommendations:
            detail_lines.extend(["- _none_", ""])
            continue
        for item in recommendations:
            detail_lines.append(
                f"- `{item['source']}` — dataset={item['dataset_status']}, asset={item['asset_status']}, credentials={item['requires_api_key']}, reason={item['reason']}"
            )
        detail_lines.append("")
    content = "\n".join(detail_lines).rstrip() + "\n"
    path.write_text(content, encoding="utf-8")
    return content


def generate(path: Path = DOC_PATH, *, source_recommendations_path: Path = SOURCE_RECOMMENDATIONS_DOC_PATH) -> str:
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
    public_no_key_sources = [summary["source"] for summary in summaries if not summary["requires_api_key"]]
    api_key_sources = [summary["source"] for summary in summaries if summary["requires_api_key"]]
    metadata_only_sources = [
        summary["source"]
        for summary in summaries
        if summary["implementation_status"] == "metadata_only" or summary["metadata_only_datasets"]
    ]
    fallback_sources = [summary["source"] for summary in summaries if summary["implementation_status"] == "fallback"]
    notes = [str(summary["notes"]) for summary in summaries if summary["notes"]]

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
    recommendation_rows = _recommendation_table_rows(hub)
    recommendation_table = _markdown_table(
        recommendation_rows,
        ["Use case", "Best sources", "Alternatives", "API key needed", "Notes"],
    )
    generate_source_recommendations(source_recommendations_path)

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
        "## Recommended Sources by Use Case\n\n"
        f"{recommendation_table}\n\n"
        "## Live fetch sources\n\n"
        f"{_bullet_list(live_sources)}\n\n"
        "## Public / no-key providers\n\n"
        f"{_bullet_list(public_no_key_sources)}\n\n"
        "## API-key providers\n\n"
        f"{_bullet_list(api_key_sources)}\n\n"
        "## Metadata-only sources\n\n"
        f"{_bullet_list(metadata_only_sources)}\n\n"
        "## Fallback / offline providers\n\n"
        f"{_bullet_list(fallback_sources)}\n\n"
        "## Important notes\n\n"
        "- CoinGecko OHLCV çıktısı synthetic_ohlcv metadata ile close-based market_chart bucket üzerinden üretilir.\n"
        "- API-key / paid-plan kaynaklarda gerçek kapsam plan seviyesine göre değişebilir.\n"
        "- offline_fallback kaynağı deterministic smoke/backtest/demo amaçlıdır.\n"
        + "\n".join(f"- {note}" for note in sorted(set(notes)))
        + "\n"
    )
    path.write_text(content, encoding="utf-8")
    return content


if __name__ == "__main__":
    generate()
    print(f"data_coverage_doc_generated path={DOC_PATH}")
    print(f"source_recommendations_doc_generated path={SOURCE_RECOMMENDATIONS_DOC_PATH}")
