import json

import pytest
from fhir.resources.R4B.bundle import Bundle
from fhir.resources.R4B.condition import Condition
from fhir.resources.R4B.operationoutcome import OperationOutcome

from healthchain.fhir import (
    FHIRValidationError,
    ValidationReport,
    create_resource_from_dict,
    load_bundle,
    validate_resource,
)

VALID_CONDITION = {
    "resourceType": "Condition",
    "subject": {"reference": "Patient/123"},
    "code": {"text": "Hypertension"},
}

VALID_MEDICATION_STATEMENT = {
    "resourceType": "MedicationStatement",
    "status": "active",
    "subject": {"reference": "Patient/123"},
    "medicationCodeableConcept": {"text": "Aspirin"},
}


def test_validate_resource_valid_dict():
    """A structurally valid resource dict produces a clean report."""
    report = validate_resource(VALID_CONDITION)

    assert report.valid is True
    assert report.resource_type == "Condition"
    assert report.fhir_version == "R4B"
    assert report.issues == []


def test_validate_resource_structural_errors():
    """Invalid payload for a valid type reports issues with expressions."""
    report = validate_resource(
        {
            "resourceType": "Condition",
            "onsetDateTime": "not-a-date",
            "bogusField": 1,
        }
    )

    assert report.valid is False
    issues_by_expression = {issue.expression: issue for issue in report.issues}
    assert issues_by_expression["Condition.subject"].code == "required"
    assert issues_by_expression["Condition.bogusField"].code == "structure"
    assert issues_by_expression["Condition.onsetDateTime"].code == "value"
    assert all(issue.severity == "error" for issue in report.issues)


def test_validate_resource_binding_violation():
    """A code outside a required binding is caught even though Pydantic accepts it."""
    report = validate_resource({**VALID_MEDICATION_STATEMENT, "status": "recorded"})

    assert report.valid is False
    assert len(report.issues) == 1
    issue = report.issues[0]
    assert issue.code == "code-invalid"
    assert issue.expression == "MedicationStatement.status"
    assert "'recorded'" in issue.diagnostics
    assert "active" in issue.diagnostics


def test_validate_resource_binding_version_aware():
    """'recorded' is invalid R4B vocabulary but valid R5 vocabulary."""
    r5_statement = {
        "resourceType": "MedicationStatement",
        "status": "recorded",
        "subject": {"reference": "Patient/123"},
        "medication": {"concept": {"text": "Aspirin"}},
    }
    report = validate_resource(r5_statement, version="R5")

    assert report.valid is True
    assert report.fhir_version == "R5"


def test_validate_resource_missing_resource_type():
    """A dict without resourceType and no resource_type argument is fatal."""
    report = validate_resource({"subject": {"reference": "Patient/123"}})

    assert report.valid is False
    assert report.issues[0].severity == "fatal"
    assert report.issues[0].code == "structure"


def test_validate_resource_unknown_resource_type():
    """An unknown resource type reports not-supported."""
    report = validate_resource({"resourceType": "NotAType"})

    assert report.valid is False
    assert report.issues[0].severity == "fatal"
    assert report.issues[0].code == "not-supported"
    assert report.resource_type == "NotAType"


def test_validate_resource_explicit_type_argument():
    """resource_type argument works for dicts without a resourceType key."""
    resource = {k: v for k, v in VALID_CONDITION.items() if k != "resourceType"}
    report = validate_resource(resource, resource_type="Condition")

    assert report.valid is True
    assert report.resource_type == "Condition"


def test_validate_resource_model_instance():
    """An instantiated resource validates, including binding checks."""
    condition = Condition.model_validate(VALID_CONDITION)
    report = validate_resource(condition)

    assert report.valid is True
    assert report.resource_type == "Condition"
    assert report.fhir_version == "R4B"


def test_validate_resource_model_instance_binding_violation():
    """Binding checks run on model instances, catching spec-invalid codes."""
    from fhir.resources.R4B.medicationstatement import MedicationStatement

    statement = MedicationStatement.model_validate(
        {**VALID_MEDICATION_STATEMENT, "status": "recorded"}
    )
    report = validate_resource(statement)

    assert report.valid is False
    assert report.issues[0].code == "code-invalid"
    assert report.issues[0].expression == "MedicationStatement.status"


def test_validation_report_serializes_to_json():
    """Reports are JSON-serializable for agent tool output."""
    report = validate_resource({"resourceType": "Condition"})
    dumped = json.loads(report.model_dump_json())

    assert dumped["valid"] is False
    assert dumped["resource_type"] == "Condition"
    assert dumped["issues"][0]["expression"] == "Condition.subject"


