from __future__ import annotations

import pathlib
import sys
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
    "API key env",
    "Implementation status",
    "Notes",
]


def _markdown_table(rows: list[dict[str, str]]) -> str:
    header = "| " + " | ".join(COLUMNS) + " |"
    sep = "|" + "|".join(["---"] * len(COLUMNS)) + "|"
    body = [
        "| " + " | ".join(str(row.get(column, "")).replace("\n", " ") for column in COLUMNS) + " |"
        for row in rows
    ]
    return "\n".join([header, sep, *body])


def generate(path: Path = DOC_PATH) -> str:
    hub = DataHub()
    rows = hub.coverage_table()
    table = _markdown_table(rows)
    content = (
        "# Data Source Coverage\n\n"
        "Bu doküman `scripts/generate_data_coverage_doc.py` ile üretilir.\n\n"
        "Durum değerleri: `live`, `partial`, `api_key`, `api_key_or_plan`, "
        "`metadata_only`, `fallback`, `unsupported`.\n\n"
        f"{table}\n"
    )
    path.write_text(content, encoding="utf-8")
    return content


if __name__ == "__main__":
    generate()
    print(f"data_coverage_doc_generated path={DOC_PATH}")
