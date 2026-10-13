# Cookbook

Runnable patterns for building reusable applications with healthcare data.

Connect live FHIR sources, turn extracts and model output into coded, validated FHIR, and deliver results through standard healthcare and agent interfaces.

!!! tip "Run a recipe"
    Cookbooks are runnable scripts in the HealthChain repository. Clone the repo to get started:

    ```bash
    git clone https://github.com/healthchainai/HealthChain.git
    cd HealthChain
    uv sync --all-extras   # or: pip install healthchain
    ```

    Each cookbook page states the exact `pip install` line it needs — optional capabilities live in extras (`[cda]`, `[examples]`, `[sandbox]`, ...), so you only install what the example uses.

    Run any cookbook from the repo root — e.g. `python cookbook/ml_risk_to_fhir.py`. Filter by **Zero Setup** below to find examples that run immediately with no external accounts. Connecting to a live FHIR API? Start with [Working with FHIR Sandboxes](setup_fhir_sandboxes.md).

<div class="tag-legend">
  <span class="tag-legend-title">Filter:</span>
  <span class="tag tag-filter tag-zerosetup" data-tag="zero-setup">Zero Setup</span>
  <span class="tag tag-filter tag-beginner" data-tag="beginner">Beginner</span>
  <span class="tag tag-filter tag-intermediate" data-tag="intermediate">Intermediate</span>
  <span class="tag tag-filter tag-advanced" data-tag="advanced">Advanced</span>
  <span class="tag tag-filter tag-fhirgateway" data-tag="fhir-gateway">FHIR Gateway</span>
  <span class="tag tag-filter tag-cdshooks" data-tag="cdshooks">CDS Hooks</span>
  <span class="tag tag-filter tag-interop" data-tag="interop">Interop</span>
  <span class="tag tag-filter tag-ml" data-tag="ml">Research / ML</span>
  <span class="tag tag-filter tag-genai" data-tag="genai">GenAI</span>
  <span class="tag-clear hidden" id="clearFilters">Clear</span>
</div>

<div class="cookbook-wrapper">
<div class="cookbook-grid" id="cookbookGrid">

<a href="research_extract_fhir_api/" class="cookbook-card" data-tags="ml fhir-gateway beginner zero-setup">
  <div class="cookbook-card-icon">🗄️</div>
  <div class="cookbook-card-title">Research Extract to Validated FHIR API</div>
  <div class="cookbook-card-description">
    Turn a research database extract into typed FHIR resources, identify structural and required-code errors, and load the validated output into a queryable FHIR server.
  </div>
  <div class="cookbook-tags">
    <span class="tag tag-beginner">Beginner</span>
    <span class="tag tag-ml">Research / ML</span>
    <span class="tag tag-fhirgateway">FHIR Gateway</span>
    <span class="tag tag-zerosetup">Zero Setup</span>
  </div>
</a>

<a href="multi_ehr_aggregation/" class="cookbook-card" data-tags="fhir-gateway intermediate">
  <div class="cookbook-card-icon">🔗</div>
  <div class="cookbook-card-title">Multi-Source FHIR Data</div>
  <div class="cookbook-card-description">
    Query multiple FHIR sources, deduplicate conditions, preserve provenance, and handle source-specific failures through one interface.
  </div>
  <div class="cookbook-tags">
    <span class="tag tag-intermediate">Intermediate</span>
    <span class="tag tag-fhirgateway">FHIR Gateway</span>
  </div>
</a>

<a href="fhir_qa/" class="cookbook-card" data-tags="genai fhir-gateway beginner">
  <div class="cookbook-card-icon">💬</div>
  <div class="cookbook-card-title">FHIR-Grounded Patient Q&A</div>
  <div class="cookbook-card-description">
    Use live FHIR as model context and return answers grounded in the underlying record — for research exploration or patient-facing applications.
  </div>
  <div class="cookbook-tags">
    <span class="tag tag-beginner">Beginner</span>
    <span class="tag tag-genai">GenAI</span>
    <span class="tag tag-fhirgateway">FHIR Gateway</span>
  </div>
