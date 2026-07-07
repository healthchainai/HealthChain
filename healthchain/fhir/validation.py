"""FHIR resource validation.

This module provides an explicit validation surface for FHIR resources:
a report-returning ``validate_resource`` suitable for agent tool loops,
a raising ``load_bundle`` for loading bundles from files or dicts, and
the ``ValidationReport``/``FHIRValidationError`` types they share.

What IS checked:
- Structure: field types, required fields, and unknown fields, as enforced
  by the underlying ``fhir.resources`` Pydantic models.
- Required bindings on primitive ``code`` fields: values are checked against
  the value set shipped with the model metadata (e.g. ``MedicationStatement.status``).

What is NOT checked:
- Bindings on CodeableConcept/Coding fields (no ValueSet expansion is bundled).
- FHIRPath invariants/constraints (e.g. "co-33: only one onset[x]").
- Profile conformance (e.g. US Core, UK Core).
- Reference integrity (whether referenced resources exist).

For full conformance validation, use a FHIR server's ``$validate`` operation
against the relevant profiles.
"""

import json
import logging

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, ValidationError
from fhir.resources.resource import Resource

from healthchain.fhir.version import (
    FHIRVersion,
    get_default_version,
    get_fhir_resource,
    get_resource_version,
)

logger = logging.getLogger(__name__)


# Maps Pydantic error types to OperationOutcome issue type codes
# https://www.hl7.org/fhir/valueset-issue-type.html
_PYDANTIC_ERROR_TO_ISSUE_CODE = {
    "missing": "required",
    "extra_forbidden": "structure",
}


class ValidationIssue(BaseModel):
    """A single validation issue, mirroring FHIR OperationOutcome.issue fields.

    https://www.hl7.org/fhir/operationoutcome.html
    """

    severity: str = Field(
        description="Issue severity: fatal | error | warning | information"
    )
    code: str = Field(
        description="OperationOutcome issue type code, e.g. structure, required, "
        "value, code-invalid, not-supported"
    )
    diagnostics: str = Field(description="Human-readable description of the issue")
    expression: Optional[str] = Field(
        default=None,
        description="Path to the offending element, e.g. 'Condition.onsetDateTime'",
    )


class ValidationReport(BaseModel):
    """Result of validating a FHIR resource.

    JSON-serializable via ``model_dump()`` so it can be returned directly
    from agent tools. Convert to a FHIR OperationOutcome resource with
    ``to_operation_outcome()``.
    """

    valid: bool = Field(description="True if no error or fatal issues were found")
    resource_type: Optional[str] = Field(
        default=None, description="The FHIR resource type that was validated"
    )
    fhir_version: Optional[str] = Field(
        default=None, description="The FHIR version validated against, e.g. 'R4B'"
    )
    issues: List[ValidationIssue] = Field(default_factory=list)

    def to_operation_outcome(self) -> Resource:
        """Convert the report to a FHIR OperationOutcome resource.

        Returns:
            An OperationOutcome of the report's FHIR version, with one issue
            per validation issue (or a single 'informational' issue if valid).
        """
        outcome_class = get_fhir_resource("OperationOutcome", self.fhir_version)
        issues: List[Dict[str, Any]] = [
            {
                "severity": issue.severity,
                "code": issue.code,
                "diagnostics": issue.diagnostics,
                **({"expression": [issue.expression]} if issue.expression else {}),
            }
            for issue in self.issues
        ]
        if not issues:
            issues = [
                {
                    "severity": "information",
                    "code": "informational",
                    "diagnostics": "Validation successful",
                }
            ]
        return outcome_class(issue=issues)


class FHIRValidationError(Exception):
    """Raised when FHIR validation fails. Carries the full ValidationReport."""

    def __init__(self, report: ValidationReport, message: Optional[str] = None):
        self.report = report
        if message is None:
            summary = "; ".join(
                f"{issue.expression or issue.code}: {issue.diagnostics}"
                for issue in report.issues[:3]
            )
            count = len(report.issues)
            message = (
                f"Validation failed for {report.resource_type or 'resource'} "
                f"with {count} issue{'s' if count != 1 else ''}: {summary}"
            )
            if count > 3:
                message += f" (and {count - 3} more)"
        super().__init__(message)


def _format_expression(resource_type: str, loc: tuple) -> str:
    """Format a Pydantic error location as a FHIRPath-style expression.

    Example: ("entry", 0, "resource", "subject") -> "Bundle.entry[0].resource.subject"
    """
    expression = resource_type
    for part in loc:
        if isinstance(part, int):
            expression += f"[{part}]"
        else:
            expression += f".{part}"
    return expression


