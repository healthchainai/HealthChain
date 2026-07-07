"""FHIR conversion and reading functions.

This module provides functions for converting between different FHIR representations
and reading data from FHIR resources.
"""

import logging
import re

from typing import Optional, Dict, Any, List, Union

from pydantic import BaseModel, Field
from fhir.resources.resource import Resource
from fhir.resources.R4B.bundle import Bundle
from fhir.resources.R4B.documentreference import DocumentReference

from healthchain.fhir.bundlehelpers import get_resources, resolve_reference
from healthchain.fhir.version import get_fhir_resource

logger = logging.getLogger(__name__)

_MEDICATION_TYPES = ("MedicationStatement", "MedicationRequest")
_CLINICAL_STATUS_TYPES = ("Condition", "AllergyIntolerance")
_DATE_FIELDS = ("authoredOn", "effectiveDateTime", "occurrenceDateTime", "recordedDate")


class EntryCoding(BaseModel):
    """A single coding (code/display/system) from a CodeableConcept."""

    code: Optional[str] = None
    display: Optional[str] = None
    system: Optional[str] = None


class CodedEntry(BaseModel):
    """Flattened coded identity of a clinical resource.

    JSON-serializable via ``model_dump()`` so it can be returned directly
    from agent tools. ``code``/``display``/``system`` come from the first
    coding; ``codings`` carries all of them.
    """

    code: Optional[str] = Field(
        default=None, description="Code from the first coding, if any"
    )
    display: Optional[str] = Field(
        default=None,
        description="Display from the first coding, falling back to the concept text",
    )
    system: Optional[str] = Field(
        default=None, description="Code system of the first coding, if any"
    )
    codings: List[EntryCoding] = Field(
        default_factory=list, description="All codings of the concept"
    )
    status: Optional[str] = Field(
        default=None,
        description="Resource status; for Condition/AllergyIntolerance this is "
        "the clinicalStatus code",
    )
    resource_type: str = Field(description="FHIR resource type of the entry")
    resource_id: Optional[str] = Field(default=None, description="Resource id")
    subject: Optional[str] = Field(
        default=None, description="Reference string of subject/patient, if any"
    )
    date: Optional[str] = Field(
        default=None,
        description="First of authoredOn/effectiveDateTime/occurrenceDateTime/"
        "recordedDate, ISO 8601",
    )
    value: Optional[float] = Field(
        default=None, description="valueQuantity.value for value-bearing resources"
    )
    unit: Optional[str] = Field(
        default=None, description="valueQuantity.unit for value-bearing resources"
    )


def _concept_codings(concept: Any) -> List[EntryCoding]:
    """Flatten a CodeableConcept into EntryCodings.

    A concept with text but no codings yields a single display-only entry.
    """
    if concept is None:
        return []
    text = getattr(concept, "text", None)
    codings = [
        EntryCoding(code=c.code, display=c.display or text, system=c.system)
        for c in (getattr(concept, "coding", None) or [])
    ]
    if not codings and text:
        codings = [EntryCoding(display=text)]
    return codings


def _resource_codings(bundle: Bundle, resource: Resource) -> List[EntryCoding]:
    """Extract the coded identity of a resource, resolving medication[x]."""
    if type(resource).__name__ in _MEDICATION_TYPES:
        codings = _concept_codings(getattr(resource, "medicationCodeableConcept", None))
        if not codings:
            medication_ref = getattr(resource, "medicationReference", None)
            if medication_ref is not None:
                target = resolve_reference(bundle, medication_ref, parent=resource)
                if target is not None:
                    codings = _concept_codings(getattr(target, "code", None))
        return codings
    return _concept_codings(getattr(resource, "code", None))


def _entry_status(resource: Resource) -> Optional[str]:
    """Read the status of a resource; clinicalStatus for condition-shaped types."""
    if type(resource).__name__ in _CLINICAL_STATUS_TYPES:
        codings = _concept_codings(getattr(resource, "clinicalStatus", None))
        return codings[0].code if codings else None
    return getattr(resource, "status", None)


def _entry_date(resource: Resource) -> Optional[str]:
    """Read the first available date field as an ISO 8601 string."""
    for field in _DATE_FIELDS:
        value = getattr(resource, field, None)
        if value is not None:
            return value.isoformat() if hasattr(value, "isoformat") else str(value)
    return None


