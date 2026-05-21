"""Thin compatibility surface mirroring MarketData client wrappers."""

from src.algotradeplan.data import DataHub, ETL, IngestResult, SourceCapability
from src.algotradeplan.plugins.data.contracts import (
    DataRecord,
    DataRequest,
    ProvenanceRecord,
    QualityReport,
    StorageReceipt,
)

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