def _structural_issues(
    error: ValidationError, resource_type: str
) -> List[ValidationIssue]:
    """Convert a Pydantic ValidationError into validation issues."""
    return [
        ValidationIssue(
            severity="error",
            code=_PYDANTIC_ERROR_TO_ISSUE_CODE.get(err["type"], "value"),
            diagnostics=err["msg"],
            expression=_format_expression(resource_type, err["loc"]),
        )
        for err in error.errors()
    ]


def _check_bindings(model: BaseModel, path: str) -> List[ValidationIssue]:
    """Recursively check primitive code fields against their required bindings.

    Walks model fields looking for ``enum_values`` in each field's
    ``json_schema_extra`` metadata (shipped by fhir.resources for required
    bindings on code-typed fields) and reports values outside the value set.
    """
    issues: List[ValidationIssue] = []
    for name, field in type(model).model_fields.items():
        value = getattr(model, name, None)
        if value is None:
            continue

        alias = field.alias or name
        extra = field.json_schema_extra
        enum_values = extra.get("enum_values") if isinstance(extra, dict) else None

        if enum_values:
            values = value if isinstance(value, list) else [value]
            for i, item in enumerate(values):
                if isinstance(item, str) and item not in enum_values:
                    expression = f"{path}.{alias}"
                    if isinstance(value, list):
                        expression += f"[{i}]"
                    issues.append(
                        ValidationIssue(
                            severity="error",
                            code="code-invalid",
                            diagnostics=(
                                f"Value '{item}' is not in the required value set. "
                                f"Allowed values: {', '.join(enum_values)}"
                            ),
                            expression=expression,
                        )
                    )
        elif isinstance(value, BaseModel):
            issues.extend(_check_bindings(value, f"{path}.{alias}"))
        elif isinstance(value, list):
            for i, item in enumerate(value):
                if isinstance(item, BaseModel):
                    issues.extend(_check_bindings(item, f"{path}.{alias}[{i}]"))
    return issues


def _class_version(resource_class: type) -> str:
    """Detect the FHIR version of a resource class from its module path."""
    module = resource_class.__module__
    if ".R4B." in module:
        return FHIRVersion.R4B.value
    elif ".STU3." in module:
        return FHIRVersion.STU3.value
    return FHIRVersion.R5.value


def validate_resource(
    resource: Union[Dict[str, Any], Resource],
    resource_type: Optional[str] = None,
    version: Optional[Union[FHIRVersion, str]] = None,
) -> ValidationReport:
    """Validate a FHIR resource and return a report. Never raises.

    Runs structural validation (types, required fields, unknown fields) and
    checks primitive code fields against their required bindings. Binding
    issues are only reported once structural validation passes. See the
    module docstring for exactly what is and is not checked.

    Args:
        resource: A dict representation or an instantiated FHIR resource
        resource_type: Resource type name (e.g. "Condition"). Optional if the
            dict has a "resourceType" key or the input is already a resource
        version: FHIR version to validate against (default: session default).
            Ignored for instantiated resources, which carry their own version

    Returns:
        ValidationReport: ``valid`` is True when no error/fatal issues exist

    Example:
        >>> report = validate_resource({"resourceType": "Condition"})
        >>> report.valid
        False
        >>> report.issues[0].expression
        'Condition.subject'
    """
    if isinstance(resource, dict):
        resolved_type = resource_type or resource.get("resourceType")
        if not resolved_type:
            return ValidationReport(
                valid=False,
                fhir_version=None,
                issues=[
                    ValidationIssue(
                        severity="fatal",
                        code="structure",
                        diagnostics=(
                            "Cannot determine resource type: no 'resourceType' key "
                            "in the dict and no resource_type argument provided"
                        ),
                    )
                ],
            )

        try:
            resource_class = get_fhir_resource(resolved_type, version)
        except ValueError as e:
            requested = version if version is not None else get_default_version()
            return ValidationReport(
                valid=False,
                resource_type=resolved_type,
                fhir_version=requested.value
                if isinstance(requested, FHIRVersion)
                else str(requested).upper(),
                issues=[
                    ValidationIssue(
                        severity="fatal", code="not-supported", diagnostics=str(e)
                    )
                ],
            )

        fhir_version = _class_version(resource_class)
        try:
            instance = resource_class.model_validate(resource)
        except ValidationError as e:
            return ValidationReport(
                valid=False,
                resource_type=resolved_type,
                fhir_version=fhir_version,
                issues=_structural_issues(e, resolved_type),
            )
    else:
        resolved_type = resource.__class__.__name__
        detected = get_resource_version(resource)
        fhir_version = detected.value if detected else None
        try:
            # Re-validate to catch invalid post-construction mutations
            resource.__class__.model_validate(resource.model_dump(exclude_none=True))
        except ValidationError as e:
            return ValidationReport(
                valid=False,
                resource_type=resolved_type,
                fhir_version=fhir_version,
                issues=_structural_issues(e, resolved_type),
            )
        instance = resource

    issues = _check_bindings(instance, resolved_type)
    valid = not any(issue.severity in ("error", "fatal") for issue in issues)
    return ValidationReport(
        valid=valid,
        resource_type=resolved_type,
        fhir_version=fhir_version,
        issues=issues,
    )


