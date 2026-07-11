from .base import BasePipeline, Pipeline
from .components import (
    BaseComponent,
    Component,
    FHIRProblemListExtractor,
)

__all__ = [
    "BasePipeline",
    "Pipeline",
    "BaseComponent",
    "Component",
    "FHIRProblemListExtractor",
]


# Tombstones for names removed in 0.16.0. The prebuilt pipelines and model-routing layer
# were removed in favour of composing steps directly with `Pipeline` + `add_node`. Raising a
# guiding ImportError (rather than a bare AttributeError) points anyone — or any code assistant
# working from the 0.15 API — at the current pattern and cookbook.
_REMOVED_IN_0_16 = {
    "MedicalCodingPipeline": (
        "MedicalCodingPipeline was removed in 0.16.0. Build the medical coding pipeline "
        "directly with `Pipeline` + `add_node` — see cookbook/notereader_clinical_coding_fhir.py"
    ),
    "SummarizationPipeline": (
        "SummarizationPipeline was removed in 0.16.0. Build the summarization pipeline "
        "directly with `Pipeline` + `add_node` — see cookbook/cds_discharge_summarizer_hf_trf.py"
    ),
    "ModelRoutingMixin": (
        "ModelRoutingMixin was removed in 0.16.0. Load models directly (spacy.load / "
        "transformers.pipeline / your LangChain chain) and add them with `pipeline.add_node(...)`."
    ),
    "ModelRouter": (
        "ModelRouter was removed in 0.16.0. Load models directly (spacy.load / "
        "transformers.pipeline / your LangChain chain) and add them with `pipeline.add_node(...)`."
    ),
    "ModelConfig": (
        "ModelConfig was removed in 0.16.0 along with the model-routing layer. Load models "
        "directly and add them with `pipeline.add_node(...)`."
    ),
    "ModelSource": (
        "ModelSource was removed in 0.16.0 along with the model-routing layer. Load models "
        "directly and add them with `pipeline.add_node(...)`."
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
