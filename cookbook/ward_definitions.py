"""
Research definitions for the ward occupancy and admissions recipe.

This file belongs to the research team. It holds every definition that is
expected to change as the research develops: what counts as an admission, how
far back counts as recent, and when a clinical score counts as high. The recipe
(ward_monitoring.py) handles FHIR access, validation and site mappings,
and calls these definitions without knowing what they contain.

A revision is a change to this file only. Each definition has its own frozen
expected output in data/ward_monitoring/, and the tests check them all, so old
and new definitions can be compared on the same data.
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


# How far back counts as "recent": one 12-hour shift. Both ends are included.
# Example revision: a move to 8-hour shifts sets this to 8 (--window-hours 8).
WINDOW_HOURS = 12


def admissions_still_present(
    visits: list[AreaVisit], cutoff: datetime, as_of: datetime
) -> int:
    """Option A: entries to the area in the window, among people still there."""
    return sum(
        v.present and v.entered_at is not None and cutoff <= v.entered_at <= as_of
        for v in visits
    )


def admissions_all_arrivals(
    visits: list[AreaVisit], cutoff: datetime, as_of: datetime
) -> int:
    """Option B: every entry to the area in the window, including people who left."""
    return sum(
        v.entered_at is not None and cutoff <= v.entered_at <= as_of for v in visits
    )


ADMISSION_DEFINITIONS: dict[str, Callable[..., int]] = {
    "still-present": admissions_still_present,
    "all-arrivals": admissions_all_arrivals,
}

# Acuity is the NEWS2 total score; 7 or more counts as high.
# The variable's FHIR code is site-specific, so it lives in each site's config.
ACUITY_HIGH = 7
ACUITY_MAX_AGE_HOURS = 12  # freshness rule: older scores count as unknown
