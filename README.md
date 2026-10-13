<!-- mcp-name: io.github.healthchainai/healthchain -->

<div align="center" style="margin-bottom: 1em;">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/healthchainai/HealthChain/main/docs/assets/brand/lockup/lockup-stacked-white.png">
  <img src="https://raw.githubusercontent.com/healthchainai/HealthChain/main/docs/assets/brand/lockup/lockup-stacked-black.png" alt="HealthChain" width="400">
</picture>

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

<h2 align="center" style="border-bottom: none">Open infrastructure for healthcare data applications.</h2>

<div align="center">

Connect Python pipelines and applications to live FHIR APIs, build and validate structured output, and deliver it through REST, CDS Hooks, CDA, MCP, or LangChain.

</div>

## Installation

```bash
pip install healthchain
```

## What HealthChain Does

HealthChain puts a consistent FHIR boundary around your Python code: live data in, your own logic in the middle, and validated FHIR out. Built for research software, healthcare data, and AI teams.

<table>
  <tr>
    <td width="50%" valign="top">
      <picture>
        <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/healthchainai/HealthChain/main/docs/assets/images/cards/hc-card-aggregation-dark.svg">
        <img src="https://raw.githubusercontent.com/healthchainai/HealthChain/main/docs/assets/images/cards/hc-card-aggregation-light.svg" alt="Epic, Cerner, and other FHIR sources flow through FHIRGateway into one patient record" width="100%">
      </picture>
      <div align="center">
        <br>
        <a href="https://healthchainai.github.io/HealthChain/reference/gateway/gateway/"><strong>🔌 Connect to Live FHIR APIs</strong></a>
        <br><br>
        <div>Connect to Epic, Cerner, Medplum, and other FHIR R4 servers through one interface that handles authentication, source routing, and common FHIR operations.</div><br>
        <a href="https://healthchainai.github.io/HealthChain/cookbook/multi_ehr_aggregation/">Getting Started →</a>
        <br><br>
      </div>
    </td>
    <td width="50%" valign="top">
      <picture>
        <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/healthchainai/HealthChain/main/docs/assets/images/cards/hc-card-fhir-dark.svg">
        <img src="https://raw.githubusercontent.com/healthchainai/HealthChain/main/docs/assets/images/cards/hc-card-fhir-light.svg" alt="Structured output goes through validate_resource, which reports any FHIR issues to correct" width="100%">
      </picture>
      <div align="center">
        <br>
        <a href="https://healthchainai.github.io/HealthChain/reference/utilities/fhir_helpers/"><strong>🔥 Build and Validate FHIR</strong></a>
        <br><br>
        <div>Build typed resources without hand-writing deeply nested FHIR. Structured validation identifies failing fields and invalid required codes before delivery.</div><br>
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
        <a href="https://healthchainai.github.io/HealthChain/reference/utilities/tools/"><strong>🤖 Use the Same Tools with Agents</strong></a>
        <br><br>
        <div>Expose the same build, validate, read, and terminology operations over MCP or LangChain, with structured errors an agent can inspect and correct.</div><br>
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
        <a href="https://healthchainai.github.io/HealthChain/cookbook/fhir_qa/"><strong>💬 Build FHIR-Backed Applications</strong></a>
        <br><br>
        <div>Use live or local FHIR data in research software, patient-facing applications, analytics, decision support, and AI-assisted workflows.</div><br>
        <a href="https://healthchainai.github.io/HealthChain/cookbook/fhir_qa/">Getting Started →</a>
        <br><br>
      </div>
    </td>
  </tr>
</table>

## Why HealthChain?

Every healthcare data team rebuilds the same integration layer. Whether your logic is rule-based, a logistic regression, or an agent, it needs authenticated access to real FHIR APIs and a reliable way to turn output into coded FHIR. Pipelines tied to one site's warehouse don't travel, and structural or coding errors may only be discovered downstream.

HealthChain handles that layer so you can focus on your logic and your domain.

- **Live data, not exports** — Connect to live FHIR APIs instead of site-specific warehouse queries and stale extracts
- **Keep connection details out of pipeline logic** — Load endpoints and credentials from environment-backed configuration
- **Build FHIR with less boilerplate** — Use flat, typed helpers instead of manually assembling deeply nested resources
- **Catch errors early** — Get structured validation reports with failing field paths and actionable diagnostics
- **Resolve codes instead of guessing them** — Map free text through a swappable terminology lookup before building a resource
- **Choose how to deliver the result** — Expose output through FHIR REST services, CDS Hooks, SOAP/CDA, MCP, or LangChain

## 🏆 Recognition & Community

**Featured & Presented:**

