# Agent Tools

`healthchain.tools` packages the FHIR build/validate/read/lookup surface as **agent tools**: flat scalar schemas a model can fill reliably, JSON-safe returns, and errors as values a model can read and correct — a raised exception kills an agent loop; `{"ok": false, "issues": [...]}` is something it can fix.

## Quick Start

```python
from healthchain.tools import FHIRToolkit

kit = FHIRToolkit(bundle="synthea_patient.json")  # optional preload

kit.get_tools()      # framework-agnostic tools
kit.as_mcp().run()   # MCP server over stdio  (pip install healthchain[mcp])
kit.as_langchain()   # LangChain StructuredTools (healthchain[langchain])
```

Or from the command line — one line to register with an MCP client:

```bash
pip install healthchain[mcp]
healthchain mcp --bundle synthea_patient.json

# e.g. with Claude Code:
claude mcp add healthchain -- healthchain mcp
```

## The tools

| Tool                | What it does                                                                                                                                                                                                                                                     |
| ------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `build_resource`    | Build a FHIR resource from flat fields (Condition, MedicationStatement, Observation, AllergyIntolerance, Patient — including the dosage triplet `dose_value`/`dose_unit`/`frequency_per_day`), validate it, and return `{ok, resource}` or `{ok: false, issues}` |
| `validate_resource` | Validate any FHIR resource dict, required value-set bindings included — the read half of an agent's build→validate→correct loop                                                                                                                                  |
| `load_bundle`       | Load a bundle from a path or JSON string and make it the working bundle; invalid bundles return issues locating each problem                                                                                                                                     |
| `get_resources`     | Full FHIR JSON for every resource of a type in the loaded bundle                                                                                                                                                                                                 |
| `get_coded_entries` | Flattened coded identity records (`code`/`display`/`system`/`status`/`authored_on`/`value`/`unit`), with `medicationReference` resolved                                                                                                                          |
| `resolve_reference` | Resolve `Patient/123` / `urn:uuid:...` references; contained (`#id`) references take a `parent_resource_id`                                                                                                                                                      |
| `lookup_code`       | Search the terminology catalog — so the model uses a *returned* code, never an invented one                                                                                                                                                                      |
| `list_codes`        | Browse the whole catalog. Only registered when the lookup is enumerable (`LocalCodeLookup` is; a remote terminology service isn't)                                                                                                                               |

## The toolkit is stateful

`FHIRToolkit` holds **one loaded bundle**, validated once. Read tools operate on it instead of shuttling bundle JSON through tool arguments — which agents can't do at realistic bundle sizes, and which would re-validate on every call. Two ways to get data in:

```python
# Host-injected (typical in a service: your app loads, the agent reads)
kit = FHIRToolkit(bundle=my_bundle)          # Bundle | dict | JSON | path
kit.bundle = other_bundle                     # swap at any time

# Agent-loaded: the model calls the load_bundle tool itself
```

Plug in a real terminology service behind the same protocol:

```python
kit = FHIRToolkit(lookup=MyTerminologyService())  # any TerminologyLookup
```

## Hand-rolled tool-calling loops

No framework required — `tool.spec` is the plain `{name, description, input_schema}` dict tool-calling APIs expect, and `run_tool` dispatches by name:

```python
kit = FHIRToolkit()
tools = [t.spec for t in kit.get_tools()]     # pass as your tools= parameter

# when the model returns a tool call:
result = kit.run_tool(call_name, call_input)  # dict or JSON-string arguments
```

Errors are values

Tools never raise. Missing bundle, unknown resource type, invalid codes, unresolvable references — all come back as `{"ok": false, "error": ...}` or `{"ok": false, "issues": [...]}` so the agent loop keeps control.
