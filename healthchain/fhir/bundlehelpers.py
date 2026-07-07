"""Helper functions for working with FHIR Bundles.
Patterns:
- create_*(): create a new FHIR bundle
- add_*(): add a resource to a bundle
- get_*(): get resources from a bundle
- set_*(): set resources in a bundle
- merge_*(): merge multiple bundles into a single bundle
- extract_*(): extract resources from a bundle
"""

from typing import List, Type, TypeVar, Optional, Union
from fhir.resources.R4B.bundle import Bundle, BundleEntry
from fhir.resources.R4B.reference import Reference
from fhir.resources.resource import Resource

T = TypeVar("T", bound=Resource)


def create_bundle(bundle_type: str = "collection") -> Bundle:
    """Create an empty FHIR Bundle.
    https://www.hl7.org/fhir/bundle.html

    Args:
        bundle_type: The type of bundle (default: collection)
            Valid types: document, message, transaction, transaction-response,
            batch, batch-response, history, searchset, collection
    """
    return Bundle(type=bundle_type, entry=[])


def add_resource(
    bundle: Bundle, resource: Resource, full_url: Optional[str] = None
) -> None:
    """Add a resource to a bundle.

    Args:
        bundle: The bundle to add to
        resource: The resource to add, e.g. Condition, MedicationStatement, AllergyIntolerance
        full_url: Optional full URL for the resource
    """
    entry = BundleEntry(resource=resource)
    if full_url:
        entry.fullUrl = full_url
    bundle.entry = (bundle.entry or []) + [entry]


def get_resource_type(
    resource_type: Union[str, Type[Resource]],
) -> Type[Resource]:
    """Get the resource type class from string or type.

    Args:
        resource_type: String name of the resource type (e.g. "Condition") or the type itself

    Returns:
        The R4B resource type class

    Raises:
        ValueError: If the resource type is not supported or cannot be imported
    """
    if isinstance(resource_type, type):
        return resource_type

    if not isinstance(resource_type, str):
        raise ValueError(
            f"Resource type must be a string or Resource class, got {type(resource_type)}"
        )

    from healthchain.fhir.version import get_fhir_resource

    return get_fhir_resource(resource_type)


def get_resources(
    bundle: Bundle, resource_type: Union[str, Type[Resource]]
) -> List[Resource]:
    """Get all resources of a specific type from a bundle.

    Args:
        bundle: The bundle to search
        resource_type: String name of the resource type (e.g. "Condition") or the type itself

    Returns:
        List of resources of the specified type

    Example:
        >>> bundle = create_bundle()
        >>> # Using string identifier
        >>> conditions = get_resources(bundle, "Condition")
        >>> medications = get_resources(bundle, "MedicationStatement")
        >>> allergies = get_resources(bundle, "AllergyIntolerance")
        >>>
        >>> # Or using type directly
        >>> from fhir.resources.condition import Condition
        >>> conditions = get_resources(bundle, Condition)
    """
    if isinstance(resource_type, str):
        type_name = resource_type
        return [
            entry.resource
            for entry in (bundle.entry or [])
            if entry.resource is not None and type(entry.resource).__name__ == type_name
        ]
    type_class = get_resource_type(resource_type)
    type_name = type_class.__name__
    return [
        entry.resource
        for entry in (bundle.entry or [])
        if entry.resource is not None and entry.resource.__class__.__name__ == type_name
    ]


