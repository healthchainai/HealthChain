"""IO module for data containers and adapters.

This module provides:
- Containers: Data structures for clinical documents
- Adapters: Convert external formats (CDA, CDS Hooks) to/from HealthChain
"""

from .containers import DataContainer, Document
from .adapters.base import BaseAdapter
from .adapters.cdaadapter import CdaAdapter
from .adapters.cdsfhiradapter import CdsFhirAdapter

__all__ = [
    # Containers
    "DataContainer",
    "Document",
    # Adapters
    "BaseAdapter",
    "CdaAdapter",
    "CdsFhirAdapter",
]
