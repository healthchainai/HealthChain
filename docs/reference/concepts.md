# Core Concepts

HealthChain's main building blocks:

- **Gateway:** Connect to multiple FHIR sources and healthcare systems with a single API.
- **FHIR helpers:** Create, validate, and code [FHIR](https://www.hl7.org/fhir/) resources with type safety and minimal boilerplate.
- **Agent tools:** Serve typed, validated FHIR tools to Claude over MCP, or to LangChain agents.
- **Sandbox:** Test your service against realistic EHR request flows — protocol-shaped requests in, validated responses out, no real EHR required.

Under the hood, **Pipelines** and the **Document** container compose processing steps around your own models inside protocol flows, and the optional **InteropEngine** (`pip install "healthchain[cda]"`) converts between FHIR and [HL7 CDA](https://www.hl7.org/implement/standards/product_brief.cfm?product_id=7) for legacy system bridging.


## Gateway

The [**HealthChainAPI**](./gateway/api.md) provides a unified interface for connecting your AI application and models to multiple healthcare systems through a single API. It automatically handles [FHIR API](https://www.hl7.org/fhir/http.html), [CDS Hooks](https://cds-hooks.org/), and [SOAP/CDA protocols](https://www.hl7.org/implement/standards/product_brief.cfm?product_id=7) with [OAuth2 authentication](https://oauth.net/2/).

[(Full Documentation on Gateway)](./gateway/gateway.md)

```python
from healthchain.gateway import HealthChainAPI, FHIRGateway
from healthchain.fhir.r4b import Patient

# Create your healthcare application
app = HealthChainAPI(title="My Healthcare AI App")

# Connect to multiple FHIR servers
fhir = FHIRGateway()
fhir.add_source("epic", "fhir://fhir.epic.com/r4?client_id=...")
fhir.add_source("medplum", "fhir://api.medplum.com/fhir/R4/?client_id=...")

# Add AI transformations to FHIR data
@fhir.transform(Patient)
def enhance_patient(id: str, source: str = None) -> Patient:
    patient = fhir.read(Patient, id, source)
    # Your AI logic here
    patient.active = True
    fhir.update(patient, source)
    return patient

# Register and run
app.register_gateway(fhir)

# Available at: GET /fhir/transform/Patient/123?source=epic
```

## FHIR & Validation

Use [**FHIR helpers**](./utilities/fhir_helpers.md) to create, read, and validate FHIR resources with minimal boilerplate — the strict schema is what lets you catch broken data before it reaches a live system. On top of the underlying Pydantic models the helpers add three things: **flat constructors** (scalars in, correctly nested resources out, the right terminology systems in the right places), **no invented facts** (no auto-timestamps or guessed statuses — output never silently gains clinical claims), and **semantic validation** (required-binding checks that catch spec-invalid codes plain type validation lets through).

[(Full Documentation on FHIR Helpers)](./utilities/fhir_helpers.md)

```python
from healthchain.fhir import create_condition, validate_resource

condition = create_condition(
    code="38341003",
    display="Hypertension",
    system="http://snomed.info/sct",
    subject="Patient/Foo",
    clinical_status="active",
)

# Validation as data: a report you can act on, never an exception
report = validate_resource(condition)
print(report.valid, [issue.diagnostics for issue in report.issues])
```

The [**Terminology**](./utilities/terminology.md) seam adds code lookup (`lookup_code("metoprolol")`) with a bundled demo catalog that swaps for your terminology server in production.

## Agent Tools

[**FHIRToolkit**](./utilities/tools.md) packages the build/validate/read/lookup surface as typed agent tools — flat schemas a model can fill reliably, with errors returned as values an agent loop can read and correct.

[(Full Documentation on Agent Tools)](./utilities/tools.md)

```python
from healthchain.tools import FHIRToolkit

kit = FHIRToolkit(bundle="patient_bundle.json")

kit.as_mcp().run()          # serve to Claude or any MCP client
tools = kit.as_langchain()  # or drop into a LangChain agent
```

## Sandbox

The [**SandboxClient**](./utilities/sandbox.md) plays the role of the EHR: it fires realistic, protocol-shaped requests (CDS Hooks, SOAP/CDA) at your service and lets you inspect what comes back — a closed verify loop that needs no real EHR, whether you wrote the integration yourself or an agent built it for you. Load test datasets, send requests, and validate responses in a few lines of code.

[(Full Documentation on Sandbox)](./utilities/sandbox.md)

### Workflows

A [**workflow**](./utilities/sandbox.md#workflow-protocol-compatibility) represents a specific event in an EHR system that triggers your service (e.g., `patient-view` when opening a patient chart, `encounter-discharge` when discharging a patient).

Workflows determine the request structure, required FHIR resources, and validation rules. Different workflows are compatible with different protocols:

| Workflow Type                      | Protocol   | Example Workflows                                      |
|-------------------------------------|------------|--------------------------------------------------------|
| **CDS Hooks**                      | REST       | `patient-view`, `order-select`, `order-sign`, `encounter-discharge` |
| **Clinical Documentation**          | SOAP       | `sign-note-inpatient`, `sign-note-outpatient`          |


### Available Dataset Loaders

[**Dataset Loaders**](./utilities/sandbox.md#dataset-registry) are shortcuts for loading common clinical test datasets from file. Currently available:

| Dataset Key        | Description                                 | FHIR Version | Source                                                                                  | Download Link                                                                                  |
|--------------------|---------------------------------------------|--------------|-----------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------|
| `mimic-on-fhir`    | **MIMIC-IV on FHIR Demo Dataset**        | R4           | [PhysioNet Project](https://physionet.org/content/mimic-iv-fhir-demo/2.1.0/)                  | [Download ZIP](https://physionet.org/content/mimic-iv-fhir-demo/get-zip/2.1.0/) (49.5 MB)      |
| `synthea-patient`  | **Synthea FHIR Patient Records**    | R4           | [Synthea Downloads](https://synthea.mitre.org/downloads)                                  | [Download ZIP](https://arc.net/l/quote/hoquexhy) (100 Sample, 36 MB)                           |


```python
from healthchain.sandbox import list_available_datasets

# See all registered datasets with descriptions
datasets = list_available_datasets()
print(datasets)
```

### Basic Usage

```python
from healthchain.sandbox import SandboxClient

# Initialize client with your service URL and workflow
client = SandboxClient(
    url="http://localhost:8000/cds/encounter-discharge",
    workflow="encounter-discharge"
)

# Load test data from a registered dataset
client.load_from_registry(
    "synthea-patient",
    data_dir="./data/synthea",
    resource_types=["Condition", "DocumentReference"],
    sample_size=3
)

# Optionally inspect before sending
client.preview_requests()  # See what will be sent
client.get_status()        # Check client state

# Send requests to your service
responses = client.send_requests()
```

For clinical documentation workflows using SOAP/CDA:

```python
# Use context manager for automatic result saving
with SandboxClient(
    url="http://localhost:8000/notereader/ProcessDocument",
    workflow="sign-note-inpatient",
    protocol="soap"
) as client:
    client.load_from_path("./cookbook/data/notereader_cda.xml")
    responses = client.send_requests()
    # Results automatically saved to ./output/ on success
```

## Pipeline & I/O

[**Pipelines**](./pipeline/pipeline.md) are the supporting primitive behind protocol flows: they compose processing steps around your own models, and gateway handlers (CDS Hooks, NoteReader) pass each request through them as a [**Document**](./io/containers/containers.md).

You can build pipelines with three different approaches:

### 1. Quick Inline Functions

For quick experiments, create a `Pipeline` and add your processing functions. Each step receives and returns a **Document**; raw input (text, a FHIR Bundle, or a list of resources) is wrapped into a `Document` automatically.

Containers make your pipeline FHIR-native by loading and transforming your data (free text, EHR resources, etc.) into structured FHIR-ready formats. Just add your processing functions with `@add_node`, compile with `.build()`, and your pipeline is ready to process FHIR data end-to-end.

[(Full Documentation on Containers)](./io/containers/containers.md)

```python
from healthchain.pipeline import Pipeline
from healthchain.io import Document
from healthchain.fhir import create_condition

pipeline = Pipeline()

@pipeline.add_node
def extract_diabetes(doc: Document) -> Document:
    """Adds a FHIR Condition for diabetes if mentioned in the text."""
    if "diabetes" in doc.text.lower():
        condition = create_condition(
            code="73211009",
            display="Diabetes mellitus",
        )
        doc.fhir.problem_list.append(condition)

    return doc

pipe = pipeline.build()

doc = Document("Patient has a history of diabetes.")
doc = pipe(doc)

print(doc.fhir.problem_list)  # FHIR Condition
```

### 2. Build With Components and Adapters

[**Components**](./pipeline/components/components.md) are reusable, stateful classes that encapsulate specific processing logic for your pipeline, and you can easily implement your own.

Bring your own NLP: load a model with the library you already use — spaCy, HuggingFace Transformers, or a LangChain chain — and wrap it in a node with `add_node`.

[(Full Documentation on Components)](./pipeline/components/components.md)

```python
import spacy
from healthchain.pipeline import Pipeline
from healthchain.io import Document

pipeline = Pipeline()

nlp = spacy.load("en_core_sci_sm")

@pipeline.add_node
def extract_problems(doc: Document) -> Document:
    spacy_doc = nlp(doc.text)
    doc.update_problem_list(
        [{"text": ent.text, "cui": ent._.cui} for ent in spacy_doc.ents],
        patient_ref="Patient/example",
    )
    return doc

pipe = pipeline.build()

doc = Document("Patient presents with hypertension.")
output = pipe(doc)
```

You can process legacy healthcare data formats too. [**Adapters**](./io/adapters/adapters.md) convert between healthcare formats like [CDA](https://www.hl7.org/implement/standards/product_brief.cfm?product_id=7) and your pipeline — just parse, process, and format without worrying about low-level data conversion.

[(Full Documentation on Adapters)](./io/adapters/adapters.md)

```python
from healthchain.io import CdaAdapter
from healthchain.models import CdaRequest

# Use adapter for format conversion
adapter = CdaAdapter()
cda_request = CdaRequest(document="<CDA XML content>")

# Parse, process, format
doc = adapter.parse(cda_request)
processed_doc = pipe(doc)
output = adapter.format(processed_doc)
```

### 3. Copy a Cookbook Recipe

For complete, runnable examples of common clinical tasks — medical coding, discharge summarization, ML risk scoring — start from a [**cookbook recipe**](../cookbook/clinical_coding.md) and adapt it. Each recipe builds its pipeline from `Pipeline` + `add_node` directly, so every step is visible and easy to change.

[(Full Documentation on Pipelines)](./pipeline/pipeline.md)

## Interoperability (CDA)

The optional Interoperability module converts between FHIR and CDA for legacy system bridging. It requires the `cda` extra: `pip install "healthchain[cda]"`.

[(Full Documentation on Interoperability Engine)](./interop/interop.md)

```python
from healthchain.interop import create_interop, FormatType

# Uses bundled configs - basic CDA ↔ FHIR conversion
engine = create_interop()

# Load a CDA document
with open("tests/data/test_cda.xml", "r") as f:
    cda_xml = f.read()

# Convert CDA XML to FHIR resources
fhir_resources = engine.to_fhir(cda_xml, src_format=FormatType.CDA)

# Convert FHIR resources back to CDA
cda_document = engine.from_fhir(fhir_resources, dest_format=FormatType.CDA)
```
