# Copilot Code Review Instructions

When reviewing pull requests, evaluate whether the changes may negatively impact compliance, security, privacy, auditability, interoperability, or operational reliability.

Use the source documents located in:

`/compliance/source-documents/`

For each compliance-relevant issue:

- cite the source document;
- cite the most precise section, requirement, or heading you can identify;
- cite the impacted file and line;
- explain why the PR introduces a negative impact;
- suggest a concrete fix.

Do not invent requirement IDs, clause numbers, or references.

If you cannot identify an exact requirement or section from the documents, say so explicitly.

Avoid generic code quality comments unless they directly affect compliance, security, privacy, auditability, interoperability, or operational reliability.

Prefer fewer, high-confidence findings over speculative ones.