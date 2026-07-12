# Pipeline

HealthChain pipelines help you quickly build data processing workflows that integrate seamlessly with EHR systems. They support healthcare formats like [FHIR](https://build.fhir.org/) out of the box, so you can focus on your AI logic, not integration hassles.

Pipelines are lightweight composition primitives: create a `Pipeline`, add steps with `add_node`, and run your data through end-to-end. Load models with the library you already use (spaCy, HuggingFace Transformers, LangChain) and wrap them in nodes. For complete worked examples of common clinical tasks (medical coding, discharge summarization, ML risk scoring), start from a [cookbook recipe](../../cookbook/clinical_coding.md).

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
import spacy

nlp = spacy.load("en_core_sci_sm")

@pipeline.add_node
def extract_conditions(doc: Document) -> Document:
    """Extract medical entities, link them to SNOMED CT, and update the problem list."""
    spacy_doc = nlp(doc.text)  # your own spaCy pipeline

    # Map clinical terms to SNOMED CT
    snomed_mapping = {
        "hypertension": "38341003",
        "diabetes": "73211009",
        "pneumonia": "233604007",
    }

    entities = [
        {"text": ent.text, "cui": snomed_mapping[ent.text.lower()]}
        for ent in spacy_doc.ents
        if ent.text.lower() in snomed_mapping
    ]
    doc.update_problem_list(entities, patient_ref="Patient/456")

    return doc

# Equivalent to:
pipeline.add_node(extract_conditions)
```

#### Components

Components are reusable, stateful classes that encapsulate specific processing logic for your pipeline. Reach for a component instead of a plain function when a step needs to hold onto state across calls (a loaded model, a client connection).

See the [Components](./components/components.md) page for the base component protocol, and [Custom Components](#custom-components) below for a worked example.

#### Custom Components

Custom components implement the `BaseComponent` interface for reusable clinical processing logic.

```python
from healthchain.pipeline import BaseComponent

class ClinicalEntityLinker(BaseComponent):
    """Links extracted entities to a SNOMED CT terminology service."""

    def __init__(self, nlp, terminology_client):
        super().__init__()
        self.nlp = nlp
        self.terminology_client = terminology_client

    def __call__(self, doc: Document) -> Document:
        """Extract entities and convert them to FHIR Conditions."""
        spacy_doc = self.nlp(doc.text)

        entities = []
        for ent in spacy_doc.ents:
            code = self.terminology_client.lookup(ent.text)
            if code:
                entities.append({"text": ent.text, "cui": code})

        doc.update_problem_list(entities, patient_ref="Patient/456")

        return doc

# Add to pipeline
linker = ClinicalEntityLinker(nlp=nlp, terminology_client=my_terminology_client)
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
@pipeline.add_node(position="after", reference="extract_conditions", stage="post_processing")
def log_problem_list(doc: Document) -> Document:
    """Log the number of conditions found, for observability."""
    print(f"Extracted {len(doc.fhir.problem_list)} conditions")
    return doc
```

You can specify dependencies between components using the `dependencies` parameter. This is useful if you want to ensure that a component is run after another component.

```python
from healthchain.fhir import create_medication_statement

@pipeline.add_node(dependencies=["extract_conditions"])
def extract_medications(doc: Document) -> Document:
    """Extract medication entities and convert them to FHIR MedicationStatements."""
    spacy_doc = nlp(doc.text)

    for ent in spacy_doc.ents:
        if ent.label_ == "MEDICATION":
            # Create FHIR MedicationStatement
            med_statement = create_medication_statement(
                subject="Patient/456",
                code=ent._.cui if hasattr(ent._, "cui") else None,
                display=ent.text
            )
            doc.fhir.medication_list.append(med_statement)

    return doc
```

#### Removing

Use `.remove()` to remove a component from the pipeline.

```python
pipeline.remove("extract_conditions")
```

#### Replacing

Use `.replace()` to replace a component in the pipeline.

```python
def enhanced_entity_linking(doc: Document) -> Document:
    """Enhanced entity linking with an external terminology service."""
    spacy_doc = nlp(doc.text)

    entities = []
    for ent in spacy_doc.ents:
        # Call external terminology service for validation
        validated_code = terminology_service.validate(ent.text)
        if validated_code:
            entities.append({"text": ent.text, "cui": validated_code})

    doc.update_problem_list(entities, patient_ref="Patient/456")

    return doc

# Replace basic extraction with the enhanced version
pipeline.replace("extract_conditions", enhanced_entity_linking)
```

#### Inspecting the Pipeline

```python
print(pipeline)
print(pipeline.stages)

# ["extract_conditions", "ClinicalEntityLinker", "log_problem_list", "extract_medications"]
# Pipeline Stages:
#   post_processing:
#     - log_problem_list
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
