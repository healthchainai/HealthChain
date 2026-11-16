#!/usr/bin/env python3
"""
Ward Monitoring on Live FHIR Data

Computes per-area ward measures (occupied beds, recent admissions, high NEWS2
scores) from FHIR Encounter, Location and Observation resources, read from
files or a live FHIR API, and serves the summary over HTTP.

HealthChain reads and checks the FHIR data (FHIRGateway, load_bundle,
validate_resource, resolve_reference) and serves the result (HealthChainAPI).
Each site's local codes live in its config.json; the research definitions live
in ward_definitions.py and never touch FHIR. All data is synthetic.

Run from the repository root after `uv sync` (or `pip install .`):
    python cookbook/ward_monitoring.py              # print, then serve at :8000/docs
    python cookbook/ward_monitoring.py --json       # print the JSON once
    python cookbook/ward_monitoring.py --json --site b --window-hours 8 --acuity-high 5
    python cookbook/ward_monitoring.py --json --admissions all-arrivals
    python cookbook/ward_monitoring.py --json --as-of 2026-10-23T04:00:00Z

Live FHIR API (needs MEDPLUM_* in .env; see the FHIR sandbox setup guide):
    healthchain seed medplum cookbook/data/ward_monitoring/site_a/medplum_upload.json
    python cookbook/ward_monitoring.py --json --source medplum --as-of 2026-10-23T12:00:00Z
"""

import argparse
import json
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Literal, NamedTuple

from dotenv import load_dotenv
from fastapi import HTTPException, Query
from pydantic import BaseModel, Field, PositiveInt

from healthchain.fhir import (
    FHIRValidationError,
    get_resources,
    load_bundle,
    resolve_reference,
    validate_resource,
)
from healthchain.fhir.r4b import Bundle, Encounter, Location, Observation
from healthchain.gateway import FHIRGateway, HealthChainAPI
from healthchain.gateway.clients import FHIRAuthConfig

try:  # run as a script: python cookbook/ward_monitoring.py
    from ward_definitions import (
        ACUITY_HIGH,
        ACUITY_MAX_AGE_HOURS,
        ADMISSION_DEFINITIONS,
        WINDOW_HOURS,
        AreaVisit,
    )
except ImportError:  # imported from the repository root
    from cookbook.ward_definitions import (
        ACUITY_HIGH,
        ACUITY_MAX_AGE_HOURS,
        ADMISSION_DEFINITIONS,
        WINDOW_HOURS,
        AreaVisit,
    )

load_dotenv()

DATA_DIR = Path(__file__).parent / "data" / "ward_monitoring"


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


class SiteData(NamedTuple):
    encounters: Bundle
    locations: Bundle
    observations: Bundle
    pulled_at: datetime  # the latest reference time the data can answer for


def load_config(site_dir: Path) -> SiteConfig:
    return SiteConfig.model_validate_json((site_dir / "config.json").read_text())


def timestamp(value: datetime | str) -> datetime:
    """A UTC datetime; refuses date-only or naive values, which can't be ordered."""
    if isinstance(value, str):
        value = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("Use complete, timezone-aware timestamps")
    return value.astimezone(timezone.utc)


# --- Steps 1-2: Read and check the FHIR data -----------------------------------


def from_files(site_dir: Path, config: SiteConfig) -> SiteData:
    """Load a site's exported Bundles. load_bundle validates every resource."""
    encounters = json.loads((site_dir / "encounters.json").read_text())
    for entry in encounters["entry"]:
        for item in entry["resource"].get("location", []):
            item["status"] = config.location_status_map.get(
                item["status"], item["status"]
            )
    encounters = load_bundle(encounters, version="R4B")
    return SiteData(
        encounters=encounters,
        locations=load_bundle(site_dir / "locations.json", version="R4B"),
        observations=load_bundle(site_dir / "observations.json", version="R4B"),
        pulled_at=timestamp(encounters.timestamp),
    )


