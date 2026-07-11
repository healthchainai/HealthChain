"""
Adapters module for HealthChain.

This module contains adapter implementations for converting between different
data formats and HealthChain's internal Document representation.
"""

from .cdsfhiradapter import CdsFhirAdapter
from .base import BaseAdapter

__all__ = ["CdaAdapter", "CdsFhirAdapter", "BaseAdapter"]


def __getattr__(name: str):
    if name == "CdaAdapter":
        try:
            from .cdaadapter import CdaAdapter

            return CdaAdapter
        except (ImportError, ModuleNotFoundError) as e:
            raise ImportError(
                "CDA support requires the cda extra. Install it with: "
                "pip install healthchain[cda]"
            ) from e
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