def resolve_reference(
    bundle: Bundle,
    reference: Union[str, Reference],
    parent: Optional[Resource] = None,
) -> Optional[Resource]:
    """Resolve a FHIR Reference to its target resource within a bundle.

    Read-side counterpart to ``add_resource``: given a reference string or an
    R4B ``Reference`` element, find the resource it points to. Resolution is
    attempted in this order:

    1. Contained: references starting with ``#`` are resolved against
       ``parent.contained`` by resource ``id``.
    2. Exact ``fullUrl`` match against ``entry.fullUrl`` (covers absolute URLs
       and ``urn:uuid:...`` references).
    3. ``Type/id`` relative references: match an entry whose resource type name
       and ``id`` match, or an absolute ``fullUrl`` ending in ``/Type/id``.
    4. ``urn:uuid:{id}`` fallback: when no ``fullUrl`` matched, match a resource
       whose ``id`` equals the uuid part.

    Never raises on unresolvable or malformed references; returns None instead.
    The lookup is built lazily per call (no caching or state).

    Args:
        bundle: The bundle to search
        reference: A reference string (e.g. "Patient/123", "urn:uuid:...",
            "#contained-id") or an R4B ``Reference`` element
        parent: The resource that owns the reference, required only to resolve
            contained ("#id") references against its ``contained`` list

    Returns:
        The first matching resource, or None if the reference cannot be resolved

    Example:
        >>> bundle = load_bundle("synthea_patient.json")
        >>> med_request = get_resources(bundle, "MedicationRequest")[0]
        >>> medication = resolve_reference(bundle, med_request.medicationReference)
        >>> patient = resolve_reference(bundle, "Patient/patient-1")
    """
    ref = reference.reference if isinstance(reference, Reference) else reference
    if not ref:
        return None

    # 1. Contained reference (#id) resolves against the parent's contained list
    if ref.startswith("#"):
        if parent is None:
            return None
        target_id = ref[1:]
        for contained in getattr(parent, "contained", None) or []:
            if getattr(contained, "id", None) == target_id:
                return contained
        return None

    entries = [entry for entry in (bundle.entry or []) if entry.resource is not None]

    # 2. Exact fullUrl match (absolute URLs and urn:uuid references)
    for entry in entries:
        if entry.fullUrl and entry.fullUrl == ref:
            return entry.resource

    # 3. Type/id relative references, and absolute fullUrls ending in /Type/id
    if "/" in ref:
        head, _, res_id = ref.rpartition("/")
        type_name = head.rsplit("/", 1)[-1]
        if type_name and res_id:
            tail = f"/{type_name}/{res_id}"
            for entry in entries:
                resource = entry.resource
                if (
                    resource.__class__.__name__ == type_name
                    and getattr(resource, "id", None) == res_id
                ):
                    return resource
                if entry.fullUrl and entry.fullUrl.endswith(tail):
                    return resource

    # 4. urn:uuid fallback: match a resource whose id equals the uuid part
    if ref.startswith("urn:uuid:"):
        uuid_part = ref[len("urn:uuid:") :]
        for entry in entries:
            if getattr(entry.resource, "id", None) == uuid_part:
                return entry.resource

    return None


def set_resources(
    bundle: Bundle,
    resources: List[Resource],
    resource_type: Union[str, Type[Resource]],
    replace: bool = True,
) -> None:
    """Set resources of a specific type in the bundle.

    Args:
        bundle: The bundle to modify
        resources: The new resources to add
        resource_type: String name of the resource type (e.g. "Condition") or the type itself
        replace: If True, remove existing resources of this type before adding new ones.
                If False, append new resources to existing ones. Defaults to True.

    Example:
        >>> bundle = create_bundle()
        >>> # Append to existing resources (default behavior)
        >>> set_resources(bundle, [condition1, condition2], "Condition")
        >>> set_resources(bundle, [medication1], "MedicationStatement")
        >>>
        >>> # Replace existing resources
        >>> set_resources(bundle, [condition3], "Condition", replace=True)
        >>>
        >>> # Or using type directly
        >>> from fhir.resources.condition import Condition
        >>> set_resources(bundle, [condition1, condition2], Condition)
    """
    # Remove existing resources of this type if replace=True
    if replace:
        if isinstance(resource_type, str):
            type_name = resource_type
            bundle.entry = [
                entry
                for entry in (bundle.entry or [])
                if entry.resource is None or type(entry.resource).__name__ != type_name
            ]
        else:
            type_class = get_resource_type(resource_type)
            type_name_cls = type_class.__name__
            bundle.entry = [
                entry
                for entry in (bundle.entry or [])
                if entry.resource is None
                or entry.resource.__class__.__name__ != type_name_cls
            ]

    # Add new resources, validating type
    if isinstance(resource_type, str):
        type_name = resource_type
        for resource in resources:
            if type(resource).__name__ != type_name:
                raise ValueError(
                    f"Resource must be of type {type_name}, "
                    f"got {type(resource).__name__}"
                )
            add_resource(bundle, resource)
    else:
        type_class = get_resource_type(resource_type)
        for resource in resources:
            if resource.__class__.__name__ != type_class.__name__:
                raise ValueError(
                    f"Resource must be of type {type_class.__name__}, "
                    f"got {type(resource).__name__}"
                )
            add_resource(bundle, resource)


