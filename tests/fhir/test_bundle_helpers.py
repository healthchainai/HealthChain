"""Tests for FHIR Bundle helper functions."""

from pathlib import Path

import pytest
from fhir.resources.R4B.bundle import Bundle, BundleEntry
from fhir.resources.R4B.condition import Condition
from fhir.resources.R4B.medicationstatement import MedicationStatement
from fhir.resources.R4B.allergyintolerance import AllergyIntolerance
from fhir.resources.R4B.documentreference import DocumentReference
from fhir.resources.R4B.patient import Patient
from fhir.resources.R4B.reference import Reference

from healthchain.fhir.bundlehelpers import (
    create_bundle,
    add_resource,
    get_resources,
    resolve_reference,
    set_resources,
    get_resource_type,
    extract_resources,
)
from healthchain.fhir import load_bundle, merge_bundles, create_condition

REFERENCE_BUNDLE_PATH = (
    Path(__file__).resolve().parent.parent / "data" / "test_reference_bundle.json"
)


@pytest.fixture
def reference_bundle():
    """Loads the Synthea-style reference-resolution fixture bundle.

    A transaction bundle with urn:uuid fullUrls exercising every branch of
    ``resolve_reference``: contained refs, urn:uuid fullUrls, relative Type/id
    refs, and an absolute-fullUrl Organization.
    """
    return load_bundle(REFERENCE_BUNDLE_PATH)


def test_create_bundle():
    """Test creating an empty bundle."""
    bundle = create_bundle()
    assert isinstance(bundle, Bundle)
    assert bundle.type == "collection"
    assert bundle.entry == []

    # Test with different type
    bundle = create_bundle(bundle_type="transaction")
    assert bundle.type == "transaction"


def test_add_resource(empty_bundle, test_condition):
    """Test adding a resource to a bundle."""
    add_resource(empty_bundle, test_condition)
    assert len(empty_bundle.entry) == 1
    assert isinstance(empty_bundle.entry[0].resource, Condition)

    # Test with full URL
    add_resource(empty_bundle, test_condition, full_url="http://test.com/Condition/123")
    assert len(empty_bundle.entry) == 2
    assert empty_bundle.entry[1].fullUrl == "http://test.com/Condition/123"


def test_get_resource_type():
    """Test getting resource type from string or class."""
    # Test with string
    assert get_resource_type("Condition") == Condition
    assert get_resource_type("MedicationStatement") == MedicationStatement
    assert get_resource_type("AllergyIntolerance") == AllergyIntolerance
    assert get_resource_type("DocumentReference") == DocumentReference
    # Test with class
    assert get_resource_type(Condition) == Condition

    # Test invalid type
    with pytest.raises(ValueError, match="Could not import resource type"):
        get_resource_type("InvalidType")

    # Test invalid input type
    with pytest.raises(
        ValueError, match="Resource type must be a string or Resource class"
    ):
        get_resource_type(123)


def test_get_resources(empty_bundle, test_condition, test_medication, test_allergy):
    """Test getting resources by type."""
    # Add mixed resources
    add_resource(empty_bundle, test_condition)
    add_resource(empty_bundle, test_medication)
    add_resource(empty_bundle, test_allergy)
    add_resource(empty_bundle, test_condition)  # Add another condition

    # Test getting by string type
    conditions = get_resources(empty_bundle, "Condition")
    assert len(conditions) == 2
    assert all(isinstance(c, Condition) for c in conditions)

    # Test getting by class type
    medications = get_resources(empty_bundle, MedicationStatement)
    assert len(medications) == 1
    assert isinstance(medications[0], MedicationStatement)


def test_set_resources_append(empty_bundle, test_condition, test_medication):
    """Test setting resources with append mode."""
    # Add initial condition
    add_resource(empty_bundle, test_condition)
    assert len(get_resources(empty_bundle, "Condition")) == 1

    # Add more conditions without replace
    set_resources(empty_bundle, [test_condition], "Condition", replace=False)
    assert len(get_resources(empty_bundle, "Condition")) == 2

    # Add medication (shouldn't affect conditions)
    set_resources(empty_bundle, [test_medication], "MedicationStatement")
    assert len(get_resources(empty_bundle, "Condition")) == 2
    assert len(get_resources(empty_bundle, "MedicationStatement")) == 1


def test_set_resources_replace(empty_bundle, test_condition, test_medication):
    """Test setting resources with replace mode."""
    # Add initial resources
    add_resource(empty_bundle, test_condition)
    add_resource(empty_bundle, test_condition)
    assert len(get_resources(empty_bundle, "Condition")) == 2

    # Replace conditions
    set_resources(empty_bundle, [test_condition], "Condition", replace=True)
    assert len(get_resources(empty_bundle, "Condition")) == 1

    # Add medication (shouldn't affect conditions)
    set_resources(empty_bundle, [test_medication], "MedicationStatement", replace=True)
    assert len(get_resources(empty_bundle, "Condition")) == 1
    assert len(get_resources(empty_bundle, "MedicationStatement")) == 1


