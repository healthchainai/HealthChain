# Quickstart

After [installing HealthChain](installation.md), get up to speed quickly with the core components before diving further into the [full documentation](reference/index.md)!
HealthChain's main building blocks:

- **Gateway:** Connect to multiple FHIR sources and healthcare systems with a single API.
- **FHIR helpers:** Create, validate, and code [FHIR](https://www.hl7.org/fhir/) resources with type safety and minimal boilerplate.
- **Agent tools:** Serve typed, validated FHIR tools to Claude over MCP, or to LangChain agents.
- **Sandbox:** Test your service against realistic EHR request flows — protocol-shaped requests in, validated responses out, no real EHR required.

Under the hood, **Pipelines** and the **Document** container compose processing steps around your own models — you'll meet them at the end of this page.


## Core Components 🧩

### Gateway 🔌

The [**HealthChainAPI**](./reference/gateway/api.md) provides a unified interface for connecting your AI application and models to multiple FHIR sources and healthcare systems with [OAuth2 authentication](https://oauth.net/2/).

[(Full Documentation on Gateway)](./reference/gateway/gateway.md)

<!--pytest.mark.skip-->
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

### FHIR Helpers 🔥

Use `healthchain.fhir` helpers to quickly create and manipulate FHIR resources (like `Condition`, `Observation`, etc.) in your code, ensuring they're standards-compliant with minimal boilerplate.

[(Full Documentation on FHIR Helpers)](./reference/utilities/fhir_helpers.md)

```python
from healthchain.fhir import create_condition

condition = create_condition(
    code="38341003",
    display="Hypertension",
    system="http://snomed.info/sct",
    subject="Patient/Foo",
    clinical_status="active"
)
```

Pair them with [validation](./reference/utilities/fhir_helpers.md#validation-loading) to catch broken data before it ships — `validate_resource` returns a structured report of everything wrong with a resource instead of throwing.

### Agent Tools 🤖

The [**FHIRToolkit**](./reference/utilities/tools.md) hands your agent typed, validated FHIR tools — build, validate, read, and code clinical data — from one toolkit.

[(Full Documentation on Agent Tools)](./reference/utilities/tools.md)

<!--pytest.mark.skip-->
```python
from healthchain.tools import FHIRToolkit

kit = FHIRToolkit(bundle="patient_bundle.json")

kit.as_mcp().run()          # serve to Claude or any MCP client (healthchain[mcp])
tools = kit.as_langchain()  # or drop into a LangChain agent (healthchain[langchain])
```

Or serve the tools straight from the terminal, no code:

<!--pytest.mark.skip-->
```bash
healthchain mcp --bundle patient_bundle.json
```

## Sandbox 🧪

Use [**SandboxClient**](./reference/utilities/sandbox.md) to test your app against real-world EHR scenarios like CDS Hooks or Clinical Documentation Improvement (CDI) workflows. It plays the role of the EHR — firing protocol-shaped requests at your service so you (or the agent that built the integration) can verify the responses before anything touches a real system. Load test datasets, send requests, and validate responses in a few lines of code.

[(Full Documentation on Sandbox)](./reference/utilities/sandbox.md)

### Workflows

A [**workflow**](./reference/utilities/sandbox.md#workflow-protocol-compatibility) represents a specific event in an EHR system that triggers your service (e.g., `patient-view` when opening a patient chart, `encounter-discharge` when discharging a patient).

Workflows determine the request structure, required FHIR resources, and validation rules. Different workflows are compatible with different protocols:

| Workflow Type                      | Protocol   | Example Workflows                                      |
|-------------------------------------|------------|--------------------------------------------------------|
| **CDS Hooks**                      | REST       | `patient-view`, `order-select`, `order-sign`, `encounter-discharge` |
| **Clinical Documentation**          | SOAP       | `sign-note-inpatient`, `sign-note-outpatient`          |


### Available Dataset Loaders

[**Dataset Loaders**](./reference/utilities/sandbox.md#dataset-registry) are shortcuts for loading common clinical test datasets from file. Currently available:

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

<!--pytest.mark.skip-->
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

## Pipelines 🛠️

HealthChain [**Pipelines**](./reference/pipeline/pipeline.md) are the supporting primitive behind protocol flows: lightweight composition of processing steps around your own models. Each step receives and returns a [**Document**](./reference/io/containers/containers.md), so raw text and FHIR resources flow through the same object.

You can build pipelines with two approaches:

### 1. Quick Inline Functions

Create a `Pipeline`, add processing functions with `@add_node`, and compile with `.build()`. Raw input (text, a FHIR Bundle, or a list of resources) is wrapped into a `Document` automatically, and each node returns FHIR-ready data end-to-end.

[(Full Documentation on Containers)](./reference/io/containers/containers.md)

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
            subject="Patient/example",
        )
        # problem_list is derived from the bundle per call; use the setter
        # (or add_resources) so the Condition persists.
        doc.fhir.problem_list = [condition]

    return doc

pipe = pipeline.build()

doc = Document("Patient has a history of diabetes.")
doc = pipe(doc)

print(doc.fhir.problem_list)  # FHIR Condition
```

### 2. Build With Components and Adapters

[**Components**](./reference/pipeline/components/components.md) are reusable, stateful classes that encapsulate specific processing logic for your pipeline, and you can easily implement your own.

Bring your own NLP: load a model with the library you already use — spaCy, HuggingFace Transformers, or a LangChain chain — and wrap it in a node with `add_node`.

[(Full Documentation on Components)](./reference/pipeline/components/components.md)

```python
from healthchain.pipeline import Pipeline
from healthchain.io import Document

pipeline = Pipeline()

@pipeline.add_node
def extract_problems(doc: Document) -> Document:
    """Run your own NLP model, then hand off entities to the problem list."""
    # Swap this for spaCy, HuggingFace, or any NER model of your choice
    entities = [{"text": "hypertension", "cui": "38341003"}]
    doc.update_problem_list(entities, patient_ref="Patient/example")
    return doc

pipe = pipeline.build()

doc = Document("Patient presents with hypertension.")
output = pipe(doc)

print(output.fhir.problem_list)  # FHIR Condition resources
```

Working with external or legacy data formats? [**Adapters**](./reference/io/adapters/adapters.md) interface them with your pipeline so you can parse, process, and format without worrying about low-level data conversion.

### 3. Copy a Cookbook Recipe

For complete, runnable examples of common clinical tasks — medical coding, discharge summarization, ML risk scoring — start from a [**cookbook recipe**](./cookbook/clinical_coding.md) and adapt it. Each recipe builds its pipeline from `Pipeline` + `add_node` directly, so every step is visible and easy to change.

## Going further ✨
Check out our [Cookbook](cookbook/index.md) section for more worked examples! HealthChain is still in its early stages, so if you have any questions please feel free to reach us on [Github](https://github.com/healthchainai/HealthChain/discussions) or [Discord](https://discord.gg/UQC6uAepUz).
