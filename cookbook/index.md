# Cookbook

Hands-on, runnable recipes for building healthcare AI applications with HealthChain.

Getting started

Cookbooks are runnable scripts in the HealthChain repository. Clone the repo to get started:

```bash
git clone https://github.com/healthchainai/HealthChain.git
cd HealthChain
uv sync --all-extras   # or: pip install healthchain
```

Each cookbook page states the exact `pip install` line it needs — optional capabilities live in extras (`[cda]`, `[examples]`, `[sandbox]`, ...), so you only install what the example uses.

Run any cookbook from the repo root — e.g. `python cookbook/ml_risk_to_fhir.py`. Filter by **Zero Setup** below to find examples that run immediately with no external accounts.

Filter: Beginner Intermediate Advanced GenAI ML Research CDS Hooks FHIR Gateway Interop Zero Setup Clear

\[🚦

Working with FHIR Sandboxes

Spin up and access free Epic, Medplum, and other FHIR sandboxes for safe experimentation. Recommended first step before the other tutorials.

Beginner FHIR Gateway\](https://healthchainai.github.io/HealthChain/cookbook/setup_fhir_sandboxes/index.md) \[🔬

Deploy ML Models: Predictions to FHIR RiskAssessments

Turn the risk scores your model already produces — XGBoost, scikit-learn, anything — into spec-valid FHIR RiskAssessment resources, then write them back to a live FHIR server through FHIRGateway.

Intermediate ML Research FHIR Gateway Zero Setup\](https://healthchainai.github.io/HealthChain/cookbook/ml_model_deployment/index.md) \[💬

FHIR-Grounded Patient Q&A

Build a patient Q&A service that fetches live FHIR data, formats it as LLM context via a pipeline, and returns grounded answers. Foundation pattern for patient portal chatbots and care navigation assistants.

Beginner GenAI FHIR Gateway\](https://healthchainai.github.io/HealthChain/cookbook/fhir_qa/index.md) \[🔗

Multi-Source Patient Data Aggregation

Merge patient data from multiple FHIR sources (Epic, Cerner, etc.), deduplicate conditions, prove provenance, and handle cross-vendor errors. Foundation for RAG and analytics workflows.

Intermediate GenAI FHIR Gateway\](https://healthchainai.github.io/HealthChain/cookbook/multi_ehr_aggregation/index.md) \[🗄️

Research Extract to Validated FHIR API

Turn a research database extract into typed, validated FHIR resources and load them into a FHIR server you can query like any EHR — validation catches the dirty rows before they ship.

Beginner ML Research FHIR Gateway Zero Setup\](https://healthchainai.github.io/HealthChain/cookbook/research_extract_fhir_api/index.md) \[🧾

Automate Clinical Coding & FHIR Integration

Extract medical conditions from clinical documentation using AI, map to SNOMED CT codes, and sync as FHIR Condition resources for billing, analytics, and interoperability.

Advanced Interop\](https://healthchainai.github.io/HealthChain/cookbook/clinical_coding/index.md) \[📝

Summarize Discharge Notes with CDS Hooks

Deploy a CDS Hooks-compliant service that listens for discharge events, auto-generates concise plain-language summaries, and delivers actionable clinical cards directly into the EHR workflow.

Beginner CDS Hooks Zero Setup\](https://healthchainai.github.io/HealthChain/cookbook/discharge_summarizer/index.md)

No cookbooks match the selected filters. [Clear filters](#)

______________________________________________________________________

## From cookbook to service

Cookbooks are standalone scripts — run them directly to explore and experiment. When you're ready to build a proper service, scaffold a project and move your logic in:

```bash
# 1. Run a cookbook locally
python cookbook/cds_discharge_summarizer_hf_trf.py

# 2. Scaffold a project
healthchain new my-cds-service -t cds-hooks
cd my-cds-service

# 3. Move your hook logic into app.py, then run with config
healthchain serve
```

`app.run()` (used in cookbooks) is a convenience wrapper — equivalent to running uvicorn directly. `healthchain serve` reads `healthchain.yaml` for port, TLS, and deployment settings, and prints a startup banner so you can see what's active at a glance.

**What moves from your script into `healthchain.yaml`:**

```python
# cookbook — everything hardcoded in Python
gateway = FHIRGateway()
gateway.add_source("medplum", FHIRAuthConfig.from_env("MEDPLUM").to_connection_string())

llm = ChatAnthropic(model="claude-opus-4-8", max_tokens=512)

app = HealthChainAPI(title="My App", service_type="fhir-gateway")
app.run(port=8000)
```

```yaml
# healthchain.yaml — port, sources, and LLM provider declared here
service:
  type: fhir-gateway
  port: 8000

sources:
  medplum:
    env_prefix: MEDPLUM   # credentials stay in .env

llm:
  provider: anthropic
  model: claude-opus-4-8
  max_tokens: 512
```

```python
# app.py — load from config instead
from langchain.chat_models import init_chat_model

from healthchain.config.appconfig import AppConfig
from healthchain.gateway import FHIRGateway, HealthChainAPI

config = AppConfig.load()
gateway = FHIRGateway.from_config(config)
llm = init_chat_model(f"{config.llm.provider}:{config.llm.model}")

app = HealthChainAPI(title="My App")
```

Credentials (API keys, client secrets) always stay in `.env` — never in `healthchain.yaml`.

Configuration reference

See the [configuration reference](https://healthchainai.github.io/HealthChain/reference/config/index.md) for all available settings — security, compliance, and more.