def load_bundle(
    source: Union[str, Path, Dict[str, Any]],
    version: Optional[Union[FHIRVersion, str]] = None,
) -> Resource:
    """Load and validate a FHIR Bundle, raising on any validation error.

    Validates the bundle structure and every entry resource, aggregating all
    issues into a single report rather than failing on the first error.
    Issue expressions locate the offending entry, e.g.
    ``Bundle.entry[2].resource.subject``. See the module docstring for
    exactly what is and is not checked.

    Args:
        source: A file path, a JSON string, or a dict representation of a Bundle
        version: FHIR version to validate against (default: session default)

    Returns:
        Bundle: The validated Bundle instance

    Raises:
        FHIRValidationError: If parsing or validation fails; carries the
            full ValidationReport in ``.report``
        FileNotFoundError: If a file path is given but does not exist

    Example:
        >>> bundle = load_bundle("synthea_patient.json")
        >>> try:
        ...     bundle = load_bundle({"resourceType": "Bundle", "entry": [...]})
        ... except FHIRValidationError as e:
        ...     print(e.report.model_dump())
    """
    if isinstance(source, Path):
        data = _parse_bundle_json(source.read_text())
    elif isinstance(source, str):
        if source.lstrip().startswith("{"):
            data = _parse_bundle_json(source)
        else:
            data = _parse_bundle_json(Path(source).read_text())
    elif isinstance(source, dict):
        data = source
    else:
        raise TypeError(
            f"source must be a file path, JSON string, or dict, got {type(source)}"
        )

    resource_type = data.get("resourceType")
    if resource_type != "Bundle":
        raise FHIRValidationError(
            ValidationReport(
                valid=False,
                resource_type=resource_type,
                issues=[
                    ValidationIssue(
                        severity="fatal",
                        code="structure",
                        diagnostics=(
                            f"Expected resourceType 'Bundle', got '{resource_type}'"
                        ),
                        expression="Bundle.resourceType",
                    )
                ],
            )
        )

    # Validate the bundle skeleton and each entry resource independently, so
    # a structural error in one entry doesn't mask issues in the others
    issues: List[ValidationIssue] = []
    entries = data.get("entry") or []
    skeleton = {
        **data,
        "entry": [
            {k: v for k, v in entry.items() if k != "resource"}
            if isinstance(entry, dict)
            else entry
            for entry in entries
        ],
    }
    skeleton_report = validate_resource(
        skeleton, resource_type="Bundle", version=version
    )
    issues.extend(skeleton_report.issues)

    for i, entry in enumerate(entries):
        if not isinstance(entry, dict):
            continue  # reported by the skeleton validation above
        entry_resource = entry.get("resource")
        if entry_resource is None:
            continue
        entry_report = validate_resource(entry_resource, version=version)
        prefix = f"Bundle.entry[{i}].resource"
        for issue in entry_report.issues:
            # Rebase the expression from the entry's resource type onto the bundle path
            suffix = ""
            if issue.expression and "." in issue.expression:
                suffix = "." + issue.expression.split(".", 1)[1]
            issues.append(issue.model_copy(update={"expression": prefix + suffix}))

    report = ValidationReport(
        valid=not any(issue.severity in ("error", "fatal") for issue in issues),
        resource_type="Bundle",
        fhir_version=skeleton_report.fhir_version,
        issues=issues,
    )
    if not report.valid:
        raise FHIRValidationError(report)

    bundle_class = get_fhir_resource("Bundle", version)
    return bundle_class.model_validate(data)


def _parse_bundle_json(text: str) -> Dict[str, Any]:
    """Parse bundle JSON, raising FHIRValidationError on malformed input."""
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise FHIRValidationError(
            ValidationReport(
                valid=False,
                issues=[
                    ValidationIssue(
                        severity="fatal",
                        code="structure",
                        diagnostics=f"Invalid JSON: {e}",
                    )
                ],
            )
        ) from e
    if not isinstance(data, dict):
        raise FHIRValidationError(
            ValidationReport(
                valid=False,
                issues=[
                    ValidationIssue(
                        severity="fatal",
                        code="structure",
                        diagnostics=f"Expected a JSON object, got {type(data).__name__}",
                    )
                ],
            )
        )
    return data
