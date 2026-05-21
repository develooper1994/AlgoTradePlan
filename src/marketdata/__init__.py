"""MarketData compatibility package for staged data-layer extraction.

This package mirrors the current AlgoTradePlan data-layer public surface while
internally reusing existing implementations for parity-safe migration.
"""

from src.marketdata.capabilities import SourceCapability
from src.marketdata.contracts import (
    DataRecord,
    DataRequest,
    ProvenanceRecord,
    QualityReport,
    StorageReceipt,
)
from src.marketdata.etl import ETL
from src.marketdata.ingestion import DataHub, IngestResult

__all__ = [
    "DataHub",
    "ETL",
    "IngestResult",
    "SourceCapability",
    "DataRequest",
    "DataRecord",
    "QualityReport",
    "StorageReceipt",
    "ProvenanceRecord",
]
