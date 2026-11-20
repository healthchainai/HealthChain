# Cookbook

Runnable patterns for building reusable applications with healthcare data.

Connect live FHIR sources, turn extracts and model output into coded, validated FHIR, and deliver results through standard healthcare and agent interfaces.

Run a recipe

Cookbooks are runnable scripts in the HealthChain repository. Clone the repo to get started:

```bash
git clone https://github.com/healthchainai/HealthChain.git
cd HealthChain
uv sync --all-extras   # or: pip install healthchain
```

Each cookbook page states the exact `pip install` line it needs — optional capabilities live in extras (`[cda]`, `[examples]`, `[sandbox]`, ...), so you only install what the example uses.

Run any cookbook from the repo root — e.g. `python cookbook/ml_risk_to_fhir.py`. Filter by **Zero Setup** below to find examples that run immediately with no external accounts. Connecting to a live FHIR API? Start with [Working with FHIR Sandboxes](https://healthchainai.github.io/HealthChain/cookbook/setup_fhir_sandboxes/index.md).

Filter: Zero Setup Beginner Intermediate Advanced FHIR Gateway CDS Hooks Interop Research / ML GenAI Clear

\[🗄️

Research Extract to Validated FHIR API

Turn a research database extract into typed FHIR resources, identify structural and required-code errors, and load the validated output into a queryable FHIR server.

Beginner Research / ML FHIR Gateway Zero Setup\](https://healthchainai.github.io/HealthChain/cookbook/research_extract_fhir_api/index.md) \[🔗

Multi-Source FHIR Data

Query multiple FHIR sources, deduplicate conditions, preserve provenance, and handle source-specific failures through one interface.

Intermediate FHIR Gateway\](https://healthchainai.github.io/HealthChain/cookbook/multi_ehr_aggregation/index.md) \[💬

FHIR-Grounded Patient Q&A

Use live FHIR as model context and return answers grounded in the underlying record — for research exploration or patient-facing applications.

Beginner GenAI FHIR Gateway\](https://healthchainai.github.io/HealthChain/cookbook/fhir_qa/index.md) \[🔬

Turn Model Predictions into FHIR RiskAssessments

Turn risk scores from XGBoost, scikit-learn, or another model into validated FHIR RiskAssessment resources, then optionally write them to a live FHIR server.

Intermediate Research / ML FHIR Gateway Zero Setup\](https://healthchainai.github.io/HealthChain/cookbook/ml_model_deployment/index.md) \[📋

Prior Authorization: Chart Pull to Coded Packet

Pull a chart from a live FHIR server, code the free-text diagnosis and requested service with retrieve-then-rerank terminology lookup, check the utilization-review criteria, and emit a validated authorization packet.

Intermediate FHIR Gateway Interop Zero Setup\](https://healthchainai.github.io/HealthChain/cookbook/prior_auth_packet/index.md) \[🧾

Automated Coding and FHIR Integration

Run extraction and coding logic over clinical documents, map conditions to SNOMED CT, and return structured FHIR for downstream use.

Advanced Interop\](https://healthchainai.github.io/HealthChain/cookbook/clinical_coding/index.md) \[📝

Deliver Discharge Summaries with CDS Hooks

Build a CDS Hooks service that turns discharge notes into concise summaries and delivers structured cards in the EHR workflow.

Beginner CDS Hooks Zero Setup\](https://healthchainai.github.io/HealthChain/cookbook/discharge_summarizer/index.md) \[🚦

Working with FHIR Sandboxes

Connect to Epic, Medplum, and other FHIR sandboxes when you need a safe live endpoint for the gateway examples.

Beginner FHIR Gateway\](https://healthchainai.github.io/HealthChain/cookbook/setup_fhir_sandboxes/index.md)

No cookbooks match the selected filters. [Clear filters](#)

______________________________________________________________________

## From recipe to reusable application

Cookbooks keep every step visible in one runnable script. Once a pattern fits your use case, move the same logic into an application and choose the interface it needs: FHIR REST, CDS Hooks, CDA, MCP, or LangChain.

```bash
# 1. Run a cookbook locally
python cookbook/cds_discharge_summarizer_hf_trf.py

# 2. Scaffold a project
healthchain new my-cds-service -t cds-hooks
cd my-cds-service

# 3. Move your hook logic into app.py, then run with config
healthchain serve
```

`app.run()` keeps a standalone recipe easy to execute. When you need a configurable service, `healthchain serve` reads `healthchain.yaml` for the service port and FHIR source names while credentials remain in environment variables.

**Separate application logic from connection config:**

```python
# cookbook — source configuration lives beside the example
gateway = FHIRGateway()
gateway.add_source("medplum", FHIRAuthConfig.from_env("MEDPLUM").to_connection_string())

app = HealthChainAPI(title="My App", service_type="fhir-gateway")
app.register_gateway(gateway)
app.run(port=8000)
```

```yaml
# healthchain.yaml — service and source names are reusable across environments
service:
  type: fhir-gateway
  port: 8000

sources:
  medplum:
    env_prefix: MEDPLUM   # credentials stay in .env
```

```python
# app.py — keep application logic independent of site credentials
from healthchain.config import AppConfig
from healthchain.gateway import FHIRGateway, HealthChainAPI

config = AppConfig.load()
gateway = FHIRGateway.from_config(config)

app = HealthChainAPI(title="My App")
app.register_gateway(gateway)
```

Credentials (API keys, client secrets) always stay in `.env` — never in `healthchain.yaml`.

Configuration reference

See the [configuration reference](https://healthchainai.github.io/HealthChain/reference/config/index.md) for service, FHIR source, and security settings.