- Featured in [TLDR AI Newsletter](https://tldr.tech/ai/2025-08-21) (900K+ developers)
- [Featured by Medplum](https://www.medplum.com/blog/healthchain) for open source integration with Epic
- Presented at [NHS Python Open Source Conference](https://github.com/nhs-r-community/conference-2024/blob/main/Talks/2024-11-21_jiang-kells_building-healthchain.md) ([watch talk](https://www.youtube.com/watch?v=_ZqlPsDUdSY&t=1967s))
- [Built from NHS AI deployment experience](https://open.substack.com/pub/jenniferjiangkells/p/healthchain-building-the-tool-i-wish) – read the origin story

## 🤝 Pilots & Partnerships

Exploring HealthChain for your product or organization? [Get in touch](mailto:jenniferjiangkells@gmail.com) to discuss integrations, pilots, or collaborations, or join our [Discord](https://discord.gg/UQC6uAepUz) to connect with the community.

## Usage Examples

### Build a FHIR Service

#### Expose Multiple FHIR Sources [[Docs](https://healthchainai.github.io/HealthChain/reference/gateway/gateway)]

```python
from healthchain.gateway import HealthChainAPI, FHIRGateway
from healthchain.gateway.clients import FHIRAuthConfig
from healthchain.fhir.r4b import Bundle, Patient

# Create a FHIR-connected service
app = HealthChainAPI(title="Multi-EHR Patient Data")

# Credentials are loaded from EPIC_* and CERNER_* environment variables
fhir = FHIRGateway()
fhir.add_source("epic", FHIRAuthConfig.from_env("EPIC").to_connection_string())
fhir.add_source("cerner", FHIRAuthConfig.from_env("CERNER").to_connection_string())

@fhir.aggregate(Patient)
def patient_data(id: str, source: str) -> Bundle:
    """Fetch patient data from any configured FHIR source."""
    bundle = fhir.search(
        Patient,
        {"_id": id},
        source,
        add_provenance=True,
        provenance_tag="healthchain-source",
    )
    return bundle

app.register_gateway(fhir)

# Available at: GET /fhir/aggregate/Patient?id=123&sources=epic&sources=cerner

if __name__ == "__main__":
    app.run(port=8888)
```

#### Scaffold with the CLI

Turn a working pipeline into a configurable FHIR service:

```bash
healthchain new my-app -t fhir-gateway
cd my-app
healthchain serve
```

<div align="center">
  <img src="https://raw.githubusercontent.com/healthchainai/HealthChain/main/docs/assets/images/demo.gif" alt="HealthChain CLI scaffolding and running a FHIR Gateway service" width="700">
</div>

Add your logic in `app.py`. Use `healthchain.yaml` to configure FHIR sources and service settings while keeping credentials in environment variables. See the [CLI reference](https://healthchainai.github.io/HealthChain/cli/) for all commands.

### Agent and Assistant Workflows

#### Give an Agent FHIR Tools [[Docs](https://healthchainai.github.io/HealthChain/reference/utilities/tools/)]

```python
from healthchain.tools import FHIRToolkit

# One toolkit: build, validate, read, and code FHIR — as typed agent tools
kit = FHIRToolkit(bundle="patient_bundle.json")

kit.as_mcp().run()          # serve to Claude or any MCP client
tools = kit.as_langchain()  # or drop into a LangChain agent
```

Or serve the tools straight from the terminal:

```bash
healthchain mcp --bundle patient_bundle.json
```

#### Build with an AI Assistant

Install the HealthChain plugin to give Claude Code or Codex the current API, CLI, and recipes:

```text
# Claude Code
/plugin marketplace add healthchainai/HealthChain
/plugin install healthchain@healthchain

# Codex
codex plugin marketplace add healthchainai/HealthChain
codex plugin add healthchain@healthchain
```

Or point any assistant at [llms.txt](https://healthchainai.github.io/HealthChain/llms.txt) for a map of the current API docs.

## 🛣️ What we're building towards

- 🔌 **Deeper FHIR connectivity** — more authentication patterns, write workflows, and real-world examples from pilot deployments
- 🧪 **Broader validation** — cover more resource types and value-set bindings, with clearer correction reports and optional server-backed profile validation
- 🧭 **Terminology integrations** — connect the `TerminologyLookup` interface to FHIR terminology servers and licensed vocabularies
- 🔎 **Traceable data movement** — carry provenance, validation results, and source errors through transformations and downstream delivery
- 🧱 **Reusable data workflows** — strengthen the patterns for moving research extracts, claims, and application data behind consistent FHIR interfaces

## 🤝 Contributing

- **Building research software or working with healthcare data?** [Contribute a cookbook](https://github.com/healthchainai/HealthChain/issues/208) — bring your use case, and I'll personally support you through it
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
