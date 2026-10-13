# Security

## Does HealthChain store patient data?

**No, not by default.** HealthChain does not include a patient-data database
or managed storage service. FHIR resources and documents normally pass
transiently through application memory for the duration of a request,
workflow, or tool session.

Data is stored only when the application or operator configures a persistent
destination, such as a FHIR write, saved file, application log, retained
object, or external service that stores requests.

## Can I use HealthChain with real patient data?

**Yes, within an appropriately approved application and environment.**
HealthChain can process real FHIR resources and clinical documents, but the
library does not itself grant permission to use patient data or make the
resulting application compliant.

Before using real data, your organization must approve the purpose, access,
configured endpoints, hosting, security controls, logging, retention, and any
required information-governance or clinical-safety review. Use synthetic data
for development and examples until those approvals and controls are in place.
Never include real patient data in public repositories, issues, cookbooks, or
support requests.

## Does HealthChain send patient data outside my environment?

**Not to the HealthChain maintainers.** The library has no HealthChain-hosted
data service and does not collect telemetry.

It does connect to endpoints that the application explicitly configures,
including FHIR servers, terminology services, and model providers. Whether
those endpoints are inside or outside your environment depends on your
configuration.

## Is HealthChain HIPAA compliant?

HealthChain does not provide or claim HIPAA compliance. It is a software
library rather than a hosted service or compliance product. The absence of a
built-in patient datastore may simplify the application's data-flow review,
but the organization remains responsible for assessing the complete
application, infrastructure, access controls, integrations, and operating
processes.

## Is HealthChain GDPR compliant?

HealthChain does not provide or claim GDPR compliance. Using the library does
not by itself send data to the HealthChain maintainers, but the roles and
obligations associated with a HealthChain application depend on how it is
configured, deployed, and used. The deploying organization remains
responsible for establishing an appropriate lawful basis, data flows,
retention, security, and data-subject processes.

## Does HealthChain have an NHS DSPT registration?

No. HealthChain is an open-source software library and does not have its own
NHS Data Security and Protection Toolkit registration. NHS organizations must
assess HealthChain as part of the application and infrastructure in which it
is used.

## Detailed Data Boundary

HealthChain runs inside the application and infrastructure where it is
installed. During a request or workflow it can read, transform, validate, and
transmit health data between components selected by the application. Any
persistence comes from application code, configured destinations, or external
services—not from a HealthChain patient database.

The optional built-in audit log records request metadata rather than request
or response bodies. Its path field can still contain identifiers, so it must
be included in the application's data-flow and retention review.

This transient-by-default boundary is relevant to information-governance
assessment, but the deployed application's data flows and security properties
are still determined by its code, configuration, dependencies, and
infrastructure.

## Security Configuration

HealthChain provides configurable API-key authentication, request audit
logging, and TLS support for services built with `HealthChainAPI`. These are
application controls, not a compliance certification or a complete security
programme. See the [security configuration
documentation](https://healthchainai.github.io/HealthChain/security/) for
their behavior and limitations.

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
