# Installation

Install HealthChain with `pip`:

```bash
pip install healthchain
```

The core install is deliberately lean — type-safe FHIR, gateways, the agent toolkit, and the CLI, with no ML or NLP frameworks attached. Optional capabilities ship as extras:

| Extra       | Installs                     | When you need it                                                       |
| ----------- | ---------------------------- | ---------------------------------------------------------------------- |
| `cda`       | `python-liquid`, `xmltodict` | CDA parsing and NoteReader integration (`CdaAdapter`, interop engine)  |
| `mcp`       | `mcp`                        | Serving the `FHIRToolkit` over MCP (`kit.as_mcp()`, `healthchain mcp`) |
| `langchain` | `langchain-core`             | `FHIRToolkit.as_langchain()` for LangChain agents                      |
| `sandbox`   | `faker`                      | Synthetic FHIR test data generators for the sandbox client             |
| `examples`  | `spacy`, `transformers`      | Running the NLP/ML cookbook examples                                   |

```bash
pip install "healthchain[cda,mcp]"   # combine as needed
```

Bring your own model framework and use it directly in pipeline nodes. Each [cookbook](https://healthchainai.github.io/HealthChain/cookbook/index.md) states the exact install line it needs, including any model-specific dependencies (e.g. `torch`).

## Give your AI assistant the API

Claude Code users can install the HealthChain plugin, which teaches Claude the current API, the CLI verbs, and the recipes:

```text
/plugin marketplace add healthchainai/HealthChain
/plugin install healthchain@healthchain
```

Codex users can install the same skill from the repository marketplace:

```text
codex plugin marketplace add healthchainai/HealthChain
codex plugin add healthchain@healthchain
```

Any other assistant can read [llms.txt](https://healthchainai.github.io/HealthChain/llms.txt) for a map of the API docs.
