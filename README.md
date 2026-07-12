<div align="center" style="margin-bottom: 1em;">

<img src="https://raw.githubusercontent.com/healthchainai/HealthChain/main/docs/assets/brand/hero/readme-hero-transparent.png" alt="HealthChain — Build, test & deploy AI in real healthcare systems" width="700"></img>

<!-- Project Badges -->

[![PyPI Version][pypi-version-badge]][pypi]
[![Stars][stars-badge]][stars]
[![Downloads][downloads-badge]][pypistats]

[![License][license-badge]][license]
[![Python Versions][python-versions-badge]][pypi]
[![Build Status][build-badge]][build]
[![AI-Assisted Development][ai-badge]][claude-md]
[![DOI](https://zenodo.org/badge/785158333.svg)](https://doi.org/10.5281/zenodo.20056729)

[![Substack][substack-badge]][substack]
[![Discord][discord-badge]][discord]

</div>

<h2 align="center" style="border-bottom: none">Open-Source Python SDK for Healthcare AI</h2>

<div align="center">

The model is the easy part — the integration that blocks it from ever reaching production is the hard part. HealthChain handles it, giving your models and agents tools they can trust: **type-safe FHIR resources**, **real-time EHR connectivity**, and **production-ready deployment**. So what you build holds up outside the demo.

</div>

## Installation

```bash
pip install healthchain
```

## Quick Start

```bash
# Scaffold a FHIR Gateway project
healthchain new my-app -t fhir-gateway
cd my-app

# Run locally
healthchain serve
```

<div align="center">
  <img src="https://raw.githubusercontent.com/healthchainai/HealthChain/main/docs/assets/images/demo.gif" alt="HealthChain CLI demo" width="700">
</div>

Edit `app.py` to add your model, and `healthchain.yaml` to configure deployment settings.

See the [CLI reference](https://healthchainai.github.io/HealthChain/cli/) for all commands.

Building with an AI assistant? Point it at [llms.txt](https://healthchainai.github.io/HealthChain/llms.txt) for a map of the current API docs.

## Core Features

The quickest way for AI developers and researchers to ship healthcare AI — everything you need out of the box, built to scale with you.

<table>
  <tr>
    <td width="50%" valign="top">
      <picture>
        <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/healthchainai/HealthChain/main/docs/assets/images/cards/hc-card-aggregation-dark.svg">
        <img src="https://raw.githubusercontent.com/healthchainai/HealthChain/main/docs/assets/images/cards/hc-card-aggregation-light.svg" alt="Epic, Cerner and your EHR flow through FHIRGateway into one patient record; manual extracts are crossed out" width="100%">
      </picture>
      <div align="center">
        <br>
        <a href="https://healthchainai.github.io/HealthChain/reference/gateway/gateway/"><strong>🔌 Multi-EHR Data Aggregation</strong></a>
        <br><br>
        <div>Connect to live FHIR APIs across Epic, Cerner, and more — and move research pipelines off manual database extracts onto data infrastructure that scales past one site</div><br>
        <a href="https://healthchainai.github.io/HealthChain/cookbook/multi_ehr_aggregation/">Getting Started →</a>
        <br><br>
      </div>
    </td>
    <td width="50%" valign="top">
      <picture>
        <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/healthchainai/HealthChain/main/docs/assets/images/cards/hc-card-fhir-dark.svg">
        <img src="https://raw.githubusercontent.com/healthchainai/HealthChain/main/docs/assets/images/cards/hc-card-fhir-light.svg" alt="Messy model output goes through validate_resource and comes out as FHIR you can trust" width="100%">
      </picture>
      <div align="center">
        <br>
        <a href="https://healthchainai.github.io/HealthChain/reference/utilities/fhir_helpers/"><strong>🔥 FHIR as a Superpower</strong></a>
        <br><br>
        <div>Type-safe FHIR resources, validation that catches broken data before it ships, and terminology lookups — the strict schema that turns healthcare data into a built-in unit test</div><br>
        <a href="https://healthchainai.github.io/HealthChain/reference/utilities/fhir_helpers/">Getting Started →</a>
        <br><br>
      </div>
    </td>
  </tr>
  <tr>
    <td width="50%" valign="top">
      <picture>
        <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/healthchainai/HealthChain/main/docs/assets/images/cards/hc-card-agent-tools-dark.svg">
        <img src="https://raw.githubusercontent.com/healthchainai/HealthChain/main/docs/assets/images/cards/hc-card-agent-tools-light.svg" alt="FHIRToolkit serves typed FHIR tools to Claude over MCP and to LangChain agents" width="100%">
      </picture>
      <div align="center">
        <br>
        <a href="https://healthchainai.github.io/HealthChain/reference/utilities/tools/"><strong>🤖 Tools Your Agents Can Trust</strong></a>
        <br><br>
        <div>Hand any agent typed, validated FHIR tools from one toolkit — served to Claude over MCP or dropped into LangChain, so what your agent writes is valid and correctly coded</div><br>
        <a href="https://healthchainai.github.io/HealthChain/reference/utilities/tools/">Getting Started →</a>
        <br><br>
      </div>
    </td>
    <td width="50%" valign="top">
      <picture>
        <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/healthchainai/HealthChain/main/docs/assets/images/cards/hc-card-fhir-qa-dark.svg">
        <img src="https://raw.githubusercontent.com/healthchainai/HealthChain/main/docs/assets/images/cards/hc-card-fhir-qa-light.svg" alt="A patient question plus the live FHIR record produces a grounded answer" width="100%">
      </picture>
      <div align="center">
        <br>
        <a href="https://healthchainai.github.io/HealthChain/cookbook/fhir_qa/"><strong>💬 FHIR-Grounded Patient Q&A</strong></a>
        <br><br>
        <div>Answer patient questions from their live clinical record — the foundational pattern for portal chatbots and care-plan assistants, with a schema for truth</div><br>
        <a href="https://healthchainai.github.io/HealthChain/cookbook/fhir_qa/">Getting Started →</a>
        <br><br>
      </div>
    </td>
  </tr>
</table>

## Why HealthChain?

Every serious healthcare AI project builds the same integration infrastructure from scratch. Whether you're deploying a logistic regression, a 70B-parameter model, or an agentic workflow, the wall between a trained model and a live clinical system is the same: real FHIR APIs, multi-site deployments, auditable governance. No off-the-shelf solution exists, and engineers who understand both AI and healthcare protocols are scarce and hard to retain.

HealthChain handles that complexity so you can focus on what actually matters: the model and the patient.

- **Optimized for real-time** - Connect to live FHIR APIs and integration points instead of stale data exports
- **Validation built in** - Type-safe FHIR resources and validation reports that catch broken data before it ships — including spec-invalid clinical codes that type checks alone let through
- **No invented facts** - Helpers never add clinical claims you didn't pass: no auto-generated timestamps, no guessed statuses — what enters the record is exactly what your model produced
- **Bring any model or agent** - LLMs, agents, or classical ML — and output validated FHIR
- **Works with your existing stack** - Integrates with FastAPI, MCP, and LangChain
- **Production-ready foundations** - Dockerized deployment, configurable security, and an architecture built for NHS and HIPAA environments

## 🏆 Recognition & Community

**Featured & Presented:**

- Featured in [TLDR AI Newsletter](https://tldr.tech/ai/2025-08-21) (900K+ developers)
- [Featured by Medplum](https://www.medplum.com/blog/healthchain) for open source integration with Epic
- Presented at [NHS Python Open Source Conference](https://github.com/nhs-r-community/conference-2024/blob/main/Talks/2024-11-21_jiang-kells_building-healthchain.md) ([watch talk](https://www.youtube.com/watch?v=_ZqlPsDUdSY&t=1967s))
- [Built from NHS AI deployment experience](https://open.substack.com/pub/jenniferjiangkells/p/healthchain-building-the-tool-i-wish) – read the origin story

## 🤝 Partnerships & Production Use

Exploring HealthChain for your product or organization? [Get in touch](mailto:jenniferjiangkells@gmail.com) to discuss integrations, pilots, or collaborations, or join our [Discord](https://discord.gg/UQC6uAepUz) to connect with the community.

## Usage Examples

### Creating a Gateway [[Docs](https://healthchainai.github.io/HealthChain/reference/gateway/gateway)]

```python
from healthchain.gateway import HealthChainAPI, FHIRGateway
from healthchain.fhir.r4b import Patient

# Create healthcare application
app = HealthChainAPI(title="Multi-EHR Patient Data")

# Connect to multiple FHIR sources
fhir = FHIRGateway()
fhir.add_source("epic", "fhir://fhir.epic.com/r4?client_id=epic_client_id")
fhir.add_source("cerner", "fhir://fhir.cerner.com/r4?client_id=cerner_client_id")

@fhir.aggregate(Patient)
def enrich_patient_data(id: str, source: str) -> Patient:
    """Get patient data from any connected EHR and add AI enhancements"""
    bundle = fhir.search(
        Patient,
        {"_id": id},
        source,
        add_provenance=True,
        provenance_tag="ai-enhanced",
    )
    return bundle

app.register_gateway(fhir)

# Available at: GET /fhir/transform/Patient/123?source=epic
# Available at: GET /fhir/transform/Patient/123?source=cerner

if __name__ == "__main__":
    app.run(port=8888)
```

### Giving an Agent FHIR Tools [[Docs](https://healthchainai.github.io/HealthChain/reference/utilities/tools/)]

```python
from healthchain.tools import FHIRToolkit

# One toolkit: build, validate, read, and code FHIR — as typed agent tools
kit = FHIRToolkit(bundle="patient_bundle.json")

kit.as_mcp().run()          # serve to Claude or any MCP client
tools = kit.as_langchain()  # or drop into a LangChain agent
```

Or straight from the terminal, no code:

```bash
healthchain mcp --bundle patient_bundle.json
```

## 🛣️ What we're building towards

- [x] 🔒 **Security foundations** — API-key authentication, audit logging, and TLS, configured via `healthchain.yaml` and enforced by the gateway middleware
- [ ] 📋 **Governance as config** — clinical safety, data access agreements, and compliance standards for NHS/HIPAA deployments as a first-class deployment artifact in `healthchain.yaml`
- [ ] 🔌 **Deeper EHR connectivity** — more FHIR sources, live data patterns, and real-world integration examples from pilot deployments
- [ ] 📊 **Observability** — deployment telemetry and audit trails for healthcare systems
- [x] 🤖 **A toolkit for clinical AI agents** — typed FHIR tools with validation and terminology built in, served over MCP and LangChain

## 🤝 Contributing

HealthChain is built by and for the next generation of healthcare developers — researchers moving models from retrospective data into live systems, AI developers who don't want to spend months learning FHIR before they can ship anything. The best contributions come from people who have hit a real problem and have something specific to say about it.

**Get started:**

- **Working with healthcare or research data?** [Contribute a cookbook](https://github.com/healthchainai/HealthChain/issues/208) — bring your use case, I'll personally support you through it
- Read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines
- Technical questions and ideas → [GitHub Discussions](https://github.com/healthchainai/HealthChain/discussions)
- Pilots and partnerships → [email](mailto:jenniferjiangkells@gmail.com?subject=HealthChain)

## 🤗 Acknowledgements

This project builds on [fhir.resources](https://github.com/nazrulworld/fhir.resources) and [CDS Hooks](https://cds-hooks.org/) standards developed by [HL7](https://www.hl7.org/) and [Boston Children's Hospital](https://www.childrenshospital.org/).

---

© 2024–2026 dotimplement ai. HealthChain is an open source project maintained by [dotimplement ai](https://dotimplement.ai).

<!-- Badge Links -->

[pypi-version-badge]: https://img.shields.io/pypi/v/healthchain?logo=python&logoColor=white&style=flat-square&color=%23e59875
[downloads-badge]: https://img.shields.io/pepy/dt/healthchain?style=flat-square&color=%2379a8a9
[stars-badge]: https://img.shields.io/github/stars/healthchainai/HealthChain?style=flat-square&logo=github&color=BD932F&logoColor=white
[license-badge]: https://img.shields.io/github/license/healthchainai/HealthChain?style=flat-square&color=%23e59875
[python-versions-badge]: https://img.shields.io/pypi/pyversions/healthchain?style=flat-square&color=%23eeeeee
[build-badge]: https://img.shields.io/github/actions/workflow/status/healthchainai/healthchain/ci.yml?branch=main&style=flat-square&color=%2379a8a9
[discord-badge]: https://img.shields.io/badge/chat-%235965f2?style=flat-square&logo=discord&logoColor=white
[substack-badge]: https://img.shields.io/badge/Cool_Things_In_HealthTech-%23c094ff?style=flat-square&logo=substack&logoColor=white
[ai-badge]: https://img.shields.io/badge/AI--dev_friendly-CLAUDE.MD-%23e59875?style=flat-square&logo=anthropic&logoColor=white
[pypi]: https://pypi.org/project/healthchain/
[pypistats]: https://pepy.tech/project/healthchain
[stars]: https://github.com/healthchainai/HealthChain/stargazers
[license]: https://github.com/healthchainai/HealthChain/blob/main/LICENSE
[build]: https://github.com/healthchainai/HealthChain/actions?query=branch%3Amain
[discord]: https://discord.gg/UQC6uAepUz
[substack]: https://jenniferjiangkells.substack.com/
[claude-md]: CLAUDE.md
