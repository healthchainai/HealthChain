"""
Site config and FHIR mapping for the ward monitoring recipe.

The project's own FHIR code: it reads each site's config and turns validated
FHIR resources into the research variables that ward_definitions.py works on
(area visits and the latest NEWS2 score per stay). ward_monitoring.py reads,
checks and serves the data with HealthChain and calls these functions.
"""

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

from pydantic import BaseModel, Field, PositiveInt

from healthchain.fhir import get_resources, resolve_reference
from healthchain.fhir.r4b import Bundle, Encounter, Location, Observation

try:  # run as a script: python cookbook/ward_monitoring.py
    from ward_definitions import ACUITY_MAX_AGE_HOURS, AreaVisit
except ImportError:  # imported from the repository root
    from cookbook.ward_definitions import ACUITY_MAX_AGE_HOURS, AreaVisit


# --- Site config: one hospital's local names -----------------------------------


class Area(BaseModel):
    name: str
    capacity: PositiveInt


class Code(BaseModel):
    system: str
    code: str


class SiteConfig(BaseModel):
    site: str
    search_params: dict[str, str]  # how to query this site's FHIR API
    location_system: str  # Location.identifier system that names areas
    areas: dict[str, Area] = Field(min_length=1)  # keyed by identifier value
    acuity_code: Code  # this site's Observation code for the NEWS2 score
    location_status_map: dict[str, str] = {}  # fixes for a non-standard export


def load_config(site_dir: Path) -> SiteConfig:
    return SiteConfig.model_validate_json((site_dir / "config.json").read_text())


def timestamp(value: datetime | str) -> datetime:
    """A UTC datetime; refuses date-only or naive values, which can't be ordered."""
    if isinstance(value, str):
        value = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("Use complete, timezone-aware timestamps")
    return value.astimezone(timezone.utc)


# --- Step 3: Map to research variables -----------------------------------------


def area_for_location(
    location: Location, locations: Bundle, config: SiteConfig
) -> str | None:
    """Walk Location.partOf up to the first configured area, or None if outside."""
    while True:
        for identifier in location.identifier or []:
            if (
                identifier.system == config.location_system
                and identifier.value in config.areas
            ):
                return identifier.value
        if location.partOf is None:
            return None
        parent = resolve_reference(locations, location.partOf)
        if parent is None:
            raise ValueError(f"Unresolved Location reference: {location.partOf}")
        location = parent


def area_visits(
    encounter: Encounter, locations: Bundle, config: SiteConfig, as_of: datetime
) -> list[AreaVisit]:
    """Turn location history into area visits at a reference time. A bed move
    within an area is not a new visit; moving to a different area is.

    Presence comes from location periods, so earlier reference times give the
    ward as it was then. An open-ended period relies on its current status."""
    if encounter.period and encounter.period.start:
        if timestamp(encounter.period.start) > as_of:
            return []

    def times(item) -> tuple[datetime | None, datetime | None]:
        period = item.period
        start = timestamp(period.start) if period and period.start else None
        end = timestamp(period.end) if period and period.end else None
        return start, end

    history = sorted(
        ((*times(item), item) for item in encounter.location or []),
        key=lambda row: (row[0] is None, row[0] or as_of),
    )
    visits: list[AreaVisit] = []
    last_area, last_end = None, None
    for start, end, item in history:
        if start is not None and start > as_of:
            continue
        bed = resolve_reference(locations, item.location)
        if bed is None:
            raise ValueError(f"Unresolved Location reference: {item.location}")
        area = area_for_location(bed, locations, config)
        if end is not None:
            present = end > as_of
        else:
            present = encounter.status == "in-progress" and item.status == "active"
        if area is not None:
            if area == last_area and start is not None and start == last_end:
                visits[-1] = replace(visits[-1], bed=bed.id, present=present)
            else:
                visits.append(AreaVisit(encounter.id, area, bed.id, start, present))
        last_area, last_end = area, end
    return visits


def latest_scores(
    observations: Bundle, encounters: Bundle, config: SiteConfig, as_of: datetime
) -> dict[str, int]:
    """Latest NEWS2 score per encounter, no older than the freshness rule allows."""
    cutoff = as_of - timedelta(hours=ACUITY_MAX_AGE_HOURS)
    code = (config.acuity_code.system, config.acuity_code.code)
    latest: dict[str, tuple[datetime, int]] = {}
    for obs in get_resources(observations, Observation):
        if code not in {(c.system, c.code) for c in obs.code.coding or []}:
            continue
        if obs.valueInteger is None or obs.effectiveDateTime is None:
            continue
        when = timestamp(obs.effectiveDateTime)
        encounter = resolve_reference(encounters, obs.encounter)
        if encounter is None or not cutoff <= when <= as_of:
            continue
        if encounter.id not in latest or when > latest[encounter.id][0]:
            latest[encounter.id] = (when, obs.valueInteger)
    return {encounter: score for encounter, (_, score) in latest.items()}
