from .base import BaseDocument
from .document import Document

__all__ = ["BaseDocument", "Document"]


# Tombstones for names removed in 0.16.0. DataContainer and the ML feature layer
# (Dataset, FeatureSchema) used to be importable from here as well as from
# `healthchain.io`. Raising a guiding ImportError (rather than a bare AttributeError)
# points anyone — or any code assistant working from the 0.15 API — at the current
# pattern and cookbook.
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
}


def __getattr__(name: str):
    if name in _REMOVED_IN_0_16:
        raise ImportError(_REMOVED_IN_0_16[name])
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
