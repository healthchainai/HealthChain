# HealthChain plugin for Claude Code

Gives Claude the HealthChain API and CLI so it can build a working healthcare AI service without reading the docs site first.

## Install

```
/plugin marketplace add healthchainai/HealthChain
/plugin install healthchain@healthchain
```

Then ask Claude to build something — a FHIR gateway, a validated FHIR write, an MCP server over a patient bundle. The skill loads on its own when the task involves FHIR, EHR APIs, or clinical data.

Requires `pip install healthchain` in the project you are working on.

Docs: https://healthchainai.github.io/HealthChain/