def get_coded_entries(
    bundle: Bundle,
    resource_type: Union[str, List[str]],
    status: Optional[str] = None,
) -> List[CodedEntry]:
    """Read the flattened coded identity of resources in a bundle.

    The read-side counterpart to the ``create_*`` helpers: instead of walking
    nested CodeableConcepts by hand, get code/display/system/status and entry
    metadata as flat records. Medication resources are handled specially:
    ``medicationCodeableConcept`` is read directly, and ``medicationReference``
    is resolved to its target (bundled or contained) Medication.

    Resources with no coded identity at all (no codings and no concept text)
    are skipped.

    Args:
        bundle: The bundle to read
        resource_type: A resource type name or list of names
            (e.g. "Condition" or ["MedicationStatement", "MedicationRequest"])
        status: Only return entries with this status. For Condition and
            AllergyIntolerance this matches the clinicalStatus code

    Returns:
        List of CodedEntry records, in bundle order per requested type

    Example:
        >>> bundle = load_bundle("synthea_patient.json")
        >>> for entry in get_coded_entries(bundle, "Condition", status="active"):
        ...     print(entry.code, entry.display, entry.date)
        >>> meds = get_coded_entries(bundle, ["MedicationStatement", "MedicationRequest"])
    """
    types = [resource_type] if isinstance(resource_type, str) else list(resource_type)
    entries: List[CodedEntry] = []
    for type_name in types:
        for resource in get_resources(bundle, type_name):
            codings = _resource_codings(bundle, resource)
            if not codings:
                continue
            entry_status = _entry_status(resource)
            if status is not None and entry_status != status:
                continue
            subject = getattr(resource, "subject", None) or getattr(
                resource, "patient", None
            )
            quantity = getattr(resource, "valueQuantity", None)
            entries.append(
                CodedEntry(
                    code=codings[0].code,
                    display=codings[0].display,
                    system=codings[0].system,
                    codings=codings,
                    status=entry_status,
                    resource_type=type_name,
                    resource_id=getattr(resource, "id", None),
                    subject=getattr(subject, "reference", None) if subject else None,
                    date=_entry_date(resource),
                    value=float(quantity.value)
                    if quantity is not None and quantity.value is not None
                    else None,
                    unit=quantity.unit if quantity is not None else None,
                )
            )
    return entries


def get_medications(bundle: Bundle, status: Optional[str] = None) -> List[CodedEntry]:
    """Read all medications in a bundle as flat coded entries.

    Sugar over ``get_coded_entries`` spanning MedicationStatement and
    MedicationRequest, with ``medicationReference`` resolved within the bundle.

    Args:
        bundle: The bundle to read
        status: Only return medications with this status (e.g. "active")

    Returns:
        List of CodedEntry records for all medications found

    Example:
        >>> for med in get_medications(bundle, status="active"):
        ...     print(med.code, med.display, med.system)
    """
    return get_coded_entries(bundle, list(_MEDICATION_TYPES), status=status)


def _fix_timezone_naive_datetimes(data: Any) -> Any:
    """
    Recursively fix timezone-naive datetime strings by appending UTC timezone.

    Pydantic v2 requires timezone-aware datetimes. This function walks through
    nested dicts/lists and adds 'Z' (UTC) to datetime strings that match the
    pattern YYYY-MM-DDTHH:MM:SS but lack timezone info.

    Args:
        data: Dict, list, or primitive value to process

    Returns:
        Processed data with timezone-aware datetime strings

    Example:
        >>> data = {"start": "2021-04-19T00:00:00", "name": "Test"}
        >>> _fix_timezone_naive_datetimes(data)
        {"start": "2021-04-19T00:00:00Z", "name": "Test"}
    """
    # Pattern: YYYY-MM-DDTHH:MM:SS optionally followed by microseconds
    # Must NOT already have timezone (Z or +/-HH:MM)
    datetime_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?$")

    if isinstance(data, dict):
        return {
            key: _fix_timezone_naive_datetimes(value) for key, value in data.items()
        }
    elif isinstance(data, list):
        return [_fix_timezone_naive_datetimes(item) for item in data]
    elif isinstance(data, str) and datetime_pattern.match(data):
        # Add UTC timezone
        return f"{data}Z"
    else:
        return data


def create_resource_from_dict(
    resource_dict: Dict, resource_type: str, raise_on_error: bool = False
) -> Optional[Resource]:
    """Create a FHIR resource instance from a dictionary

    Args:
        resource_dict: Dictionary representation of the resource
        resource_type: Type of FHIR resource to create
        raise_on_error: If True, raise FHIRValidationError with a full
            ValidationReport instead of returning None on failure

    Returns:
        Optional[Resource]: FHIR resource instance or None if creation failed

    Raises:
        FHIRValidationError: If raise_on_error is True and validation fails
    """
    try:
        resource_class = get_fhir_resource(resource_type)
        return resource_class(**resource_dict)
    except Exception as e:
        if raise_on_error:
            from healthchain.fhir.validation import (
                FHIRValidationError,
                ValidationIssue,
                ValidationReport,
                validate_resource,
            )

            report = validate_resource(resource_dict, resource_type=resource_type)
            if report.valid:
                # The constructor failed for a reason validation didn't reproduce
                report = ValidationReport(
                    valid=False,
                    resource_type=resource_type,
                    issues=[
                        ValidationIssue(
                            severity="fatal", code="exception", diagnostics=str(e)
                        )
                    ],
                )
            raise FHIRValidationError(report) from e
        logger.error(f"Failed to create FHIR resource: {str(e)}")
        return None


