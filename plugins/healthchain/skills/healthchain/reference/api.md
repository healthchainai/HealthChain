# HealthChain 0.16 API reference

Symbols verified against healthchain 0.16.0. Fuller docs: https://healthchainai.github.io/HealthChain/llms.txt

## 1. Gateway — `healthchain.gateway`

`HealthChainAPI` is a FastAPI app. `FHIRGateway` connects to one or many FHIR sources and registers onto it.

```python
from healthchain.gateway import HealthChainAPI, FHIRGateway
from healthchain.fhir.r4b import Patient

app = HealthChainAPI(title="Multi-EHR Patient Data")
fhir = FHIRGateway()
fhir.add_source("epic", "fhir://fhir.epic.com/r4?client_id=epic_client_id")

@fhir.aggregate(Patient)
def enrich_patient_data(id: str, source: str) -> Patient:
    return fhir.search(Patient, {"_id": id}, source, add_provenance=True)

app.register_gateway(fhir)
```

**`FHIRGateway` is not a context manager.** It defines no `__enter__` / `__exit__` (verified with `hasattr`) — do not write `with FHIRGateway(...) as gateway:`. Construct it, call `add_source`, and let it live for the app's lifetime; `HealthChainAPI`/`register_gateway` own its lifecycle.

Real signatures (verified with `inspect.signature`):

- `FHIRGateway.__init__(self, **kwargs)` — keyword args only, nothing positional required.
- `add_source(self, name: str, connection_string: str) -> None` — `connection_string` is `fhir://host/path?client_id=...&client_secret=...&token_url=...&scope=...`. Build it by hand, or from `FHIRAuthConfig` (below).
- `search(self, resource_type, params=None, source=None, add_provenance=False, provenance_tag=None, follow_pagination=False, max_pages=None) -> Bundle`

Real credentials belong in environment variables via `FHIRAuthConfig`, not typed into the connection string:

<!-- pytest.mark.skip -->
```python
from healthchain.gateway.clients import FHIRAuthConfig

# Reads EPIC_BASE_URL, EPIC_CLIENT_ID, EPIC_CLIENT_SECRET (or EPIC_CLIENT_SECRET_PATH),
# EPIC_TOKEN_URL, and optional EPIC_SCOPE / EPIC_AUDIENCE / EPIC_TIMEOUT / EPIC_VERIFY_SSL /
# EPIC_USE_JWT_ASSERTION / EPIC_KEY_ID.
auth = FHIRAuthConfig.from_env("EPIC")
fhir.add_source("epic", auth.to_connection_string())
```

`FHIRAuthConfig` is imported from `healthchain.gateway.clients`, not `healthchain.gateway` itself. `from_env(env_prefix: str) -> FHIRAuthConfig` and `to_connection_string(self) -> str` are the two methods that matter; the class is a Pydantic model so `FHIRAuthConfig(base_url=..., client_id=..., ...)` also works directly. Skipped above only because it needs real `EPIC_*` environment variables to construct without a validation error — the pattern itself needs no other explanation.

Also available: `AsyncFHIRGateway` and `AsyncFHIRClient` for modern systems (prefer sync — legacy EHR compatibility), `FHIRClient`, `CDSHooksService`, `NoteReaderService` (CDA/SOAP, needs `healthchain[cda]`), `EHREvent`, `EHREventType`, `EventDispatcher`, `ClientPool`.

Source URLs are `fhir://host/version?client_id=...`; secrets come from environment variables, never the URL string in code.

## 2. FHIR & Validation — `healthchain.fhir`

### Create

```python
from healthchain.fhir import create_condition, create_patient

condition = create_condition(
    subject="Patient/123",
    code="38341003",
    display="Hypertension",
    system="http://snomed.info/sct",
)
```

`create_condition(subject, clinical_status="active", code=None, display=None, system="http://snomed.info/sct", onset=None, *, generate_id=True, warn=True)`

Keyword-only escape hatches on the resource-level `create_*` helpers: `generate_id=False` for deterministic output, `warn=False` to silence binding warnings. The element helpers accept neither. Most raise `TypeError` if you pass them, but `create_document_reference_content` takes `**kwargs` and silently copies whatever it gets into the dict it returns — passing `generate_id` there yields a content dict with a stray `"generate_id"` key rather than an error.

Others: `create_patient`, `create_medication_statement` (status defaults to `"unknown"`), `create_allergy_intolerance`, `create_value_quantity_observation`, `create_document_reference`, `create_risk_assessment_from_prediction`, `set_condition_category`, `add_provenance_metadata`, `add_coding_to_codeable_concept`.

Element helpers: `create_single_codeable_concept`, `create_single_reaction`, `create_single_attachment`, `create_dosage`, `create_document_reference_content`.

### Validate

```python
from healthchain.fhir import validate_resource

report = validate_resource({"resourceType": "Condition"})
print(report.valid)
```

`validate_resource(resource, resource_type=None, version=None) -> ValidationReport`. **Never raises.** `report.valid` is False when any error or fatal issue exists; `report.issues` holds `ValidationIssue` entries. Checks structure (types, required fields, unknown fields) and required bindings on primitive code fields. Does **not** check profiles or invariants — that's a server's `$validate`.

`load_bundle(source)` takes a path, JSON string, or dict and returns a validated `Bundle`. `FHIRValidationError` is raised only by `load_bundle`, not by `validate_resource`.

### Read

