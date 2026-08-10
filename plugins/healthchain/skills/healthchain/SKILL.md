---
name: healthchain
description: Use when building, debugging, or deploying a Python service that touches FHIR resources, EHR APIs, CDS Hooks, clinical documents, or patient data — including writing model or agent output back into a patient record, connecting to Epic/Cerner/Medplum, or serving FHIR tools to an agent over MCP or LangChain.
---

# HealthChain

HealthChain is a Python SDK for healthcare AI services — the layer that turns model or agent output into FHIR a real system will accept.

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

## The CLI drives the whole loop

```bash
healthchain new my-app -t fhir-gateway   # scaffold (also: cds-hooks, default)
healthchain serve                        # run app:app with uvicorn
healthchain sandbox run --url URL        # fire test requests at it (--url required)
healthchain seed medplum ./data          # load demo FHIR into a test server
healthchain mcp --bundle patient.json    # serve FHIR agent tools over stdio
healthchain status                       # what healthchain.yaml is configured to do
```

`healthchain.yaml` is the deployment artifact — port, security, governance config.

## Why the helpers instead of raw Pydantic

`create_*` gives flat constructors — scalars in, correctly nested resources out — with no invented facts: no auto-timestamps, no guessed statuses. `validate_resource` catches spec-invalid codes that type checks alone let through, and returns a `ValidationReport` rather than raising, so a build → validate → correct loop reads the report as data.

What's not checked: profiles and invariants — that's a server's `$validate`. Licensed terminologies like SNOMED need their own license to resolve display text.

## Before writing code

Check exact signatures — and removed 0.15 names — in `reference/api.md` before using the Gateway surface; it is not guessable from memory alone.

- Deeper API docs: https://healthchainai.github.io/HealthChain/llms.txt
