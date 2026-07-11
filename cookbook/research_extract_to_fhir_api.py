#!/usr/bin/env python3
"""
From Research Database Extract to Validated FHIR API

You have an extract from a research database — rows of patients, diagnoses,
and lab values pulled from a data warehouse. To use it beyond one-off analysis
(dashboards, downstream apps, multi-site studies), it needs to become validated
FHIR behind a real API. This example does exactly that: turn extract rows into
typed FHIR resources, catch the dirty data before it ships, and load it all
into a FHIR server you can query like any EHR.

Bring your own extract. This script uses pre-baked rows so it runs offline with
zero setup — no database, no credentials. Swap in your own query results and
the rest is unchanged.

Requirements:
- pip install healthchain

Run:
    python cookbook/research_extract_to_fhir_api.py
    # Builds and validates FHIR resources from extract rows, saves a Bundle.
    # Set MEDPLUM_* env vars to also load them into a live FHIR server.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

from healthchain.fhir import (
    add_resource,
    create_bundle,
    create_condition,
    create_patient,
    create_value_quantity_observation,
    validate_resource,
)

load_dotenv()


# --- Your extract ------------------------------------------------------------
# Rows as they come out of a data warehouse: local conventions ("M"/"F" sex
# codes), one record per line. Note row 3: sex arrived as "U" — real extracts
# always have at least one value that doesn't fit the standard.
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
    {
        "mrn": "MRN-002",
        "sex": "F",
        "birth_date": "1948-07-02",
        "dx_code": "42343007",
        "dx_display": "Congestive heart failure",
        "lab_loinc": "33762-6",
        "lab_display": "NT-proBNP",
        "lab_value": 1890.0,
        "lab_unit": "pg/mL",
    },
    {
        "mrn": "MRN-003",
        "sex": "U",  # <- doesn't map to a FHIR administrative gender
        "birth_date": "1961-12-19",
        "dx_code": "13645005",
        "dx_display": "Chronic obstructive pulmonary disease",
        "lab_loinc": "19926-5",
        "lab_display": "FEV1/FVC",
        "lab_value": 0.62,
        "lab_unit": "%",
    },
]

# Local warehouse codes -> FHIR administrative gender. Deliberately incomplete,
# like every real mapping table.
SEX_MAP = {"M": "male", "F": "female"}


def build_and_validate():
    """Turn extract rows into validated FHIR resources, collected in a Bundle.

    Every resource is validated before it enters the bundle. When a local code
    doesn't fit the FHIR spec, the validator names the exact field — that's the
    strict schema working as a unit test for your data.
    """
    bundle = create_bundle()

    for row in EXTRACT_ROWS:
        # warn=False: we validate explicitly below instead of relying on log warnings
        patient = create_patient(
            gender=SEX_MAP.get(row["sex"], row["sex"]),
            birth_date=row["birth_date"],
            identifier=row["mrn"],
            warn=False,
        )

        report = validate_resource(patient)
        if not report.valid:
            for issue in report.issues:
                print(f"  CAUGHT {row['mrn']}: {issue.diagnostics}")
            # Fix the mapping gap and re-validate — never ship an invalid resource
            patient.gender = "unknown"
            report = validate_resource(patient)
            assert report.valid

        patient_ref = f"Patient/{patient.id}"

        condition = create_condition(
            subject=patient_ref,
            code=row["dx_code"],
            display=row["dx_display"],
            warn=False,
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
            report = validate_resource(resource)
            assert report.valid, report.issues
            add_resource(bundle, resource)

        print(f"  OK {row['mrn']}: Patient + Condition + Observation validated")

    return bundle


def load_to_fhir_server(bundle):
    """Optionally load the validated resources into a live FHIR server.

    This is the payoff: your extract becomes a queryable FHIR API. Configure a
    source with credentials and the gateway writes each resource; afterwards
    the data answers standard FHIR queries (e.g. GET /Patient?identifier=MRN-001)
    from any FHIR client — no more emailing CSVs.
    """
    from healthchain.gateway import FHIRGateway
    from healthchain.gateway.clients import FHIRAuthConfig

    gateway = FHIRGateway()
    gateway.add_source(
        "medplum", FHIRAuthConfig.from_env("MEDPLUM").to_connection_string()
    )

    for entry in bundle.entry:
        created = gateway.create(entry.resource, source="medplum")
        print(f"  wrote {created.__class__.__name__}/{created.id} to medplum")


if __name__ == "__main__":
    print("Building validated FHIR from extract rows:\n")
    bundle = build_and_validate()

    print(f"\nBundle contains {len(bundle.entry)} validated resources.")

    # Save the Bundle — already a useful artifact for sharing or loading later.
    out_path = Path("./output/research_extract_bundle.json")
    out_path.parent.mkdir(exist_ok=True)
    out_path.write_text(bundle.model_dump_json(exclude_none=True, indent=2))
    print(f"Saved to {out_path}")

    # Take it live: load into a FHIR server if configured.
    if os.getenv("MEDPLUM_CLIENT_ID"):
        print("\n=== Loading into Medplum ===")
        load_to_fhir_server(bundle)
    else:
        print("\nSet MEDPLUM_* env vars to load these into a live FHIR server.")
