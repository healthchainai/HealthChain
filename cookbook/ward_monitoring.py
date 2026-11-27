#!/usr/bin/env python3
"""
Ward Monitoring on Live FHIR Data

Computes per-area ward measures (occupied beds, recent admissions, high NEWS2
scores) from FHIR Encounter, Location and Observation resources, read from
files or a live FHIR API, and serves the summary over HTTP.

HealthChain reads and checks the FHIR data (FHIRGateway, load_bundle,
validate_resource, resolve_reference) and serves the result (HealthChainAPI).
The project's own FHIR mapping lives in ward_mapping.py, with each site's local
codes in its config.json; the research definitions live in ward_definitions.py
and never touch FHIR. All data is synthetic.

Run from the repository root after `pip install healthchain`:
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
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Literal, NamedTuple

from dotenv import load_dotenv
from fastapi import HTTPException, Query

from healthchain.fhir import (
    FHIRValidationError,
    get_resources,
    load_bundle,
    validate_resource,
)
from healthchain.fhir.r4b import Bundle, Encounter, Location, Observation
from healthchain.gateway import FHIRGateway, HealthChainAPI
from healthchain.gateway.clients import FHIRAuthConfig

try:  # run as a script: python cookbook/ward_monitoring.py
    from ward_definitions import ACUITY_HIGH, ADMISSION_DEFINITIONS, WINDOW_HOURS
    from ward_mapping import (
        SiteConfig,
        area_visits,
        latest_scores,
        load_config,
        timestamp,
    )
except ImportError:  # imported from the repository root
    from cookbook.ward_definitions import (
        ACUITY_HIGH,
        ADMISSION_DEFINITIONS,
        WINDOW_HOURS,
    )
    from cookbook.ward_mapping import (
        SiteConfig,
        area_visits,
        latest_scores,
        load_config,
        timestamp,
    )

load_dotenv()

DATA_DIR = Path(__file__).parent / "data" / "ward_monitoring"


# --- Steps 1-2: Read and check the FHIR data -----------------------------------


class SiteData(NamedTuple):
    encounters: Bundle
    locations: Bundle
    observations: Bundle
    pulled_at: datetime  # the latest reference time the data can answer for


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
        bundle = gateway.search(
            resource_type, config.search_params, source=source, follow_pagination=True
        )
        for entry in bundle.entry or []:
            report = validate_resource(entry.resource)
            if not report.valid:
                raise FHIRValidationError(report)
        return bundle

    pulled_at = datetime.now(timezone.utc)
    return SiteData(fetch(Encounter), fetch(Location), fetch(Observation), pulled_at)


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
    scores = latest_scores(data.observations, data.encounters, config, as_of)
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
