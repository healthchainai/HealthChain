"""Terminology lookup for HealthChain.

A small seam for mapping free text to codings: the ``TerminologyLookup``
protocol, the ``Coding`` model, and ``LocalCodeLookup`` — an in-process
implementation over a demo catalog (RxNorm/LOINC/ICD-10-CM) for offline
demos and tests. Real terminology services implement the same protocol.
"""

from healthchain.terminology.base import Coding, TerminologyLookup
from healthchain.terminology.local import (
    ICD10CM,
    LOINC,
    RXNORM,
    LocalCodeLookup,
)

__all__ = [
    "Coding",
    "TerminologyLookup",
    "LocalCodeLookup",
    "RXNORM",
    "LOINC",
    "ICD10CM",
]
