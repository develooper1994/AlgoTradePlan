"""MarketData contract DTOs and plugin interface compatibility exports."""

from src.algotradeplan.plugins.data.contracts import (
    DataRecord,
    DataRequest,
    ProvenanceRecord,
    QualityReport,
    StorageReceipt,
)
from src.algotradeplan.plugins.data.interfaces import (
    DataQualityPlugin,
    DataSourcePlugin,
    DataStoragePlugin,
    ProvenancePlugin,
)

__all__ = [
    "DataRequest",
    "DataRecord",
    "QualityReport",
    "StorageReceipt",
    "ProvenanceRecord",
    "DataSourcePlugin",
    "DataStoragePlugin",
    "DataQualityPlugin",
    "ProvenancePlugin",
]
