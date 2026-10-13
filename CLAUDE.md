# HealthChain - Claude Code Context

> **Purpose**: This file guides AI assistants and developers working on HealthChain. It encodes coding standards, constraints, and workflows to keep architecture and domain judgment in human hands. It's a working document that will be updated as the project evolves.

## 0. Project Overview

HealthChain is an open-source Python library for live FHIR connectivity and validated FHIR tooling. It connects Python pipelines and applications to FHIR APIs, helps them produce coded, validated FHIR, and delivers results through healthcare and agent interfaces.

**Key Problem**: Healthcare data applications are often tied to one site's schemas and connection logic, while structural and coding errors may surface only after FHIR reaches a downstream system. HealthChain provides a consistent FHIR boundary around user-owned logic.

**Target Users** (in priority order):
- Research software and healthcare data teams building reusable tools, studies, and data services
- Healthcare integration engineers working across research organizations, hospitals, payers, and health technology companies
- AI, agent, and general Python developers building healthcare and personal health applications

For more background, read README.md and docs/index.md.

---

## 1. Non-Negotiable Golden Rules

| # | AI *may* do | AI *must NOT* do |
|---|-------------|------------------|
| G-0 | When unsure about implementation details or requirements, ask developer for clarification before making changes. | ❌ Write changes or use tools when you are not sure about something project specific, or if you don't have context for a particular feature/decision. |
| G-1 | Generate code inside `healthchain/` or explicitly pointed files. | ❌ Modify or create test files without explicit approval. |
| G-2 | For changes >200 LOC or >3 files, propose a plan and wait for confirmation. | ❌ Refactor large modules without human guidance. |
| G-3 | Follow lint/style configs (`pyproject.toml`, `.ruff.toml`). Use `ruff` for formatting. | ❌ Reformat code to any other style. |
| G-4 | Stay within the current task context. Inform the dev if it'd be better to start afresh. | ❌ Continue work from a prior prompt after "new task" – start a fresh session. |

---

## 2. Testing Discipline

| What | AI CAN Do | AI MUST NOT Do |
|------|-----------|----------------|
| Implementation | Generate business logic | Write new tests without confirmation |
| Test Planning | Suggest test scenarios and coverage gaps | Implement test code during design phase |
| Debugging | Analyze test failures and suggest fixes | Modify test expectations without approval |

**Key principle**: Tests encode business requirements and human intent. AI assistance is welcome for suggestions, maintenance, and execution, but new test creation always requires explicit confirmation.

---

## 3. Coding Standards

- **Python**: 3.10-3.13, prefer sync for legacy EHR compatibility; async available for modern systems but use only when explicitly needed
- **Dependencies**: NumPy must stay <2.0.0 (spaCy compatibility)
- **Environment**: Use `uv` for all development tasks — manage dependencies and run commands with `uv run <command>`
- **Dependency security**: Vulnerability fixes arrive via Dependabot security PRs; CI runs `pip-audit` advisory-only on PRs. Run `uv run pip-audit` locally for a full on-demand check.
- **Formatting**: `ruff` enforces project style
- **Typing**: Always use explicit type hints, even for obvious types; Pydantic v2 models for external data
- **Naming**:
  - Code: `snake_case` (functions/vars), `PascalCase` (classes), `SCREAMING_SNAKE` (constants)
  - Files: No underscores, e.g., `fhiradapter.py` not `fhir_adapter.py`
- **Error Handling**: Prefer specific exceptions over generic
- **Documentation**: Docstrings for public APIs only
- **Healthcare Standards**: Follow HL7 FHIR and CDS Hooks specifications
- **Testing**: Separate test files matching source file patterns. Use flat functions instead of classes for tests.

---

## 4. Core Components

### Key Modules (When to Use What)

| Module | Purpose |
|--------|---------|
| `pipeline/` | Document/patient NLP with `Pipeline[T]` generics |
| `gateway/` | EHR connectivity and protocol handling (CDS Hooks, FHIR APIs, SOAP/CDA) |
| `fhir/` | FHIR resource utilities (fhir.resources models) and helpers |
| `interop/` | Format conversion with Liquid templates + YAML (FHIR ↔ CDA, etc.) |
| `io/` | **Containers**: FHIR-aware structures<br>**Mappers**: semantic mapping (ML features, OMOP)<br>**Adapters**: interface with external formats (CDA, CSV) |
| `sandbox/` | Testing client for healthcare services (CDS Hooks, SOAP) & dataset loaders for common test datasets (MIMIC-IV on FHIR, Synthea, etc.) |

---

## 5. Common Workflows

### AI Assistant Workflow

When responding to user instructions, follow this process:

1. **Consult Relevant Guidance**: Review this CLAUDE.md and relevant patterns in @healthchain/ for the request. Look up relevant files, information, best practices, etc. using the internet or tools if necessary.
2. **Clarify Ambiguities**: If anything is unclear, ask targeted questions before proceeding. Don't make assumptions about business logic or domain requirements.
3. **Break Down & Plan**:
   - Break down, think through the problem, and create a rough plan
   - Reference project conventions and best practices
   - **Before proposing new APIs or abstractions**: check what comparable libraries in the Python/healthcare ecosystem do first. HealthChain is a healthcare abstraction layer designed to complement existing stacks (FastAPI, LangChain, HuggingFace, spaCy, etc.) — not replace them. Users plug HealthChain into tools they already know, so familiar idioms (context managers, decorators, method chaining) should be the default. Never reinvent patterns that already exist upstream. Bespoke APIs are only justified when the healthcare domain genuinely has no prior art (e.g. FHIR-specific concepts). When presenting a proposal, name the prior art explicitly so the developer can make an informed decision (e.g. "FastAPI does X, LangServe does Y, I'm proposing Z because...").
   - **Trivial tasks**: Start immediately
   - **Non-trivial tasks** (>200 LOC or >3 files): Present plan → wait for user confirmation
4. **Execute**:
   - Make small, focused diffs
   - Prefer existing abstractions over new ones
   - Run: `uv run ruff check . --fix && uv run ruff format .`
   - If stuck, return to step 3 to re-plan
5. **Review**: Summarize files changed, key design decisions, and any follow-ups or TODOs. Always check:
   - **Tests**: Do any existing tests need updating? Are there gaps worth flagging?
   - **Docs**: Do any doc pages, docstrings, or examples need updating?
   - **Cookbooks**: Do any cookbook examples need updating to reflect the change?
6. **Session Boundaries**: If request isn't related to current context, suggest starting fresh to avoid confusion

### Committing Changes

When the developer is ready to commit, AI should:
1. Run the review checklist from step 5 above — flag anything outstanding
2. Run `git status` and `git diff` to identify what's changed
3. Group changes into logical commits if needed (e.g. don't mix a feature with a test infra change)
4. Suggest which files to stage for each commit
5. Propose a commit message following [Conventional Commits](https://www.conventionalcommits.org/) style
6. Let the developer review and run the actual `git commit` themselves — AI never runs `git commit` or `git push`

### Writing Cookbook Examples

Follow the principles in [CONTRIBUTING.md — Writing Cookbooks](../CONTRIBUTING.md#writing-cookbooks). Key rule: reduce time-to-running above all else — pre-bake demo data, collapse advanced setup, and lead with the problem the cookbook solves.

### Adding New FHIR Resource Utilities

1. Check for existing utilities in @healthchain/fhir/
2. If missing, ask: "Create utility function for [ResourceType]?"
3. Follow pattern: MINIMUM VIABLE resource, all variable data as parameters
4. Avoid overly specific utilities; prefer generic

---

**Last updated**: 2026-10-06
