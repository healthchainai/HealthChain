from .base import BaseComponent, Component
from .fhirproblemextractor import FHIRProblemListExtractor

__all__ = [
    "BaseComponent",
    "Component",
    "FHIRProblemListExtractor",
]


# Tombstones for names removed in 0.16.0. Model wrappers and the card creator were
# deleted in favour of using the underlying libraries directly with `pipeline.add_node`.
# Raising a guiding ImportError (rather than a bare AttributeError) points anyone — or any
# code assistant working from the 0.15 API — at the current pattern.
_REMOVED_IN_0_16 = {
    "SpacyNLP": (
        "SpacyNLP was removed in 0.16.0. Load spaCy directly with `nlp = spacy.load(...)` "
        "and add it with `pipeline.add_node(...)` — see cookbook/notereader_clinical_coding_fhir.py"
    ),
    "HFTransformer": (
        "HFTransformer was removed in 0.16.0. Use `pipe = transformers.pipeline(...)` "
        "directly and add it with `pipeline.add_node(...)` — see cookbook/cds_discharge_summarizer_hf_trf.py"
    ),
    "LangChainLLM": (
        "LangChainLLM was removed in 0.16.0. Use your LangChain chain directly and add it "
        "with `pipeline.add_node(...)`."
    ),
    "CdsCardCreator": (
        "CdsCardCreator was removed in 0.16.0. Build CDS Hooks cards directly with the `Card` "
        "model — see cookbook/cds_discharge_summarizer_hf_trf.py"
    ),
    "TextPreProcessor": (
        "TextPreProcessor was removed in 0.16.0. Write a plain function that takes and "
        "returns a Document and add it with `pipeline.add_node(...)`."
    ),
    "TextPostProcessor": (
        "TextPostProcessor was removed in 0.16.0. Write a plain function that takes and "
        "returns a Document and add it with `pipeline.add_node(...)`."
    ),
}


def __getattr__(name: str):
    if name in _REMOVED_IN_0_16:
        raise ImportError(_REMOVED_IN_0_16[name])
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