```python
from healthchain.fhir import load_bundle, get_resources, get_coded_entries, resolve_reference
```

- `get_resources(bundle, resource_type)` / `set_resources` / `add_resource` / `create_bundle` / `get_resource_type`
- `get_coded_entries(bundle, resource_type, status=None)` → `CodedEntry` objects with `.code`, `.display`, `.system`, `.status`, `.authored_on` (renamed from `.date` in 0.16), and `.codings` keeping every coding including text-only concepts
- `get_medications(bundle)` — the medication-shaped convenience over the same reader
- `resolve_reference(bundle, reference)` — follows a `Reference` within a bundle
- `create_resource_from_dict`, `convert_prefetch_to_fhir_objects`, `prefetch_to_bundle`, `read_content_attachment`

### Versions

`healthchain.fhir.r4b` holds the R4B resource classes. `fhir_version_context`, `convert_resource`, `get_fhir_resource`, `get_default_version`, `get_resource_version` handle multi-version work.

## 3. Agent Tools — `healthchain.tools`

```python
from healthchain.tools import FHIRToolkit

kit = FHIRToolkit()
assert [t.name for t in kit.get_tools()] == [
    "build_resource",
    "validate_resource",
    "load_bundle",
    "get_resources",
    "get_coded_entries",
    "resolve_reference",
    "lookup_code",
    "list_codes",
]
```

`FHIRToolkit(bundle=None, lookup=None)`. `bundle` accepts a `Bundle`, dict, JSON string, or file path and is validated once on assignment. `lookup` is any `TerminologyLookup`; it defaults to `LocalCodeLookup`'s demo catalog.

`list_codes` is registered only when the lookup is enumerable (has `entries()`); the other seven are always present. The assertion above is the contract — if the toolkit gains or loses a tool, CI fails here rather than letting the skill teach a stale list.

Views:
- `kit.as_mcp(name="healthchain")` → a FastMCP server; `.run()` serves over stdio. Needs `healthchain[mcp]`.
- `kit.as_langchain()` → a list of `StructuredTool`. Needs `healthchain[langchain]`.
- `kit.get_tools()` → `Tool` objects; `t.spec` is a plain dict for a hand-rolled loop.
- `kit.run_tool(name, arguments)` → call one directly.

Zero-code path: `healthchain mcp --bundle patient_bundle.json`.

## 4. Sandbox — `healthchain.sandbox` (needs `healthchain[sandbox]`)

`SandboxClient` fires protocol-shaped test requests at a running service — CDS Hooks or SOAP/CDA — so the service can be proven end to end with no real EHR. `DatasetLoader` and `DatasetRegistry` load common test datasets (MIMIC-IV on FHIR, Synthea). CLI equivalents: `healthchain sandbox run --url <url>`, `healthchain seed medplum <path>`.

## Terminology — `healthchain.terminology`

```python
from healthchain.terminology import LocalCodeLookup

lookup = LocalCodeLookup()
hits = lookup.search("metoprolol")
assert hits[0].code == "866427"
assert hits[0].system == "http://www.nlm.nih.gov/research/umls/rxnorm"
assert len(lookup.entries()) == 25
```

`TerminologyLookup` is a Protocol with `search(text, system=None) -> List[Coding]`. `LocalCodeLookup` ships a small demo catalog (RxNorm, LOINC) and adds `entries()`, `__iter__`, `__len__`. It deliberately excludes SNOMED — licensing. For real entity linking, plug a UMLS linker in behind the same protocol.

The catalog size is asserted rather than stated in prose so the gate catches it growing. If CI fails on that line, update the number — don't delete the assertion.

The point of the seam: an LLM uses codes a lookup returned, never codes it invented.

## Under the hood — `Pipeline` and `Document`

```python
from healthchain.pipeline import Pipeline

pipeline = Pipeline()

@pipeline.add_node
def annotate(doc):
    return doc
```

`Pipeline()` — not `Pipeline[Document]()`. Raw input auto-wraps to `Document`. `Document` carries text, FHIR resources, and CDS annotations; `document.update_problem_list(entities, patient_ref)` writes extracted entities into the FHIR side. Models load with their own libraries inside `add_node`.

## Removed in 0.16 — do not use

| Reached for | Use instead |
|---|---|
| `SpacyNLP`, `HFTransformer`, `LangChainLLM` | Load the model with its own library inside `Pipeline.add_node` |
| `ModelRouter`, `ModelRoutingMixin`, `ModelSource`, `ModelConfig` | — |
| `Pipeline.load`, `.from_model_id`, `.from_local_model`, `configure_pipeline` | `Pipeline()` + `add_node` |
| `MedicalCodingPipeline`, `SummarizationPipeline` | The cookbook recipes |
| `CdsCardCreator` | Build `Card` inline |
| `Pipeline[Document]()`, `DataContainer` | `Pipeline()` |
| `Document.models`, `ModelOutputs`, `Document.nlp`, `NlpAnnotations` | Run the model and build output in one node |
| `TextPreProcessor`, `TextPostProcessor`, `FHIRProblemListExtractor` | `document.update_problem_list(...)` |
| `Dataset`, `FeatureSchema`, `FHIRFeatureMapper`, `BaseMapper`, `bundle_to_dataframe`, `TimeWindow`, `ValidationResult` | `create_risk_assessment_from_prediction` for the ML → FHIR hop |
| `CodedEntry.date` | `CodedEntry.authored_on` |
| HL7v2 anything | Removed entirely |
