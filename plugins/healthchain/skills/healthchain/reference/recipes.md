# HealthChain recipes

Four end-to-end paths, one per building block. Each is a starting point to adapt, not a template to fill in.

## 1. Stand up a FHIR gateway service

Starting from nothing:

<!-- pytest.mark.skip -->
```bash
healthchain new my-app -t fhir-gateway
cd my-app
```

Adding a service to a directory that already exists — a repo the user already chose — pass `.` instead, which scaffolds in place and refuses rather than overwriting anything already there:

<!-- pytest.mark.skip -->
```bash
healthchain new . -t fhir-gateway
```

Either way the scaffold gives you `app.py` and `healthchain.yaml`. Writing `app.py` by hand instead skips `healthchain.yaml`, and with it `healthchain serve`, `healthchain status`, and the governance config. Edit `app.py` to add your sources and endpoints, then:

<!-- pytest.mark.skip -->
```bash
healthchain serve
```

`healthchain status` shows what `healthchain.yaml` is configured to do — port, security, governance. Source credentials come from environment variables (`EPIC_CLIENT_ID`, `EPIC_CLIENT_SECRET`, and the Cerner equivalents for the two-source scaffold); `healthchain serve` fails fast with a config error if they're missing, which is the fastest way to find out what a source needs. See `reference/api.md` for the `FHIRGateway` surface `app.py` is built on.

## 2. Turn model output into a validated FHIR resource

The write path is the one that matters: a model produced something, and it has to enter the record correctly.

```python
from healthchain.fhir import create_condition, create_patient, validate_resource

model_output = {"text": "hypertension", "code": "38341003"}

# The subject comes from your data — the request, a lookup, the bundle you loaded.
# A Condition pointing at a patient that doesn't exist is valid FHIR and still wrong,
# so resolve the real patient before you build anything that references one.
patient = create_patient(identifier="MRN-12345")
subject = f"Patient/{patient.id}"

condition = create_condition(
    subject=subject,
    code=model_output["code"],
    display=model_output["text"],
    system="http://snomed.info/sct",
)

report = validate_resource(condition)
if not report.valid:
    for issue in report.issues:
        print(issue)
else:
    print(condition.code.coding[0].code)
```

`validate_resource` never raises — the report is data, which is what makes a build → validate → correct loop work for an agent.

Codes come from a lookup, not from the model:

```python
from healthchain.terminology import LocalCodeLookup

lookup = LocalCodeLookup()
hits = lookup.search("metoprolol")
assert hits[0].code == "866427"
print(hits[0].display, hits[0].system)
```

The demo catalog covers RxNorm and LOINC, and leaves out SNOMED — that needs its own license to resolve display text; `lookup.entries()` enumerates what's there. Swap in any object with a `search(text, system=None)` method for real terminology.

## 3. Give an agent FHIR tools

Zero code, over MCP, pointed at a bundle already on disk:

<!-- pytest.mark.skip -->
```bash
pip install "healthchain[mcp]"
healthchain mcp --bundle patient_bundle.json
```

Point Claude Desktop or any MCP client at that stdio server and the FHIR tools appear — point `--bundle` at your own file.

From Python, `FHIRToolkit` is the same tools before any MCP or LangChain wrapping. Load the bundle at construction time and the read tools operate on it:

```python
from healthchain.tools import FHIRToolkit

kit = FHIRToolkit(bundle="tests/data/test_reference_bundle.json")
print([t.name for t in kit.get_tools()])
```

`run_tool(name, arguments)` is what an MCP client or a hand-rolled agent loop calls — pass a tool name and its arguments straight through. This is the read half — a flat, coded view of every Condition in the loaded bundle:

```python
from healthchain.tools import FHIRToolkit

kit = FHIRToolkit(bundle="tests/data/test_reference_bundle.json")
entries = kit.run_tool("get_coded_entries", {"resource_type": "Condition"})
print(entries[0]["code"], entries[0]["display"])
```

And the write half — `build_resource` runs the same `create_*` + `validate_resource` path as recipe 2, callable by name:

```python
from healthchain.tools import FHIRToolkit

kit = FHIRToolkit()
result = kit.run_tool(
    "build_resource",
    {
        "resource_type": "Condition",
        "subject": "Patient/123",
        "code": "38341003",
        "display": "Hypertension",
    },
)
print(result["ok"], result["resource"]["resourceType"])
```

`get_resources`, `get_coded_entries`, and `resolve_reference` need a loaded bundle and return `{"ok": False, ...}` if none was given; `build_resource`, `validate_resource`, `load_bundle`, `lookup_code`, and `list_codes` don't — the toolkit's job is building, validating, and reading, the same split `healthchain.fhir` itself keeps.

`kit.as_langchain()` returns this same tool list as LangChain `StructuredTool`s (`healthchain[langchain]`). `kit.as_mcp().run()` is the programmatic form of the CLI command above (`healthchain[mcp]`) — whichever view an agent gets, `build_resource` and `get_coded_entries` behave identically underneath.

## 4. Prove it works without a real EHR

<!-- pytest.mark.skip -->
```bash
pip install "healthchain[sandbox]"
healthchain serve &
healthchain sandbox run --url http://localhost:8000/cds/cds-services/my-service
```

`--url` is required and points at your own running service's real endpoint — the value above is the CLI's own example shape, not a fixed string to copy as-is. `SandboxClient` plays the role of the EHR — it fires protocol-shaped requests (CDS Hooks, SOAP/CDA) at the running service, so the integration can be verified whether a human wrote it or an agent built it. `healthchain seed medplum ./data` loads demo FHIR into a test server first when the service needs data to read.

## Reading an existing bundle

```python
from healthchain.fhir import load_bundle, get_coded_entries

bundle = load_bundle("tests/data/test_reference_bundle.json")
for entry in get_coded_entries(bundle, "Condition"):
    print(entry.code, entry.display, entry.authored_on)
```
