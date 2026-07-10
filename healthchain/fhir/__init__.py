"""FHIR utilities for HealthChain."""

from healthchain.fhir import r4b

from healthchain.fhir.version import (
    FHIRVersion,
    get_fhir_resource,
    get_default_version,
    fhir_version_context,
    convert_resource,
    get_resource_version,
)

from healthchain.fhir.resourcehelpers import (
    create_condition,
    create_medication_statement,
    create_allergy_intolerance,
    create_value_quantity_observation,
    create_patient,
    create_risk_assessment_from_prediction,
    create_document_reference,
    create_document_reference_content,
    set_condition_category,
    add_provenance_metadata,
    add_coding_to_codeable_concept,
)

from healthchain.fhir.elementhelpers import (
    create_single_codeable_concept,
    create_single_reaction,
    create_single_attachment,
    create_dosage,
)

from healthchain.fhir.readers import (
    CodedEntry,
    EntryCoding,
    create_resource_from_dict,
    convert_prefetch_to_fhir_objects,
    get_coded_entries,
    get_medications,
    prefetch_to_bundle,
    read_content_attachment,
)

from healthchain.fhir.validation import (
    FHIRValidationError,
    ValidationIssue,
    ValidationReport,
    load_bundle,
    validate_resource,
)

from healthchain.fhir.bundlehelpers import (
    create_bundle,
    add_resource,
    get_resource_type,
    get_resources,
    resolve_reference,
    set_resources,
    merge_bundles,
    extract_resources,
    count_resources,
)

from healthchain.fhir.utilities import (
    calculate_age_from_birthdate,
    calculate_age_from_event_date,
    encode_gender,
)

__all__ = [
    # R4B re-export module
    "r4b",
    # Version management
    "FHIRVersion",
    "get_fhir_resource",
    "get_default_version",
    "fhir_version_context",
    "convert_resource",
    "get_resource_version",
    # Resource creation
    "create_condition",
    "create_medication_statement",
    "create_allergy_intolerance",
    "create_value_quantity_observation",
    "create_patient",
    "create_risk_assessment_from_prediction",
    "create_document_reference",
    "create_document_reference_content",
    # Element creation
    "create_single_codeable_concept",
    "create_single_reaction",
    "create_single_attachment",
    "create_dosage",
    # Resource modification
    "set_condition_category",
    "add_provenance_metadata",
    "add_coding_to_codeable_concept",
    # Conversions and readers
    "CodedEntry",
    "EntryCoding",
    "create_resource_from_dict",
    "convert_prefetch_to_fhir_objects",
    "get_coded_entries",
    "get_medications",
    "prefetch_to_bundle",
    "read_content_attachment",
    # Validation
    "FHIRValidationError",
    "ValidationIssue",
    "ValidationReport",
    "load_bundle",
    "validate_resource",
    # Bundle operations
    "create_bundle",
    "add_resource",
    "get_resource_type",
    "get_resources",
    "resolve_reference",
    "set_resources",
    "merge_bundles",
    "extract_resources",
    "count_resources",
    # Utility functions
    "calculate_age_from_birthdate",
    "calculate_age_from_event_date",
    "encode_gender",
]
