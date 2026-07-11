# Pipeline

HealthChain pipelines help you quickly build data processing workflows that integrate seamlessly with EHR systems. They support healthcare formats like [FHIR](https://build.fhir.org/) out of the box, so you can focus on your AI logic, not integration hassles.

Pipelines are lightweight composition primitives: create a `Pipeline`, add steps with `add_node`, and run your data through end-to-end. HealthChain doesn't ship prebuilt pipeline classes or NLP wrappers — load models with the library you already use (spaCy, HuggingFace Transformers, LangChain) and wrap them in nodes. For complete worked examples of common clinical tasks (medical coding, discharge summarization, ML risk scoring), start from a [cookbook recipe](../../cookbook/clinical_coding.md).

## Building a Pipeline 🕺

[**Containers**](../io/containers/containers.md) are at the core of HealthChain pipelines: a [Document](../io/containers/document.md) carries your data and accumulates results as it flows through each step, just like spaCy's `Doc`.

Create a `Pipeline`; each node processes and returns a `Document`, enabling smooth, modular workflows and direct FHIR conversion. Raw input (text, a FHIR Bundle, or a list of resources) is wrapped into a `Document` automatically.

```python
from healthchain.pipeline import Pipeline
from healthchain.io.containers import Document

pipeline = Pipeline()
```

To use a built pipeline, compile it by running `.build()`. This will return a compiled pipeline that you can run on your data.

```python
# Compile the pipeline to create a callable object
pipe = pipeline.build()

# Create a Document with your clinical text and run it through the pipeline
doc = pipe(Document("Patient is diagnosed with diabetes"))

# Print the extracted problem list items
print(doc.fhir.problem_list)
```

### Adding Nodes

There are three types of nodes you can add to your pipeline with the method `.add_node()`:

- Inline Functions
- Components
- Custom Components

#### Inline Functions

Inline functions are simple functions that process Document containers. Use them for custom clinical logic without creating full components.

```python
from spacy.tokens import Span

@pipeline.add_node
def link_snomed_codes(doc: Document) -> Document:
    """Map medical entities to SNOMED CT codes."""
    if not Span.has_extension("cui"):
        Span.set_extension("cui", default=None)

    spacy_doc = doc.nlp.get_spacy_doc()

    # Map clinical terms to SNOMED CT
    snomed_mapping = {
        "hypertension": "38341003",
        "diabetes": "73211009",
        "pneumonia": "233604007",
    }

    for ent in spacy_doc.ents:
        if ent.text.lower() in snomed_mapping:
            ent._.cui = snomed_mapping[ent.text.lower()]

    return doc

# Equivalent to:
pipeline.add_node(link_snomed_codes)
```

#### Components

Components are reusable building blocks for common clinical processing tasks. HealthChain ships a pure-Python `FHIRProblemListExtractor`; for NLP, bring your own model and wrap it in a node.

See the full list at the [Components](./components/components.md) page.

```python
import spacy
from healthchain.pipeline.components import FHIRProblemListExtractor

# Bring your own NLP: load a spaCy model and wrap it in a node
nlp = spacy.load("en_core_sci_sm")

@pipeline.add_node
def run_nlp(doc: Document) -> Document:
    doc.nlp.add_spacy_doc(nlp(doc.text))
    return doc

# Extract FHIR Condition resources from entities
extractor = FHIRProblemListExtractor(patient_ref="Patient/456")
pipeline.add_node(extractor)
```

#### Custom Components

Custom components implement the `BaseComponent` interface for reusable clinical processing logic.

```python
from healthchain.pipeline import BaseComponent
from healthchain.fhir import create_condition

class ClinicalEntityLinker(BaseComponent):
    """Links extracted entities to standard medical terminologies."""

    def __init__(self, terminology_service_url: str):
        super().__init__()
        self.terminology_url = terminology_service_url

    def __call__(self, doc: Document) -> Document:
        """Convert medical entities to FHIR Conditions."""
        spacy_doc = doc.nlp.get_spacy_doc()

        for ent in spacy_doc.ents:
            if ent._.cui:  # Has SNOMED CT code
                condition = create_condition(
                    subject=f"Patient/{doc.patient_id}",
                    code=ent._.cui,
                    display=ent.text
                )
                doc.fhir.problem_list.append(condition)

        return doc

# Add to pipeline
linker = ClinicalEntityLinker(terminology_service_url="https://terminology.hl7.org/")
pipeline.add_node(linker)
```

[(BaseComponent API Reference)](../../api/component.md#healthchain.pipeline.components.base.BaseComponent)


## Pipeline Management 🔨

#### Adding

Use `.add_node()` to add a component to the pipeline. By default, the component will be added to the end of the pipeline and named as the function name provided.

You can specify the position of the component using the `position` parameter. Available positions are:

- `"first"`
- `"last"`
- `"default"`
- `"after"`
- `"before"`

When using `"after"` or `"before"`, you must also specify the `reference` parameter with the name of the node you want to add the component after or before.

You can also specify the `stage` parameter to add the component to a specific stage group of the pipeline.

```python
@pipeline.add_node(position="after", reference="run_nlp", stage="entity_linking")
def link_snomed_codes(doc: Document) -> Document:
    """Add SNOMED CT codes to extracted medical entities."""
    spacy_doc = doc.nlp.get_spacy_doc()
    snomed_mapping = {
        "hypertension": "38341003",
        "diabetes": "73211009",
    }
    for ent in spacy_doc.ents:
        if ent.text.lower() in snomed_mapping:
            ent._.cui = snomed_mapping[ent.text.lower()]
    return doc
```

You can specify dependencies between components using the `dependencies` parameter. This is useful if you want to ensure that a component is run after another component.

```python
@pipeline.add_node(dependencies=["run_nlp"])
def extract_medications(doc: Document) -> Document:
    """Extract medication entities and convert to FHIR MedicationStatements."""
    spacy_doc = doc.nlp.get_spacy_doc()

    for ent in spacy_doc.ents:
        if ent.label_ == "MEDICATION":
            # Create FHIR MedicationStatement
            med_statement = create_medication_statement(
                subject=f"Patient/{doc.patient_id}",
                code=ent._.cui if hasattr(ent._, "cui") else None,
                display=ent.text
            )
            doc.fhir.medication_list.append(med_statement)

    return doc
```

#### Removing

Use `.remove()` to remove a component from the pipeline.

```python
pipeline.remove("link_snomed_codes")
```

#### Replacing

Use `.replace()` to replace a component in the pipeline.

```python
def enhanced_entity_linking(doc: Document) -> Document:
    """Enhanced entity linking with external terminology service."""
    spacy_doc = doc.nlp.get_spacy_doc()

    for ent in spacy_doc.ents:
        # Call external terminology service for validation
        validated_code = terminology_service.validate(ent.text)
        if validated_code:
            ent._.cui = validated_code

    return doc

# Replace basic linking with enhanced version
pipeline.replace("link_snomed_codes", enhanced_entity_linking)
```

#### Inspecting the Pipeline

```python
print(pipeline)
print(pipeline.stages)

# ["run_nlp", "ClinicalEntityLinker", "FHIRProblemListExtractor"]
# preprocessing:
#   - run_nlp
# entity_linking:
#   - ClinicalEntityLinker
# fhir_conversion:
#   - FHIRProblemListExtractor
```
## Working with Healthcare Data Formats 🔄

Adapters let you easily convert between healthcare formats (CDA, FHIR, CDS Hooks) and HealthChain Documents. Keep your ML pipeline format-agnostic while always getting FHIR-ready outputs.

[(Full Documentation on Adapters)](../io/adapters/adapters.md)

```python
from healthchain.io import CdaAdapter, Document

adapter = CdaAdapter()

# Parse healthcare data into Document
doc = adapter.parse(cda_request)

# Process with pure pipeline
processed_doc = pipeline(doc)

# Convert back to healthcare format
response = adapter.format(processed_doc)
```
