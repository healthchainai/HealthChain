# HealthChain plugins for Claude Code and Codex

Gives Claude Code and Codex the HealthChain API and CLI so they can build a working healthcare AI service without reading the docs site first. Both integrations use the same `skills/healthchain/` content.

## Install in Claude Code

```
/plugin marketplace add healthchainai/HealthChain
/plugin install healthchain@healthchain
```

Then ask Claude to build something — a FHIR gateway, a validated FHIR write, an MCP server over a patient bundle. The skill loads on its own when the task involves FHIR, EHR APIs, or clinical data.

Requires `pip install healthchain` in the project you are working on.

## Install in Codex

From the published repository marketplace:

```
codex plugin marketplace add healthchainai/HealthChain
codex plugin add healthchain@healthchain
```

For local development, point Codex at the repository's `.agents/plugins` marketplace directory instead:

```
codex plugin marketplace add /path/to/HealthChain/.agents/plugins
codex plugin add healthchain@healthchain
```

Start a new Codex thread after installing so it discovers the skill.

Docs: https://healthchainai.github.io/HealthChain/
