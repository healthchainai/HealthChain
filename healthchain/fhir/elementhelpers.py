"""FHIR element creation functions.

This module provides convenience functions for creating FHIR elements that are used
as building blocks within FHIR resources (e.g., CodeableConcept, Attachment, Coding).
"""

import logging
import base64

from typing import Optional, List, Dict, Any

from fhir.resources.R4B.codeableconcept import CodeableConcept
from fhir.resources.R4B.coding import Coding
from fhir.resources.R4B.attachment import Attachment
from fhir.resources.R4B.dosage import Dosage
from fhir.resources.R4B.quantity import Quantity
from fhir.resources.R4B.timing import Timing
from healthchain.fhir.utilities import _utc_now

logger = logging.getLogger(__name__)


def create_single_codeable_concept(
    code: str,
    display: Optional[str] = None,
    system: Optional[str] = "http://snomed.info/sct",
) -> Any:
    """
    Create a minimal FHIR CodeableConcept with a single coding.

    Args:
        code: REQUIRED. The code value from the code system
        display: The display name for the code
        system: The code system (default: SNOMED CT)

    Returns:
        CodeableConcept: A FHIR CodeableConcept resource with a single coding
    """
    return CodeableConcept(coding=[Coding(system=system, code=code, display=display)])


def create_single_reaction(
    code: str,
    display: Optional[str] = None,
    system: Optional[str] = "http://snomed.info/sct",
    severity: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Create a minimal FHIR Reaction with a single coding.

    Creates a FHIR Reaction object with a single manifestation coding. The manifestation
    describes the clinical reaction that was observed. The severity indicates how severe
    the reaction was.

    Args:
        code: REQUIRED. The code value from the code system representing the reaction manifestation
        display: The display name for the manifestation code
        system: The code system for the manifestation code (default: SNOMED CT)
        severity: The severity of the reaction (mild, moderate, severe)

    Returns:
        A list containing a single FHIR Reaction dictionary with manifestation and severity fields
    """
    concept = CodeableConcept(
        coding=[Coding(system=system, code=code, display=display)]
    )

    return [
        {
            "manifestation": [concept],
            "severity": severity,
        }
    ]


def create_dosage(
    text: Optional[str] = None,
    route_code: Optional[str] = None,
    route_display: Optional[str] = None,
    route_system: Optional[str] = "http://snomed.info/sct",
    dose_value: Optional[float] = None,
    dose_unit: Optional[str] = None,
    frequency: Optional[int] = None,
    period: Optional[float] = None,
    period_unit: Optional[str] = None,
    as_needed: Optional[bool] = None,
) -> Dosage:
    """Create a minimal FHIR Dosage element.

    Builds a minimum viable Dosage suitable for attaching to a
    MedicationStatement or MedicationRequest. Only the fields you provide are
    populated. For anything more complex, construct the FHIR Dosage directly.
    https://build.fhir.org/dosage.html

    Args:
        text: Free-text dosage instructions (e.g. "1 tablet twice daily")
        route_code: The route of administration code (e.g. SNOMED CT code for "oral")
        route_display: The display name for the route code
        route_system: The code system for the route (default: SNOMED CT)
        dose_value: The numeric dose amount, set as doseAndRate.doseQuantity.value
        dose_unit: The unit for the dose amount (e.g. "mg", "tablet")
        frequency: How many times per period the dose is taken (Timing.repeat.frequency)
        period: The length of the period (Timing.repeat.period)
        period_unit: The unit of the period (e.g. "d" for day, "h" for hour)
        as_needed: Whether the medication is taken as needed (asNeededBoolean)

    Returns:
        Dosage: A FHIR Dosage element populated with the provided fields
    """
    dosage_data: Dict[str, Any] = {}

    if text is not None:
        dosage_data["text"] = text

    if route_code is not None:
        dosage_data["route"] = create_single_codeable_concept(
            code=route_code, display=route_display, system=route_system
        )

    if dose_value is not None or dose_unit is not None:
        dosage_data["doseAndRate"] = [
            {"doseQuantity": Quantity(value=dose_value, unit=dose_unit)}
        ]

    timing_repeat: Dict[str, Any] = {}
    if frequency is not None:
        timing_repeat["frequency"] = frequency
    if period is not None:
        timing_repeat["period"] = period
    if period_unit is not None:
        timing_repeat["periodUnit"] = period_unit
    if timing_repeat:
        dosage_data["timing"] = Timing(repeat=timing_repeat)

    if as_needed is not None:
        dosage_data["asNeededBoolean"] = as_needed

    return Dosage(**dosage_data)


def create_single_attachment(
    content_type: Optional[str] = None,
    data: Optional[str] = None,
    url: Optional[str] = None,
    title: Optional[str] = "Attachment created by HealthChain",
) -> Any:
    """Create a minimal FHIR Attachment.

    Creates a FHIR Attachment resource with basic fields. Either data or url should be provided.
    If data is provided, it will be base64 encoded.

    Args:
        content_type: The MIME type of the content
        data: The actual data content to be base64 encoded
        url: The URL where the data can be found
        title: A title for the attachment (default: "Attachment created by HealthChain")

    Returns:
        Attachment: A FHIR Attachment resource with basic metadata and content
    """
    if not data and not url:
        logger.warning("No data or url provided for attachment")

    if data:
        data = base64.b64encode(data.encode("utf-8")).decode("utf-8")

    return Attachment(
        contentType=content_type,
        data=data,
        url=url,
        title=title,
        creation=_utc_now(),
    )
