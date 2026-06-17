---
template: welcome.html
hide:
  - navigation
  - toc
---

# Welcome to HealthChain

HealthChain is the shared infrastructure layer for healthcare AI: built-in FHIR support, real-time EHR connectivity, and production-ready deployment tooling. Stop building integration from scratch and focus on what actually matters: the model and the patient.

[ :fontawesome-brands-discord: Join our Discord](https://discord.gg/UQC6uAepUz){ .md-button .md-button--primary }
&nbsp;&nbsp;&nbsp;&nbsp;
[ :octicons-rocket-24: Quickstart Guide](quickstart.md){ .md-button .md-button--secondary }

## What are the main features?

<div class="grid cards" markdown>

-   :material-console:{ .lg .middle } __CLI & Deployment__

    ---

    Scaffold, configure, and serve healthcare AI apps with `healthchain new`, `healthchain.yaml`, and `healthchain serve`

    [:octicons-arrow-right-24: CLI](cli.md)

-   :material-connection:{ .lg .middle } __Multi-EHR Gateway__

    ---

    Connect to multiple FHIR sources and healthcare systems with a unified API

    [:octicons-arrow-right-24: Gateway](reference/gateway/gateway.md)

-   :material-robot:{ .lg .middle } __LLM & AI Model Integrations__

    ---

    Wire up any model — LangChain, HuggingFace, spaCy — to FHIR data pipelines with automatic output conversion

    [:octicons-arrow-right-24: Pipeline](reference/pipeline/pipeline.md)

-   :material-fire:{ .lg .middle } __Developer Utilities__

    ---

    Type-safe FHIR resources, validation helpers, and sandbox environments for rapid development

    [:octicons-arrow-right-24: Utilities](reference/utilities/fhir_helpers.md)

</div>

## Getting Started with Healthcare AI

Whether you're processing medical documents, deploying models as FHIR APIs, or connecting to multiple EHRs, these docs will guide you through:

- **🔧 Core concepts** - Understand FHIR resources, pipelines, and gateway patterns
- **📚 Real examples** - Step-by-step tutorials for common healthcare AI use cases
- **🏗️ Advanced patterns** - Production deployment, authentication, and multi-EHR workflows
- **🧪 Testing tools** - Sandbox environments and utilities for development

## What You Can Build with HealthChain

|   | Use Case                              | Description                                                                 |
|---|---------------------------------------|-----------------------------------------------------------------------------|
| 🔗 | **Multi-EHR patient aggregation**     | Combine patient records from Epic, Cerner, and specialty systems            |
| 🤖 | **ML model deployment**               | Serve your trained healthcare models as FHIR-compliant APIs                 |
| 📋 | **Automatic medical coding**          | Extract ICD-10 or SNOMED-CT codes from physician notes with confidence scores|
| 🚨 | **CDS alerts for discharge summaries** | Generate clinical recommendations directly in Epic workflows                |

**New to healthcare AI?** Start with our [Quickstart Guide](quickstart.md) to build your first medical NLP pipeline in under 10 minutes.

**Ready to integrate with EHRs?** Jump to our [Cookbook](cookbook/index.md) for complete examples.

---

Built by developers who have hit the same integration wall. For inquiries and collaborations, [get in touch](mailto:jenniferjiangkells@gmail.com).
