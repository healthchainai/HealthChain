# Document 📄

The `Document` class is a container for working with both clinical text and structured healthcare data. It natively manages FHIR resources, tracks clinical document relationships, and stores decision support outputs.

Use Document containers for clinical notes, discharge summaries, patient records, and any healthcare data that combines text with structured FHIR resources.

## Usage

The main things you'll do with `Document`:

- Store and update clinical notes and FHIR Bundles
- Extract and manipulate diagnoses, meds, allergies, and documents
- Generate & store CDS Hooks cards (recommendations, alerts)


## API Overview

**Document** is built around three attributes:

| Attribute | For |
|---|---|
| `doc.text` | The input clinical text |
| `doc.fhir` | FHIR management—Clinical lists, Bundles, DocReference, patient info |
| `doc.cds`  | Decision support—recommendation cards, actions |

Bring your own NLP or ML library — spaCy, HuggingFace Transformers, LangChain — run it inside a pipeline node, and hand off the results explicitly with `doc.update_problem_list(...)` or by writing straight to `doc.fhir`.


### FHIR Data (`doc.fhir`)

- Automatic FHIR Bundle creation and management
- Resource type validation
- Easy access to clinical data lists (e.g., problems, medications, allergies)
- OperationOutcome and Provenance resources automatically extracted and accessible as `doc.fhir.operation_outcomes` and `doc.fhir.provenances` (removed from main bundle)

**Convenience Accessors**

| Attribute         | Description                                              |
|-------------------|---------------------------------------------------------|
| `patient`         | First Patient resource in the bundle (or `None`)         |
| `patients`        | List of Patient resources                                |
| `problem_list`    | List of Condition resources (diagnoses, problems)        |
| `medication_list` | List of MedicationStatement resources                    |
| `allergy_list`    | List of AllergyIntolerance resources                     |

**Document Reference Management**

- Document relationship tracking (parent/child/sibling)
- Attachment handling with base64 encoding
- Document family retrieval

**CDS Support**

- Support for CDS Hooks prefetch resources
- Resource indexing by type


```python
from healthchain.io import Document
from healthchain.fhir import (
    create_condition,
    create_document_reference,
)

# Initialize with clinical text from EHR
doc = Document("Patient presents with uncontrolled hypertension and Type 2 diabetes")

# Build problem list with SNOMED CT codes
doc.fhir.problem_list = [
    create_condition(
        subject="Patient/123",
        code="38341003",
        display="Hypertension"
    ),
    create_condition(
        subject="Patient/123",
        code="44054006",
        display="Type 2 diabetes mellitus"
    )
]

# Track document versions and amendments
initial_note = create_document_reference(
    data="Initial assessment: Patient presents with chest pain",
    content_type="text/plain",
    description="Initial ED note"
)
initial_id = doc.fhir.add_document_reference(initial_note)

# Add amended note
amended_note = create_document_reference(
    data="Amended: Patient presents with chest pain, ruling out cardiac etiology",
    content_type="text/plain",
    description="Amended ED note"
)
amended_id = doc.fhir.add_document_reference(
    amended_note,
    parent_id=initial_id,
    relationship_type="replaces"
)

# Retrieve document history for audit trail
family = doc.fhir.get_document_reference_family(amended_id)
print(f"Original note: {family['parents'][0].description}")


# Handle errors and track data provenance
if doc.fhir.operation_outcomes:
    for outcome in doc.fhir.operation_outcomes:
        print(f"Warning: {outcome.issue[0].diagnostics}")

# Access patient demographics
if doc.fhir.patient:
    print(f"Patient: {doc.fhir.patient.name[0].given[0]} {doc.fhir.patient.name[0].family}")

# Prepare data for CDS Hooks integration
prefetch = {
    "Condition": doc.fhir.problem_list,
    "MedicationStatement": doc.fhir.medication_list,
}
doc.fhir.prefetch_resources = prefetch

# CDS service can query prefetch data
conditions = doc.fhir.get_prefetch_resources("Condition")
print(f"Active conditions: {len(conditions)}")
```

### Problem List from NLP (`doc.update_problem_list`)

Run your own NLP library directly inside a plain pipeline node, then hand the linked entities off explicitly with `update_problem_list(entities, patient_ref, coding_system="http://snomed.info/sct", code_attribute="cui")`. Each entity is a dict with at least `"text"` and a medical code under `code_attribute`; entities missing the code are skipped, and existing problem list Conditions are preserved.

```python
def extract_problems(doc: Document) -> Document:
    spacy_doc = nlp(doc.text)  # your own spaCy pipeline
    doc.update_problem_list(
        [{"text": ent.text, "cui": ent._.cui} for ent in spacy_doc.ents],
        patient_ref="Patient/123",
    )
    return doc

pipeline.add_node(extract_problems)
```

### Clinical Decision Support (`doc.cds`)

- `cards`: Clinical recommendation cards displayed in EHR workflows
- `actions`: Suggested interventions (orders, referrals, documentation)

```python
from healthchain.models import Card, Action

# Generate clinical alert
doc.cds.cards = [
    Card(
        summary="Drug interaction detected",
        indicator="critical",
        detail="Warfarin + NSAIDs: Increased bleeding risk",
        source={"label": "Clinical Decision Support"},
    )
]

# Suggest action
doc.cds.actions = [
    Action(
        type="create",
        description="Order CBC to monitor platelets",
        resource={
            "resourceType": "ServiceRequest",
            "code": {"text": "Complete Blood Count"}
        }
    )
]
```


### Properties and Methods

```python
# FHIR access
print(doc.fhir.problem_list)
print(doc.fhir.patient)

# Clinical decision support
cards = doc.cds.cards
```

## Resource Docs

- [FHIR Bundle](https://www.hl7.org/fhir/bundle.html)
- [FHIR Condition](https://www.hl7.org/fhir/condition.html)
- [FHIR DocumentReference](https://www.hl7.org/fhir/documentreference.html)

## API Reference

See [Document API Reference](../../../api/containers.md#healthchain.io.containers.document) for full details.