def test_validation_report_to_operation_outcome():
    """Reports convert to FHIR OperationOutcome resources."""
    report = validate_resource({"resourceType": "Condition"})
    outcome = report.to_operation_outcome()

    assert isinstance(outcome, OperationOutcome)
    assert outcome.issue[0].severity == "error"
    assert outcome.issue[0].code == "required"
    assert outcome.issue[0].expression == ["Condition.subject"]


def test_validation_report_to_operation_outcome_valid():
    """A valid report converts to an informational OperationOutcome."""
    report = validate_resource(VALID_CONDITION)
    outcome = report.to_operation_outcome()

    assert outcome.issue[0].severity == "information"
    assert outcome.issue[0].code == "informational"


def test_load_bundle_from_dict():
    """A valid bundle dict loads into a Bundle instance."""
    bundle = load_bundle(
        {
            "resourceType": "Bundle",
            "type": "collection",
            "entry": [{"resource": VALID_CONDITION}],
        }
    )

    assert isinstance(bundle, Bundle)
    assert type(bundle.entry[0].resource).__name__ == "Condition"


def test_load_bundle_from_json_string_and_file(tmp_path):
    """Bundles load from JSON strings and file paths."""
    bundle_json = json.dumps(
        {
            "resourceType": "Bundle",
            "type": "collection",
            "entry": [{"resource": VALID_MEDICATION_STATEMENT}],
        }
    )

    from_string = load_bundle(bundle_json)
    assert isinstance(from_string, Bundle)

    bundle_file = tmp_path / "bundle.json"
    bundle_file.write_text(bundle_json)
    from_path = load_bundle(bundle_file)
    assert isinstance(from_path, Bundle)
    from_str_path = load_bundle(str(bundle_file))
    assert isinstance(from_str_path, Bundle)


def test_load_bundle_aggregates_entry_errors():
    """Errors across multiple entries are aggregated with entry-indexed expressions."""
    bad_bundle = {
        "resourceType": "Bundle",
        "type": "collection",
        "entry": [
            {"resource": VALID_CONDITION},
            {"resource": {"resourceType": "Condition", "onsetDateTime": "bad"}},
            {"resource": {**VALID_MEDICATION_STATEMENT, "status": "recorded"}},
        ],
    }

    with pytest.raises(FHIRValidationError) as exc_info:
        load_bundle(bad_bundle)

    report = exc_info.value.report
    assert report.valid is False
    expressions = [issue.expression for issue in report.issues]
    assert "Bundle.entry[1].resource.subject" in expressions
    assert "Bundle.entry[1].resource.onsetDateTime" in expressions
    assert "Bundle.entry[2].resource.status" in expressions


def test_load_bundle_rejects_non_bundle():
    """A resource that isn't a Bundle raises with a fatal issue."""
    with pytest.raises(FHIRValidationError) as exc_info:
        load_bundle(VALID_CONDITION)

    report = exc_info.value.report
    assert report.issues[0].severity == "fatal"
    assert "Condition" in report.issues[0].diagnostics


def test_load_bundle_rejects_malformed_json():
    """Malformed JSON raises FHIRValidationError, not JSONDecodeError."""
    with pytest.raises(FHIRValidationError) as exc_info:
        load_bundle('{"resourceType": "Bundle",')

    assert exc_info.value.report.issues[0].code == "structure"


def test_load_bundle_missing_file():
    """A nonexistent file path raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_bundle("/nonexistent/bundle.json")


def test_create_resource_from_dict_raise_on_error():
    """raise_on_error=True raises FHIRValidationError carrying the report."""
    with pytest.raises(FHIRValidationError) as exc_info:
        create_resource_from_dict(
            {"onsetDateTime": "bad"}, "Condition", raise_on_error=True
        )

    report = exc_info.value.report
    assert isinstance(report, ValidationReport)
    assert report.valid is False
    assert any(issue.expression == "Condition.subject" for issue in report.issues)


def test_create_resource_from_dict_default_still_returns_none():
    """Default behavior is unchanged: failures return None."""
    assert create_resource_from_dict({"onsetDateTime": "bad"}, "Condition") is None


def test_create_resource_from_dict_raise_on_error_valid_input():
    """raise_on_error=True does not affect successful creation."""
    resource = create_resource_from_dict(
        VALID_CONDITION, "Condition", raise_on_error=True
    )

    assert isinstance(resource, Condition)