def prefetch_to_bundle(prefetch: Dict[str, Any]) -> Dict[str, Any]:
    """Flatten CDS Hooks prefetch into a collection Bundle dict.

    Converts the keyed prefetch format (used in CDS Hooks) into a flat bundle
    suitable for Dataset.from_fhir_bundle().

    Args:
        prefetch: CDS Hooks prefetch dict with format:
            {"patient": {...}, "observations": {"entry": [...]}, ...}

    Returns:
        Bundle dict with type "collection" and flattened entries

    Example:
        >>> prefetch = request.prefetch
        >>> bundle = prefetch_to_bundle(prefetch)
        >>> dataset = Dataset.from_fhir_bundle(bundle, schema=schema)
    """
    entries = []
    for key, value in prefetch.items():
        if isinstance(value, dict):
            if "entry" in value:  # Searchset bundle
                entries.extend(value["entry"])
            elif "resourceType" in value:  # Single resource
                entries.append({"resource": value})
    return {"type": "collection", "entry": entries}


def convert_prefetch_to_fhir_objects(
    prefetch_dict: Dict[str, Any],
) -> Dict[str, Resource]:
    """Convert a dictionary of FHIR resource dicts to FHIR Resource objects.

    Takes a prefetch dictionary where values may be either dict representations of FHIR
    resources or already instantiated FHIR Resource objects, and ensures all values are
    FHIR Resource objects.

    Args:
        prefetch_dict: Dictionary mapping keys to FHIR resource dicts or objects

    Returns:
        Dict[str, Resource]: Dictionary with same keys but all values as FHIR Resource objects

    Example:
        >>> prefetch = {
        ...     "patient": {"resourceType": "Patient", "id": "123"},
        ...     "condition": Condition(id="456", ...)
        ... }
        >>> fhir_objects = convert_prefetch_to_fhir_objects(prefetch)
        >>> isinstance(fhir_objects["patient"], Patient)  # True
        >>> isinstance(fhir_objects["condition"], Condition)  # True
    """
    result: Dict[str, Resource] = {}

    for key, resource_data in prefetch_dict.items():
        if isinstance(resource_data, dict):
            # Convert dict to FHIR Resource object
            resource_type = resource_data.get("resourceType")
            if resource_type:
                try:
                    # Fix timezone-naive datetimes before validation
                    fixed_data = _fix_timezone_naive_datetimes(resource_data)
                    resource_class = get_fhir_resource(resource_type)
                    result[key] = resource_class(**fixed_data)
                except Exception as e:
                    logger.warning(
                        f"Failed to convert {resource_type} to FHIR object: {e}"
                    )
                    result[key] = resource_data
            else:
                logger.warning(
                    f"No resourceType found for key '{key}', keeping as dict"
                )
                result[key] = resource_data
        elif isinstance(resource_data, Resource):
            # Already a FHIR object
            result[key] = resource_data
        else:
            logger.warning(f"Unexpected type for key '{key}': {type(resource_data)}")
            result[key] = resource_data

    return result


def read_content_attachment(
    document_reference: DocumentReference,
    include_data: bool = True,
) -> Optional[List[Dict[str, Any]]]:
    """Read the attachments in a human readable format from a FHIR DocumentReference content field.

    Args:
        document_reference: The FHIR DocumentReference resource
        include_data: Whether to include the data of the attachments. If true, the data will be also be decoded (default: True)

    Returns:
        Optional[List[Dict[str, Any]]]: List of dictionaries containing attachment data and metadata,
            or None if no attachments are found:
            [
                {
                    "data": str,
                    "metadata": Dict[str, Any]
                }
            ]
    """
    if not document_reference.content:
        return None

    attachments = []
    for content in document_reference.content:
        attachment = content.attachment
        result = {}

        if include_data:
            result["data"] = (
                attachment.url if attachment.url else attachment.data.decode("utf-8")
            )

        result["metadata"] = {
            "content_type": attachment.contentType,
            "title": attachment.title,
            "creation": attachment.creation,
        }

        attachments.append(result)

    return attachments
