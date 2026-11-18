---
authors: [your-github-handle]  # everyone who wrote the page, including domain experts
date: YYYY-MM-DD  # first published
level: Beginner  # Beginner, Intermediate or Advanced
---

# [Cookbook Title]

[One or two sentences on the problem this solves — lead with the pain, not the code. E.g. "You have X data and need to do Y. This shows how to bridge that gap."]

Full working example: [cookbook/your_cookbook.py](https://github.com/healthchainai/HealthChain/tree/main/cookbook/your_cookbook.py)

---

## [Clinical / Research] Context

[Who has this problem and why it's hard, in domain terms. Follow one concrete example from the real workflow, ideally in words a domain expert wrote or approved. Assume no healthcare background: define each clinical term the first time it appears.]

### Workflow

[What the example does, end to end. A table from the domain task to the FHIR resources used and the output works well. Then list the steps in order, each labelled with who owns it:]

1. **Read** (HealthChain): [pull the records from a FHIR API or files]
2. **Compute** (project code): [the domain logic this cookbook is about]
3. **Return** (HealthChain): [serve or write back the result as FHIR]

---

## Quick Start

[Collapse setup if it requires external accounts — keep the zero-setup path front and centre if possible.]

```bash
pip install healthchain
python cookbook/your_cookbook.py
```

Expected output:

```
[paste real output here]
```

---

## How It Works

[Walk through the key steps. Lead with HealthChain's role — what would have been 50+ lines of custom code without it.]

### Step 1: Pull FHIR data

```python
# code snippet
```

### Step 2: Process

```python
# code snippet
```

### Step 3: Return as FHIR

```python
# code snippet
```

??? details "Advanced: [optional advanced path]"

    [Collapse anything that's not on the critical path for a first run.]

---

## What You've Built

[Short summary — one paragraph or a table. What does this enable, which parts does HealthChain handle versus the project's own code, and where could it go next?]

[Optional: add Next Steps only when there are concrete ones for this cookbook.]

!!! tip "Next Steps"

    - [Concrete next step 1]
    - **Turn it into a service**: Scaffold a project with `healthchain new` and run with `healthchain serve` — see [From cookbook to service](./index.md#from-cookbook-to-service).
