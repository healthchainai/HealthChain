"""Tests for FHIR converter helpers.

Covers prefetch_to_bundle, which flattens CDS Hooks prefetch payloads into a
collection Bundle.
"""

from healthchain.fhir import prefetch_to_bundle


def test_prefetch_to_bundle_flattens_cds_prefetch():
    """prefetch_to_bundle converts CDS Hooks prefetch to collection bundle."""
    prefetch = {
        "patient": {"resourceType": "Patient", "id": "123", "gender": "male"},
        "heart_rate": {
            "resourceType": "Bundle",
            "type": "searchset",
            "entry": [
                {
                    "resource": {
                        "resourceType": "Observation",
                        "code": {"coding": [{"code": "8867-4"}]},
                        "valueQuantity": {"value": 85.0},
                    }
                }
            ],
        },
    }

    bundle = prefetch_to_bundle(prefetch)

    assert bundle["type"] == "collection"
    assert len(bundle["entry"]) == 2
    # Patient should be wrapped in resource
    patient_entry = next(
        e
        for e in bundle["entry"]
        if e.get("resource", {}).get("resourceType") == "Patient"
    )
    assert patient_entry["resource"]["id"] == "123"


def test_prefetch_to_bundle_handles_empty_prefetch():
    """prefetch_to_bundle handles empty prefetch gracefully."""
    bundle = prefetch_to_bundle({})
    assert bundle["type"] == "collection"
    assert bundle["entry"] == []
