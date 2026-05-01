# Security & Data Handling

This page answers the most common information governance questions from NHS Trusts, academic hospitals, and research institutions evaluating HealthChain for clinical AI projects.

---

## Does HealthChain process or store patient data?

**No.** HealthChain is a Python SDK. It provides the scaffolding to build clinical AI workflows — it does not host services, transmit data, or store anything. All data handling happens entirely within your own infrastructure and environment.

When you build an application using HealthChain:

- Patient data **never leaves your environment**
- HealthChain does not connect to any external servers or telemetry services
- No data is sent to the HealthChain maintainers or any third party

---

## HIPAA Compliance

HealthChain does not transmit, store, or process Protected Health Information (PHI). The SDK operates entirely within the environment where it is deployed. No HealthChain service, telemetry, or dependency makes external calls with patient data.

Your organisation is responsible for ensuring that the infrastructure on which HealthChain-based applications run is appropriately hardened and HIPAA-compliant. HealthChain does not introduce additional HIPAA risk.

---

## GDPR Compliance

HealthChain is a software library, not a data processor. As such:

- HealthChain itself is not subject to GDPR as a data processor
- Your organisation, as the controller of any patient data processed using HealthChain, retains full responsibility for GDPR compliance
- Because HealthChain processes no data itself and has no external network calls, it introduces no additional GDPR risk surface

If your information governance team requires confirmation of any of the above, feel free to direct them to this page or contact [jenniferjiangkells@gmail.com](mailto:jenniferjiangkells@gmail.com).

---

## NHS Data Security and Protection Toolkit (DSPT)

HealthChain is a software library and does not have its own DSPT registration. However, because HealthChain introduces no external data flows, its use does not create new data-sharing agreements or processing activities that would require separate DSPT entries.

For NHS Trusts building HealthChain-based tools that will process patient data, the DSPT obligations remain with the Trust's own infrastructure and deployment environment.

---

## Dependency Security

HealthChain's dependencies are declared in `pyproject.toml` and locked in `uv.lock`. To audit dependencies for known vulnerabilities:

```bash
uv run pip-audit
```

Security issues in dependencies are addressed as part of the normal release cycle. Critical vulnerabilities are patched in a hotfix release.

---

## Reporting a Vulnerability

If you discover a security vulnerability in HealthChain, please **do not open a public GitHub issue**. Instead, email [jenniferjiangkells@gmail.com](mailto:jenniferjiangkells@gmail.com) with the subject line `[SECURITY] Vulnerability Report`.

We aim to acknowledge reports within 2 working days and to issue a patch or mitigation within 14 days of confirmation.

---

## Questions

For IG queries, penetration test evidence requests, or data flow documentation for your organisation's approval process, contact [jenniferjiangkells@gmail.com](mailto:jenniferjiangkells@gmail.com).