def from_gateway(gateway: FHIRGateway, source: str, config: SiteConfig) -> SiteData:
    """Query the same resources from a FHIR API and validate them."""

    def fetch(resource_type: type) -> Bundle:
        params = {**config.search_params, "_count": "100"}
        bundle = gateway.search(resource_type, params, source=source)
        if any(link.relation == "next" for link in bundle.link or []):
            raise ValueError(f"{resource_type.__name__} search returned >1 page")
        for entry in bundle.entry or []:
            report = validate_resource(entry.resource)
            if not report.valid:
                raise FHIRValidationError(report)
        return bundle

    pulled_at = datetime.now(timezone.utc)
    return SiteData(fetch(Encounter), fetch(Location), fetch(Observation), pulled_at)


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
    data: SiteData, config: SiteConfig, as_of: datetime
) -> dict[str, int]:
    """Latest NEWS2 score per encounter, no older than the freshness rule allows."""
    cutoff = as_of - timedelta(hours=ACUITY_MAX_AGE_HOURS)
    code = (config.acuity_code.system, config.acuity_code.code)
    latest: dict[str, tuple[datetime, int]] = {}
    for obs in get_resources(data.observations, Observation):
        if code not in {(c.system, c.code) for c in obs.code.coding or []}:
            continue
        if obs.valueInteger is None or obs.effectiveDateTime is None:
            continue
        when = timestamp(obs.effectiveDateTime)
        encounter = resolve_reference(data.encounters, obs.encounter)
        if encounter is None or not cutoff <= when <= as_of:
            continue
        if encounter.id not in latest or when > latest[encounter.id][0]:
            latest[encounter.id] = (when, obs.valueInteger)
    return {encounter: score for encounter, (_, score) in latest.items()}


# --- Step 4: Compute the measures ----------------------------------------------


def summarise(
    data: SiteData,
    config: SiteConfig,
    admissions: str = "still-present",
    window_hours: int = WINDOW_HOURS,
    as_of: datetime | str | None = None,
    acuity_high: int = ACUITY_HIGH,
) -> dict:
    as_of = timestamp(as_of or data.pulled_at)
    if as_of > data.pulled_at:
        raise ValueError("as_of is after the data was pulled")
    if window_hours <= 0:
        raise ValueError("window_hours must be positive")
    if not 0 <= acuity_high <= 20:
        raise ValueError("acuity_high must be a NEWS2 score from 0 to 20")
    known = {
        identifier.value
        for location in get_resources(data.locations, Location)
        for identifier in location.identifier or []
        if identifier.system == config.location_system
    }
    if missing := set(config.areas) - known:
        raise ValueError(f"Configured areas not found in Locations: {sorted(missing)}")

    visits = [
        visit
        for encounter in get_resources(data.encounters, Encounter)
        for visit in area_visits(encounter, data.locations, config, as_of)
    ]
    beds = [v.bed for v in visits if v.present]
    if len(beds) != len(set(beds)):
        raise ValueError("Two encounters occupy the same bed")
    scores = latest_scores(data, config, as_of)
    count_admissions = ADMISSION_DEFINITIONS[admissions]
    cutoff = as_of - timedelta(hours=window_hours)

    rows = []
    for area_id, area in config.areas.items():
        in_area = [v for v in visits if v.area == area_id]
        present = [v for v in in_area if v.present]
        rows.append(
            {
                "area": area.name,
                "occupied_beds": len(present),
                "bed_capacity": area.capacity,
                "occupancy_percent": round(100 * len(present) / area.capacity, 1),
                "admissions": count_admissions(in_area, cutoff, as_of),
                "unknown_entry_times": sum(v.entered_at is None for v in present),
                "high_acuity": sum(
                    scores.get(v.encounter, -1) >= acuity_high for v in present
                ),
                "acuity_unknown": sum(v.encounter not in scores for v in present),
            }
        )
    return {
        "as_of": as_of.isoformat(),
        "window_hours": window_hours,
        "admissions_definition": admissions,
        "acuity_high": acuity_high,
        "areas": rows,
    }


