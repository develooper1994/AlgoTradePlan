"""Coverage compatibility exports via thin DataHub wrapper."""

from src.algotradeplan.data.coverage import (
    ASSET_COLUMNS,
    DATASET_COLUMNS,
    build_coverage_table,
)

__all__ = [
    "DATASET_COLUMNS",
    "ASSET_COLUMNS",
    "build_coverage_table",
]
