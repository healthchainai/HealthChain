---
name: healthchain
description: Use when building or debugging Python software that connects to FHIR APIs, builds or validates FHIR resources, serves CDS Hooks or clinical documents, or exposes FHIR tools over MCP or LangChain — including work with Epic, Cerner, Medplum, and other FHIR servers.
---

# HealthChain

HealthChain is an open-source Python library for live FHIR connectivity and validated FHIR tooling, built for research software, healthcare data, and AI teams.

Install: `pip install healthchain`. Optional capability comes from extras: `healthchain[mcp]`, `[langchain]`, `[cda]`, `[sandbox]`, `[examples]`.

## Four building blocks

Pick by what the task needs. Full signatures are in `reference/api.md`; end-to-end runnable code is in `reference/recipes.md`.

| Block | Use it when | Entry point |
|---|---|---|
| **Gateway** | Connecting to one or many EHR FHIR APIs, or serving CDS Hooks / clinical documents | `HealthChainAPI`, `FHIRGateway` |
| **FHIR & Validation** | Creating, validating, reading, or coding FHIR resources | `healthchain.fhir` |
| **Agent Tools** | Handing an agent typed FHIR tools over MCP or LangChain | `FHIRToolkit` |
| **Sandbox** | Proving the service works with no real EHR | `SandboxClient`, `healthchain sandbox run` |

`Pipeline` and `Document` sit under the hood — supporting primitives that carry text plus FHIR through protocol flows. Reach for them when wiring a model into a gateway flow, not as a starting point.

## Common CLI workflows

```bash
healthchain new my-app -t fhir-gateway   # scaffold (also: cds-hooks, default)
healthchain serve                        # run app:app with uvicorn
healthchain sandbox run --url URL        # fire test requests at it (--url required)
healthchain seed medplum ./data          # load demo FHIR into a test server
healthchain mcp --bundle patient.json    # serve FHIR agent tools over stdio
healthchain status                       # what healthchain.yaml is configured to do
```

Starting from nothing, `healthchain new my-app` creates the directory. Already inside a project the user chose? `healthchain new .` scaffolds into the current directory instead, and refuses rather than overwriting anything already there. Either way you get `healthchain.yaml`, which holds service settings and named FHIR sources while credentials remain in environment variables. Hand-writing `app.py` skips the config-driven setup.

## Why the helpers instead of raw Pydantic

`create_*` gives flat constructors — scalars in, correctly nested resources out — and reduces FHIR boilerplate. Callers remain responsible for clinical assertions; helpers provide documented defaults and never guess clinical codes. Some helpers generate IDs or metadata, and `create_document_reference` currently adds a timestamp. `validate_resource` checks structure and required primitive-code bindings, returning a `ValidationReport` rather than raising so a build → validate → correct loop reads the report as data.

What's not checked: profiles, FHIRPath invariants, `CodeableConcept` value-set bindings, and reference integrity. Full conformance may require a server's `$validate`. Licensed terminologies like SNOMED need their own license to resolve display text.

## Before writing code

Check exact signatures — and removed 0.15 names — in `reference/api.md` before using the Gateway surface; it is not guessable from memory alone.

- Deeper API docs: https://healthchainai.github.io/HealthChain/llms.txt