def test_set_resources_type_validation(empty_bundle, test_condition):
    """Test type validation in set_resources."""
    # Try to add condition as medication
    with pytest.raises(
        ValueError, match="Resource must be of type MedicationStatement"
    ):
        set_resources(empty_bundle, [test_condition], "MedicationStatement")


def test_merge_bundles_basic_and_type():
    """Merging combines entries and sets bundle type to collection by default."""
    b1 = create_bundle("searchset")
    add_resource(b1, create_condition(subject="Patient/123", code="E11.9"))
    add_resource(b1, create_condition(subject="Patient/123", code="I10"))

    b2 = create_bundle("searchset")
    add_resource(b2, create_condition(subject="Patient/123", code="J44.9"))

    merged = merge_bundles([b1, b2])
    assert merged.entry is not None and len(merged.entry) == 3
    assert merged.type == "collection"


def test_merge_bundles_deduplication_toggle():
    """Deduplication removes dups when True, keeps when False."""
    c1 = create_condition(subject="Patient/123", code="E11.9")
    c1.id = "cond-1"
    c1_dup = create_condition(subject="Patient/123", code="E11.9")
    c1_dup.id = "cond-1"

    b1 = create_bundle("searchset")
    add_resource(b1, c1)
    b2 = create_bundle("searchset")
    add_resource(b2, c1_dup)

    merged_dedupe = merge_bundles([b1, b2], deduplicate=True)
    assert merged_dedupe.entry is not None and len(merged_dedupe.entry) == 1

    merged_all = merge_bundles([b1, b2], deduplicate=False)
    assert merged_all.entry is not None and len(merged_all.entry) == 2


def test_merge_bundles_preserves_full_url_and_handles_empty_none():
    """Preserves fullUrl and handles empty/None bundles."""
    b1 = create_bundle("searchset")
    cond = create_condition(subject="Patient/123", code="E11.9")
    add_resource(b1, cond, full_url="http://example.com/Condition/123")

    b2 = create_bundle("searchset")  # empty

    merged = merge_bundles([b1, b2, None])
    assert merged.entry is not None and len(merged.entry) == 1
    assert merged.entry[0].fullUrl == "http://example.com/Condition/123"


def test_merge_bundles_customizations():
    """Supports custom bundle_type and custom dedupe_key semantics."""
    # custom bundle_type
    b = create_bundle("searchset")
    add_resource(b, create_condition(subject="Patient/123", code="E11.9"))
    merged_txn = merge_bundles([b], bundle_type="transaction")
    assert merged_txn.type == "transaction"

    # custom dedupe_key (keep both because ids differ)
    c1 = create_condition(subject="Patient/123", code="E11.9")
    c1.id = "id-1"
    c2 = create_condition(subject="Patient/123", code="E11.9")
    c2.id = "id-2"
    b1 = create_bundle("searchset")
    add_resource(b1, c1)
    b2 = create_bundle("searchset")
    add_resource(b2, c2)
    merged_custom_key = merge_bundles([b1, b2], deduplicate=True, dedupe_key="id")
    assert merged_custom_key.entry is not None and len(merged_custom_key.entry) == 2


def test_extract_resources_removes_and_returns():
    """extract_resources removes resources of a type and returns them."""
    b = create_bundle()
    c1 = create_condition(subject="Patient/1", code="E11.9")
    c2 = create_condition(subject="Patient/1", code="I10")
    add_resource(b, c1)
    add_resource(b, c2)
    extracted = extract_resources(b, "Condition")
    assert len(extracted) == 2
    assert b.entry == []


def test_merge_bundles_dedupe_missing_key_keeps_all():
    """Resources missing dedupe_key should not be collapsed when deduplicate=True."""
    b1 = create_bundle("searchset")
    b2 = create_bundle("searchset")
    c1 = create_condition(subject="Patient/1", code="E11.9")
    c1.id = None
    c2 = create_condition(subject="Patient/1", code="E11.9")
    c2.id = None
    add_resource(b1, c1)
    add_resource(b2, c2)
    merged = merge_bundles([b1, b2], deduplicate=True, dedupe_key="id")
    assert merged.entry is not None and len(merged.entry) == 2


# ########################################
# ######## resolve_reference #############
# ########################################


def test_reference_bundle_loads_cleanly():
    """The fixture bundle loads and validates via load_bundle (fixture check)."""
    bundle = load_bundle(REFERENCE_BUNDLE_PATH)
    assert isinstance(bundle, Bundle)
    assert bundle.type == "transaction"
    assert len(bundle.entry) == 6


