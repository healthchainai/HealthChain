When reviewing pull requests, evaluate whether the change may break compliance expectations from the source documents located in `/compliance/source-documents/`.

For each compliance issue:
- cite the source document;
- cite the most precise section or requirement you can identify;
- cite the impacted file and line;
- explain the negative impact introduced by the PR;
- suggest a concrete fix.

Do not invent requirement IDs or clause numbers.
If you cannot identify an exact requirement from the documents, say so explicitly.
Avoid generic code quality comments unless they affect compliance, security, auditability, privacy, access control, logging, retention, or data integrity.