</a>

<a href="ml_model_deployment/" class="cookbook-card" data-tags="ml fhir-gateway intermediate zero-setup">
  <div class="cookbook-card-icon">🔬</div>
  <div class="cookbook-card-title">Turn Model Predictions into FHIR RiskAssessments</div>
  <div class="cookbook-card-description">
    Turn risk scores from XGBoost, scikit-learn, or another model into validated FHIR RiskAssessment resources, then optionally write them to a live FHIR server.
  </div>
  <div class="cookbook-tags">
    <span class="tag tag-intermediate">Intermediate</span>
    <span class="tag tag-ml">Research / ML</span>
    <span class="tag tag-fhirgateway">FHIR Gateway</span>
    <span class="tag tag-zerosetup">Zero Setup</span>
  </div>
</a>

<a href="prior_auth_packet/" class="cookbook-card" data-tags="fhir-gateway interop intermediate zero-setup">
  <div class="cookbook-card-icon">📋</div>
  <div class="cookbook-card-title">Prior Authorization: Chart Pull to Coded Packet</div>
  <div class="cookbook-card-description">
    Pull a chart from a live FHIR server, code the free-text diagnosis and requested service with retrieve-then-rerank terminology lookup, check the utilization-review criteria, and emit a validated authorization packet.
  </div>
  <div class="cookbook-tags">
    <span class="tag tag-intermediate">Intermediate</span>
    <span class="tag tag-fhirgateway">FHIR Gateway</span>
    <span class="tag tag-interop">Interop</span>
    <span class="tag tag-zerosetup">Zero Setup</span>
  </div>
</a>

<a href="clinical_coding/" class="cookbook-card" data-tags="interop advanced">
  <div class="cookbook-card-icon">🧾</div>
  <div class="cookbook-card-title">Automated Coding and FHIR Integration</div>
  <div class="cookbook-card-description">
    Run extraction and coding logic over clinical documents, map conditions to SNOMED CT, and return structured FHIR for downstream use.
  </div>
  <div class="cookbook-tags">
    <span class="tag tag-advanced">Advanced</span>
    <span class="tag tag-interop">Interop</span>
  </div>
</a>

<a href="discharge_summarizer/" class="cookbook-card" data-tags="cdshooks beginner zero-setup">
  <div class="cookbook-card-icon">📝</div>
  <div class="cookbook-card-title">Deliver Discharge Summaries with CDS Hooks</div>
  <div class="cookbook-card-description">
    Build a CDS Hooks service that turns discharge notes into concise summaries and delivers structured cards in the EHR workflow.
  </div>
  <div class="cookbook-tags">
    <span class="tag tag-beginner">Beginner</span>
    <span class="tag tag-cdshooks">CDS Hooks</span>
    <span class="tag tag-zerosetup">Zero Setup</span>
  </div>
</a>

<a href="setup_fhir_sandboxes/" class="cookbook-card" data-tags="beginner fhir-gateway">
  <div class="cookbook-card-icon">🚦</div>
  <div class="cookbook-card-title">Working with FHIR Sandboxes</div>
  <div class="cookbook-card-description">
    Connect to Epic, Medplum, and other FHIR sandboxes when you need a safe live endpoint for the gateway examples.
  </div>
  <div class="cookbook-tags">
    <span class="tag tag-beginner">Beginner</span>
    <span class="tag tag-fhirgateway">FHIR Gateway</span>
  </div>
</a>

<div class="no-results hidden" id="noResults">
  No cookbooks match the selected filters. <a href="#" onclick="clearAllFilters(); return false;">Clear filters</a>
</div>

</div>
</div>

---

## From recipe to reusable application {#from-cookbook-to-service}

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

!!! tip "Configuration reference"
    See the [configuration reference](../reference/config.md) for service, FHIR source, and security settings.
