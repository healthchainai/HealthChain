import json
from pathlib import Path

import pytest

from healthchain.fhir import (
    CodedEntry,
    get_coded_entries,
    get_medications,
    load_bundle,
)

FIXTURE_PATH = Path(__file__).parent.parent / "data" / "test_reference_bundle.json"


@pytest.fixture
def reference_bundle():
    return load_bundle(FIXTURE_PATH)


def _bundle_of(*resources: dict):
    return load_bundle(
        {
            "resourceType": "Bundle",
            "type": "collection",
            "entry": [{"resource": r} for r in resources],
        }
    )


def test_get_coded_entries_condition():
    """Conditions flatten to code/display/system with clinicalStatus as status."""
    bundle = _bundle_of(
        {
            "resourceType": "Condition",
            "id": "c1",
            "subject": {"reference": "Patient/123"},
            "clinicalStatus": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                        "code": "active",
                    }
                ]
            },
            "code": {
                "coding": [
                    {
                        "system": "http://snomed.info/sct",
                        "code": "38341003",
                        "display": "Hypertension",
                    }
                ]
            },
            "recordedDate": "2024-01-15T09:00:00Z",
        }
    )

    entries = get_coded_entries(bundle, "Condition")

    assert len(entries) == 1
    entry = entries[0]
    assert entry.code == "38341003"
    assert entry.display == "Hypertension"
    assert entry.system == "http://snomed.info/sct"
    assert entry.status == "active"
    assert entry.resource_type == "Condition"
    assert entry.resource_id == "c1"
    assert entry.subject == "Patient/123"
    assert entry.authored_on == "2024-01-15T09:00:00+00:00"


def test_get_coded_entries_status_filter_clinical_status():
    """The status filter matches clinicalStatus for condition-shaped types."""
    active = {
        "resourceType": "Condition",
        "subject": {"reference": "Patient/123"},
        "clinicalStatus": {"coding": [{"code": "active"}]},
        "code": {"coding": [{"code": "111"}]},
    }
    resolved = {
        "resourceType": "Condition",
        "subject": {"reference": "Patient/123"},
        "clinicalStatus": {"coding": [{"code": "resolved"}]},
        "code": {"coding": [{"code": "222"}]},
    }
    bundle = _bundle_of(active, resolved)

    entries = get_coded_entries(bundle, "Condition", status="active")

    assert [entry.code for entry in entries] == ["111"]


def test_get_coded_entries_multiple_types():
    """A list of types returns entries grouped in the requested type order."""
    bundle = _bundle_of(
        {
            "resourceType": "MedicationStatement",
            "status": "active",
            "subject": {"reference": "Patient/123"},
            "medicationCodeableConcept": {"coding": [{"code": "313782"}]},
        },
        {
            "resourceType": "Condition",
            "subject": {"reference": "Patient/123"},
            "code": {"coding": [{"code": "38341003"}]},
        },
    )

    entries = get_coded_entries(bundle, ["Condition", "MedicationStatement"])

    assert [entry.resource_type for entry in entries] == [
        "Condition",
        "MedicationStatement",
    ]


def test_get_coded_entries_all_codings_kept():
    """code/display/system come from the first coding; codings keeps all."""
    bundle = _bundle_of(
        {
            "resourceType": "Condition",
            "subject": {"reference": "Patient/123"},
            "code": {
                "coding": [
                    {"system": "http://snomed.info/sct", "code": "38341003"},
                    {"system": "http://hl7.org/fhir/sid/icd-10-cm", "code": "I10"},
                ]
            },
        }
    )

    entry = get_coded_entries(bundle, "Condition")[0]

    assert entry.code == "38341003"
    assert len(entry.codings) == 2
    assert entry.codings[1].code == "I10"
    assert entry.codings[1].system == "http://hl7.org/fhir/sid/icd-10-cm"


def test_get_coded_entries_text_only_concept():
    """A concept with text but no codings yields a display-only entry."""
    bundle = _bundle_of(
        {
            "resourceType": "Condition",
            "subject": {"reference": "Patient/123"},
            "code": {"text": "Headache"},
        }
    )

    entry = get_coded_entries(bundle, "Condition")[0]

    assert entry.code is None
    assert entry.display == "Headache"


