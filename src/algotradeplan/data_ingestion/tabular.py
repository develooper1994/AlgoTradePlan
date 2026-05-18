"""Tabular ingestion helpers for CSV/Excel sources."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


def load_csv_rows(path: str) -> list[dict[str, Any]]:
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def load_with_pandas(path: str):
    try:
        import pandas as pd
    except ImportError as exc:  # pragma: no cover - optional dependency path
        raise RuntimeError("Install optional dependency group: data") from exc
    suffix = Path(path).suffix.lower()
    if suffix in {".xlsx", ".xls"}:
        return pd.read_excel(path)
    return pd.read_csv(path)