def run(
    site: str = "a",
    admissions: str = "still-present",
    window_hours: int = WINDOW_HOURS,
    source: str = "files",
    as_of: datetime | str | None = None,
    acuity_high: int = ACUITY_HIGH,
) -> dict:
    """The whole workflow: read one site's records and summarise them."""
    site_dir = DATA_DIR / f"site_{site}"
    config = load_config(site_dir)
    if source == "files":
        data = from_files(site_dir, config)
    else:
        gateway = FHIRGateway()
        gateway.add_source(
            source, FHIRAuthConfig.from_env(source.upper()).to_connection_string()
        )
        data = from_gateway(gateway, source, config)
    return summarise(data, config, admissions, window_hours, as_of, acuity_high)


# --- Step 5: Serve the summary -------------------------------------------------


def create_app(
    site: Literal["a", "b"] = "a",
    admissions: str = "still-present",
    window_hours: int = WINDOW_HOURS,
    source: str = "files",
    as_of: str | None = None,
    acuity_high: int = ACUITY_HIGH,
) -> HealthChainAPI:
    """Serve the per-area summary at GET /ward-summary; each request reruns `run`."""
    app = HealthChainAPI(title="Ward summary")

    @app.get("/ward-summary")
    def ward_summary(
        site: Literal["a", "b"] = site,
        admissions: Literal[tuple(ADMISSION_DEFINITIONS)] = admissions,
        window_hours: int = Query(default=window_hours, gt=0),
        as_of: str | None = as_of,
        acuity_high: int = Query(default=acuity_high, ge=0, le=20),
    ) -> dict:
        try:
            return run(site, admissions, window_hours, source, as_of, acuity_high)
        except ValueError as error:  # e.g. a reference time after the data pull
            raise HTTPException(status_code=422, detail=str(error)) from error

    return app


def format_table(result: dict) -> str:
    """The summary as a plain-text table, one row per area."""
    columns = {
        "area": "Area",
        "occupied_beds": "Occupied beds",
        "bed_capacity": "Capacity",
        "admissions": f"Admissions ({result['window_hours']}h)",
        "unknown_entry_times": "Unknown entry times",
        "high_acuity": "High acuity",
        "acuity_unknown": "Acuity unknown",
    }
    rows = [list(columns.values())]
    rows += [[str(area[key]) for key in columns] for area in result["areas"]]
    widths = [max(len(row[i]) for row in rows) for i in range(len(columns))]
    lines = [
        "  ".join(v.ljust(w) for v, w in zip(row, widths)).rstrip() for row in rows
    ]
    return f"Ward summary at {result['as_of']}\n" + "\n".join(lines)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Synthetic ward summary from FHIR")
    parser.add_argument("--site", choices=["a", "b"], default="a")
    parser.add_argument(
        "--admissions", choices=list(ADMISSION_DEFINITIONS), default="still-present"
    )
    parser.add_argument("--window-hours", type=int, default=WINDOW_HOURS)
    parser.add_argument("--source", choices=["files", "medplum"], default="files")
    parser.add_argument("--as-of", help="Reference time, e.g. 2026-10-23T04:00:00Z")
    parser.add_argument(
        "--acuity-high", type=int, default=ACUITY_HIGH, help="NEWS2 high cutoff, 0-20"
    )
    parser.add_argument("--json", action="store_true", help="Print JSON and exit")
    parser.add_argument("--port", type=int, default=8000)
    options = vars(parser.parse_args())
    as_json, port = options.pop("json"), options.pop("port")
    if as_json:
        print(json.dumps(run(**options), indent=2))
    else:
        print(format_table(run(**options)))
        print(f"\nTry it: http://127.0.0.1:{port}/docs  (Ctrl+C to stop)\n")
        create_app(**options).run(host="127.0.0.1", port=port)
