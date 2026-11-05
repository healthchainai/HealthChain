# Turn a Research Database Extract into a Validated FHIR API

**Level:** Beginner

You have an extract from a research database — rows of patients, diagnoses, and lab values pulled from a data warehouse. To use it beyond one-off analysis (dashboards, downstream apps, multi-site studies), it needs to become validated FHIR behind a real API. This example turns extract rows into typed FHIR resources, catches the dirty data before it ships, and loads it all into a FHIR server you can query like any EHR.

Check out the full working example [here](https://github.com/healthchainai/HealthChain/tree/main/cookbook/research_extract_to_fhir_api.py) — it runs offline with zero setup.

## Setup

```bash
pip install healthchain
```

That's it. The script uses pre-baked extract rows so there's no database or credentials to configure — swap in your own query results and the rest is unchanged.

## The Extract

Rows as they come out of a data warehouse: local conventions (`"M"`/`"F"` sex codes), one record per line. Note the third row — `sex` arrived as `"U"`, and real extracts always have at least one value that doesn't fit the standard.

```python
EXTRACT_ROWS = [
    {
        "mrn": "MRN-001",
        "sex": "M",
        "birth_date": "1954-03-11",
        "dx_code": "44054006",
        "dx_display": "Type 2 diabetes mellitus",
        "lab_loinc": "4548-4",
        "lab_display": "Hemoglobin A1c",
        "lab_value": 8.2,
        "lab_unit": "%",
    },
    # ... more rows, including one with sex="U"
]

# Local warehouse codes -> FHIR administrative gender. Deliberately incomplete,
# like every real mapping table.
SEX_MAP = {"M": "male", "F": "female"}
```

## Build and Validate

Each row becomes three typed FHIR resources using the [FHIR helpers](https://healthchainai.github.io/HealthChain/reference/utilities/fhir_helpers/index.md), and every resource is validated with [`validate_resource`](https://healthchainai.github.io/HealthChain/reference/utilities/fhir_helpers/index.md) before it enters the bundle:

```python
from healthchain.fhir import (
    add_resource,
    create_bundle,
    create_condition,
    create_patient,
    create_value_quantity_observation,
    validate_resource,
)

bundle = create_bundle()

for row in EXTRACT_ROWS:
    patient = create_patient(
        gender=SEX_MAP.get(row["sex"], row["sex"]),
        birth_date=row["birth_date"],
        identifier=row["mrn"],
        warn=False,  # we validate explicitly below
    )

    report = validate_resource(patient)
    if not report.valid:
        for issue in report.issues:
            print(f"CAUGHT {row['mrn']}: {issue.diagnostics}")
        patient.gender = "unknown"  # fix the mapping gap, never ship invalid data
        assert validate_resource(patient).valid

    patient_ref = f"Patient/{patient.id}"
    condition = create_condition(
        subject=patient_ref, code=row["dx_code"], display=row["dx_display"], warn=False
    )
    observation = create_value_quantity_observation(
        code=row["lab_loinc"],
        display=row["lab_display"],
        value=row["lab_value"],
        unit=row["lab_unit"],
        subject=patient_ref,
        warn=False,
    )

    for resource in (patient, condition, observation):
        assert validate_resource(resource).valid
        add_resource(bundle, resource)
```

Running it, the unmapped sex code is caught by the FHIR schema — with the exact field and allowed values named — instead of slipping silently into your dataset:

```text
OK MRN-001: Patient + Condition + Observation validated
OK MRN-002: Patient + Condition + Observation validated
CAUGHT MRN-003: Value 'u' is not in the required value set. Allowed values: male, female, other, unknown
OK MRN-003: Patient + Condition + Observation validated
```

That's the strict schema working as a built-in unit test for your data.

## Load into a FHIR Server

This is the payoff: your extract becomes a queryable FHIR API. Configure a source ([free Medplum sandbox setup →](https://healthchainai.github.io/HealthChain/cookbook/setup_fhir_sandboxes/#medplum)) and the [FHIRGateway](https://healthchainai.github.io/HealthChain/reference/gateway/fhir_gateway/index.md) writes each resource:

```python
from healthchain.gateway import FHIRGateway
from healthchain.gateway.clients import FHIRAuthConfig

gateway = FHIRGateway()
gateway.add_source(
    "medplum", FHIRAuthConfig.from_env("MEDPLUM").to_connection_string()
)

for entry in bundle.entry:
    created = gateway.create(entry.resource, source="medplum")
```

Afterwards the data answers standard FHIR queries from any FHIR client — no more emailing CSVs:

```bash
GET /Patient?identifier=MRN-001
GET /Observation?code=4548-4
GET /Condition?code=44054006
```

## What You've Built

- **Typed FHIR from tabular rows** — Patients, Conditions, and Observations built with minimal helpers, correctly coded (SNOMED CT, LOINC)
- **Validation as a gate** — broken data is caught and named before it ships, not discovered downstream
- **A real API** — your one-off extract is now infrastructure other tools, sites, and agents can query

Next Steps

- **Scale the input**: Replace `EXTRACT_ROWS` with your SQL query results or CSV reader — the build-and-validate loop is unchanged.
- **Add provenance**: Use `add_provenance_metadata` to tag resources with their source extract for auditability.
- **Serve it to agents**: Point the [FHIRToolkit](https://healthchainai.github.io/HealthChain/reference/utilities/tools/index.md) at your bundle or server to give LLM agents validated FHIR tools over the same data.
- **Aggregate across sites**: Combine with the [Multi-Source Data Aggregation](https://healthchainai.github.io/HealthChain/cookbook/multi_ehr_aggregation/index.md) pattern once more than one FHIR source is involved.
