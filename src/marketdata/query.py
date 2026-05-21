"""MarketData query/recommendation compatibility exports."""

from src.algotradeplan.data.query import (
    asset_sources_matrix,
    asset_status_for_source,
    available_datasets,
    best_sources_for,
    compare_sources,
    dataset_sources_matrix,
    dataset_status_for_source,
    explain_dataset,
    explain_source,
    recommend_sources,
    source_summary,
    sources_for,
    supported_use_cases,
    supports,
)

__all__ = [
    "supported_use_cases",
    "dataset_status_for_source",
    "asset_status_for_source",
    "supports",
    "sources_for",
    "available_datasets",
    "compare_sources",
    "source_summary",
    "best_sources_for",
    "explain_source",
    "explain_dataset",
    "recommend_sources",
    "dataset_sources_matrix",
    "asset_sources_matrix",
]
