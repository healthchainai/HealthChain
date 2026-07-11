"""IO module for data containers and adapters.

This module provides:
- Containers: Data structures for clinical documents
- Adapters: Convert external formats (CDA, CDS Hooks) to/from HealthChain
"""

from .containers import Document
from .adapters.base import BaseAdapter
from .adapters.cdsfhiradapter import CdsFhirAdapter

__all__ = [
    # Containers
    "Document",
    # Adapters
    "BaseAdapter",
    "CdaAdapter",
    "CdsFhirAdapter",
]


_CDA_EXTRA_MESSAGE = (
    "CDA support requires the cda extra. Install it with: pip install healthchain[cda]"
)


# Tombstones for names removed in 0.16.0. The generic DataContainer and the ML feature
# layer (Dataset, FeatureSchema, mappers, dataframe conversion, and their supporting
# types) were removed to keep the IO surface FHIR+AI native. Raising a guiding
# ImportError (rather than a bare AttributeError) points anyone — or any code assistant
# working from the 0.15 API — at the current pattern and cookbook.
_REMOVED_IN_0_16 = {
    "DataContainer": (
        "DataContainer was removed in 0.16.0. The generic container was removed; use "
        "Document directly (it wraps raw text automatically when passed to a Pipeline)."
    ),
    "Dataset": (
        "Dataset was removed in 0.16.0 with the ML feature layer — extract what you "
        "need from FHIR resources with your own pandas code; see the ml_risk_to_fhir "
        "cookbook for the pattern."
    ),
    "FeatureSchema": (
        "FeatureSchema was removed in 0.16.0 with the ML feature layer — extract what "
        "you need from FHIR resources with your own pandas code; see the "
        "ml_risk_to_fhir cookbook for the pattern."
    ),
    "FHIRFeatureMapper": (
        "FHIRFeatureMapper was removed in 0.16.0 with the ML feature layer — extract "
        "what you need from FHIR resources with your own pandas code; see the "
        "ml_risk_to_fhir cookbook for the pattern."
    ),
    "BaseMapper": (
        "BaseMapper was removed in 0.16.0 with the ML feature layer — extract what you "
        "need from FHIR resources with your own pandas code; see the ml_risk_to_fhir "
        "cookbook for the pattern."
    ),
    "bundle_to_dataframe": (
        "bundle_to_dataframe was removed in 0.16.0 with the ML feature layer — extract "
        "what you need from FHIR resources with your own pandas code; see the "
        "ml_risk_to_fhir cookbook for the pattern."
    ),
    "TimeWindow": (
        "TimeWindow was removed in 0.16.0 with the ML feature layer — extract what you "
        "need from FHIR resources with your own pandas code; see the ml_risk_to_fhir "
        "cookbook for the pattern."
    ),
    "ValidationResult": (
        "ValidationResult was removed in 0.16.0 with the ML feature layer — extract "
        "what you need from FHIR resources with your own pandas code; see the "
        "ml_risk_to_fhir cookbook for the pattern."
    ),
}


def __getattr__(name: str):
    if name == "CdaAdapter":
        try:
            from .adapters.cdaadapter import CdaAdapter

            return CdaAdapter
        except (ImportError, ModuleNotFoundError) as e:
            raise ImportError(_CDA_EXTRA_MESSAGE) from e
    if name in _REMOVED_IN_0_16:
        raise ImportError(_REMOVED_IN_0_16[name])
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