def test_get_coded_entries_skips_resources_without_coded_identity():
    """Resources with no code and no text are skipped, not returned empty."""
    bundle = _bundle_of(
        {
            "resourceType": "Condition",
            "subject": {"reference": "Patient/123"},
        }
    )

    assert get_coded_entries(bundle, "Condition") == []
    assert get_coded_entries(bundle, "Patient") == []


def test_get_coded_entries_observation_value():
    """Value-bearing Observations carry value/unit and effective date."""
    bundle = _bundle_of(
        {
            "resourceType": "Observation",
            "status": "final",
            "code": {
                "coding": [
                    {
                        "system": "http://loinc.org",
                        "code": "8480-6",
                        "display": "Systolic blood pressure",
                    }
                ]
            },
            "subject": {"reference": "Patient/123"},
            "effectiveDateTime": "2024-02-01T08:30:00Z",
            "valueQuantity": {"value": 140, "unit": "mmHg"},
        }
    )

    entry = get_coded_entries(bundle, "Observation")[0]

    assert entry.code == "8480-6"
    assert entry.status == "final"
    assert entry.value == 140.0
    assert entry.unit == "mmHg"
    assert entry.authored_on == "2024-02-01T08:30:00+00:00"


def test_get_coded_entries_resolves_medication_reference(reference_bundle):
    """medicationReference resolves to the bundled Medication's code."""
    entries = get_coded_entries(reference_bundle, "MedicationRequest")

    assert len(entries) == 1
    entry = entries[0]
    assert entry.code == "313782"
    assert entry.display == "Acetaminophen 325 MG Oral Tablet"
    assert entry.system == "http://www.nlm.nih.gov/research/umls/rxnorm"
    assert entry.status == "active"
    assert entry.subject == "urn:uuid:11111111-1111-1111-1111-111111111111"


def test_get_coded_entries_resolves_contained_medication():
    """medicationReference to a contained Medication resolves via parent."""
    bundle = _bundle_of(
        {
            "resourceType": "MedicationStatement",
            "status": "active",
            "subject": {"reference": "Patient/123"},
            "medicationReference": {"reference": "#med-1"},
            "contained": [
                {
                    "resourceType": "Medication",
                    "id": "med-1",
                    "code": {"coding": [{"code": "197361", "display": "Amlodipine"}]},
                }
            ],
        }
    )

    entry = get_coded_entries(bundle, "MedicationStatement")[0]

    assert entry.code == "197361"
    assert entry.display == "Amlodipine"


def test_get_coded_entries_unresolvable_medication_reference_skipped():
    """A medication with an unresolvable reference has no identity and is skipped."""
    bundle = _bundle_of(
        {
            "resourceType": "MedicationStatement",
            "status": "active",
            "subject": {"reference": "Patient/123"},
            "medicationReference": {"reference": "Medication/nowhere"},
        }
    )

    assert get_coded_entries(bundle, "MedicationStatement") == []


def test_get_medications_spans_both_types(reference_bundle):
    """get_medications covers MedicationStatement and MedicationRequest."""
    statement_bundle = _bundle_of(
        {
            "resourceType": "MedicationStatement",
            "status": "active",
            "subject": {"reference": "Patient/123"},
            "medicationCodeableConcept": {"coding": [{"code": "197361"}]},
        },
        {
            "resourceType": "MedicationRequest",
            "status": "stopped",
            "intent": "order",
            "subject": {"reference": "Patient/123"},
            "medicationCodeableConcept": {"coding": [{"code": "313782"}]},
        },
    )

    medications = get_medications(statement_bundle)
    assert {med.code for med in medications} == {"197361", "313782"}

    active_only = get_medications(statement_bundle, status="active")
    assert [med.code for med in active_only] == ["197361"]

    fixture_medications = get_medications(reference_bundle)
    assert [med.code for med in fixture_medications] == ["313782"]


def test_coded_entry_serializes_to_json(reference_bundle):
    """CodedEntry records are JSON-serializable for agent tool output."""
    entry = get_medications(reference_bundle)[0]

    dumped = json.loads(entry.model_dump_json())

    assert dumped["code"] == "313782"
    assert dumped["resource_type"] == "MedicationRequest"
    assert isinstance(dumped["codings"], list)
    assert isinstance(entry, CodedEntry)