def test_resolve_reference_contained(reference_bundle):
    """Contained (#id) refs resolve against the parent's contained list."""
    med_request = get_resources(reference_bundle, "MedicationRequest")[0]
    resolved = resolve_reference(
        reference_bundle, med_request.requester, parent=med_request
    )
    assert resolved is not None
    assert resolved.__class__.__name__ == "Practitioner"
    assert resolved.id == "requester-1"


def test_resolve_reference_contained_without_parent_returns_none(reference_bundle):
    """A contained ref cannot resolve without the owning parent resource."""
    assert resolve_reference(reference_bundle, "#requester-1") is None


def test_resolve_reference_contained_missing_id_returns_none(reference_bundle):
    """A contained ref to an id absent from parent.contained returns None."""
    med_request = get_resources(reference_bundle, "MedicationRequest")[0]
    assert resolve_reference(reference_bundle, "#nope", parent=med_request) is None


def test_resolve_reference_exact_full_url(reference_bundle):
    """An exact urn:uuid fullUrl match resolves the entry resource."""
    resolved = resolve_reference(
        reference_bundle, "urn:uuid:22222222-2222-2222-2222-222222222222"
    )
    assert resolved is not None
    assert resolved.__class__.__name__ == "Medication"
    assert resolved.id == "medication-1"


def test_resolve_reference_object_input_urn_via_full_url(reference_bundle):
    """A Reference element whose .reference is a urn resolves via fullUrl."""
    med_request = get_resources(reference_bundle, "MedicationRequest")[0]
    resolved = resolve_reference(reference_bundle, med_request.medicationReference)
    assert resolved is not None
    assert resolved.__class__.__name__ == "Medication"
    assert resolved.id == "medication-1"


def test_resolve_reference_type_id_relative(reference_bundle):
    """A relative Type/id ref matches a resource by type name and id.

    The Patient entry's fullUrl is a urn (not /Patient/patient-1), so only the
    type+id branch can resolve this.
    """
    resolved = resolve_reference(reference_bundle, "Patient/patient-1")
    assert resolved is not None
    assert isinstance(resolved, Patient)
    assert resolved.id == "patient-1"


def test_resolve_reference_type_id_against_absolute_full_url(reference_bundle):
    """A relative Type/id ref resolves the entry with a matching absolute fullUrl."""
    resolved = resolve_reference(reference_bundle, "Organization/org-1")
    assert resolved is not None
    assert resolved.__class__.__name__ == "Organization"
    assert resolved.id == "org-1"


def test_resolve_reference_full_url_tail_when_id_differs():
    """The fullUrl-tail branch resolves even when resource.id != the URL tail.

    Isolates the ``fullUrl.endswith('/Type/id')`` arm: the resource carries no
    matching id, so only the RESTful fullUrl base can resolve the relative ref.
    """
    bundle = create_bundle("searchset")
    patient = Patient()
    entry = BundleEntry(
        resource=patient, fullUrl="https://example.org/fhir/Patient/xyz"
    )
    bundle.entry = [entry]

    resolved = resolve_reference(bundle, "Patient/xyz")
    assert resolved is patient


def test_resolve_reference_urn_uuid_fallback_by_id(reference_bundle):
    """When no fullUrl matches, a urn:uuid ref falls back to matching by id."""
    # No entry has fullUrl 'urn:uuid:medication-1'; the Medication's id does.
    resolved = resolve_reference(reference_bundle, "urn:uuid:medication-1")
    assert resolved is not None
    assert resolved.__class__.__name__ == "Medication"
    assert resolved.id == "medication-1"


def test_resolve_reference_object_input_type_id():
    """A Reference element carrying a relative Type/id ref resolves by type+id."""
    bundle = create_bundle()
    condition = create_condition(subject="Patient/1", code="E11.9")
    condition.id = "cond-42"
    add_resource(bundle, condition)

    resolved = resolve_reference(bundle, Reference(reference="Condition/cond-42"))
    assert resolved is condition


def test_resolve_reference_unresolvable_returns_none(reference_bundle):
    """An unknown reference resolves to None without raising."""
    assert resolve_reference(reference_bundle, "Patient/does-not-exist") is None
    assert resolve_reference(reference_bundle, "urn:uuid:unknown") is None


def test_resolve_reference_empty_reference_returns_none(reference_bundle):
    """Empty or None reference strings resolve to None."""
    assert resolve_reference(reference_bundle, "") is None
    assert resolve_reference(reference_bundle, Reference()) is None


def test_resolve_reference_empty_bundle_returns_none():
    """Resolving against an empty bundle returns None."""
    assert resolve_reference(create_bundle(), "Patient/123") is None