def merge_bundles(
    bundles: List[Bundle],
    bundle_type: str = "collection",
    deduplicate: bool = False,
    dedupe_key: str = "id",
) -> Bundle:
    """Merge multiple FHIR bundles into a single bundle.

    Combines entries from multiple bundles while preserving resource metadata.
    Useful for aggregating search results from multiple FHIR sources.

    Args:
        bundles: List of bundles to merge
        bundle_type: Type for the merged bundle (default: "collection")
        deduplicate: If True, remove duplicate resources based on dedupe_key
        dedupe_key: Resource attribute to use for deduplication (default: "id")

    Returns:
        A new bundle containing all entries from input bundles

    Example:
        >>> # Merge search results from multiple sources
        >>> epic_bundle = gateway.search(Condition, {"patient": "123"}, "epic")
        >>> cerner_bundle = gateway.search(Condition, {"patient": "123"}, "cerner")
        >>> merged = merge_bundles([epic_bundle, cerner_bundle], deduplicate=True)
        >>>
        >>> # Use in Document workflow
        >>> doc = Document(data=merged)
        >>> doc.fhir.bundle  # Contains all conditions from both sources
    """
    merged = create_bundle(bundle_type=bundle_type)

    if deduplicate:
        # Track seen resources by dedupe_key to avoid duplicates
        seen_keys = set()

        for bundle in bundles:
            if not bundle or not bundle.entry:
                continue

            for entry in bundle.entry:
                if not entry.resource:
                    continue

                # Get the deduplication key value
                key_value = getattr(entry.resource, dedupe_key, None)

                # Skip if we've seen this key before
                if key_value and key_value in seen_keys:
                    continue

                # Add to merged bundle and track the key
                add_resource(merged, entry.resource, entry.fullUrl)
                if key_value:
                    seen_keys.add(key_value)
    else:
        # No deduplication - just merge all entries
        for bundle in bundles:
            if not bundle or not bundle.entry:
                continue

            for entry in bundle.entry:
                if entry.resource:
                    add_resource(merged, entry.resource, entry.fullUrl)

    return merged


def extract_resources(
    bundle: Bundle, resource_type: Union[str, Type[Resource]]
) -> List[Resource]:
    """Remove resources of a given type from a bundle and return them.

    Useful for extracting and separating specific resource types (e.g., OperationOutcome)
    from a FHIR Bundle, modifying the bundle in place.

    Args:
        bundle: The FHIR Bundle to process (modified in place)
        resource_type: The FHIR resource class or string name to extract (e.g., OperationOutcome or "OperationOutcome")

    Returns:
        List[Resource]: All resources of the specified type that were in the bundle
    """
    if not bundle or not bundle.entry:
        return []

    extracted: List[Resource] = []
    remaining_entries: List[BundleEntry] = []

    if isinstance(resource_type, str):
        type_name = resource_type
        for entry in bundle.entry:
            resource = entry.resource
            if resource is not None and type(resource).__name__ == type_name:
                extracted.append(resource)
                continue
            remaining_entries.append(entry)
    else:
        type_class = get_resource_type(resource_type)
        type_name_cls = type_class.__name__
        for entry in bundle.entry:
            resource = entry.resource
            if resource is not None and resource.__class__.__name__ == type_name_cls:
                extracted.append(resource)
                continue
            remaining_entries.append(entry)

    bundle.entry = remaining_entries
    return extracted


def count_resources(bundle: Bundle) -> dict[str, int]:
    """Count resources by type in a bundle.

    Args:
        bundle: The FHIR Bundle to analyze

    Returns:
        Dictionary mapping resource type names to their counts.
        Example: {"Condition": 2, "MedicationStatement": 1, "Patient": 1}

    Example:
        >>> bundle = create_bundle()
        >>> add_resource(bundle, create_condition(...))
        >>> add_resource(bundle, create_condition(...))
        >>> add_resource(bundle, create_medication_statement(...))
        >>> counts = count_resources(bundle)
        >>> print(counts)
        {'Condition': 2, 'MedicationStatement': 1}
    """
    if not bundle or not bundle.entry:
        return {}

    counts: dict[str, int] = {}
    for entry in bundle.entry:
        if entry.resource:
            # Get the resource type from the class name
            resource_type = entry.resource.__resource_type__
            counts[resource_type] = counts.get(resource_type, 0) + 1

    return counts
