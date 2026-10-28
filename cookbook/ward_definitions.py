"""
Research definitions for the ward occupancy and admissions recipe.

This file belongs to the research team. It holds every definition that is
expected to change as the research develops: what counts as an admission, how
far back counts as recent, and when a clinical score counts as high. The recipe
(ward_monitoring.py) handles FHIR access, validation and site mappings,
and calls these definitions without knowing what they contain.

A revision is a change to this file only. Each definition has its own frozen
expected output in data/ward_monitoring/, and the tests check both, so old and new
definitions can be compared on the same data.

R2-R3 mark open research decisions; the values below are placeholders.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Callable


@dataclass(frozen=True)
class AreaVisit:
    """One stay in a research area, as the recipe hands it to the definitions."""

    encounter: str  # Encounter resource ID
    area: str  # configured area identifier
    bed: str  # Location ID of the latest bed in this area
    entered_at: datetime | None  # None when the source has no area-entry time
    present: bool  # in this area at the reference time


# R2: how far back counts as "recent"? Both ends of the window are included.
WINDOW_HOURS = 12


def admissions_still_present(
    visits: list[AreaVisit], cutoff: datetime, as_of: datetime
) -> int:
    """R2 option A: entries to the area in the window, among people still there."""
    return sum(
        v.present and v.entered_at is not None and cutoff <= v.entered_at <= as_of
        for v in visits
    )


def admissions_all_arrivals(
    visits: list[AreaVisit], cutoff: datetime, as_of: datetime
) -> int:
    """R2 option B: every entry to the area in the window, including people who left."""
    return sum(
        v.entered_at is not None and cutoff <= v.entered_at <= as_of for v in visits
    )


ADMISSION_DEFINITIONS: dict[str, Callable[..., int]] = {
    "still-present": admissions_still_present,
    "all-arrivals": admissions_all_arrivals,
}

# R3: which clinical variable sits alongside occupancy, and what counts as high?
# The variable's FHIR code is site-specific, so it lives in each site's config.
ACUITY_HIGH = 3  # placeholder: a score of 3 or more on a synthetic 1-4 scale
ACUITY_MAX_AGE_HOURS = 12  # freshness rule: older scores count as unknown
