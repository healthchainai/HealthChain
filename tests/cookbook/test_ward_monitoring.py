import json
from datetime import datetime

import pytest

from cookbook.ward_monitoring import (
    DATA_DIR,
    SiteData,
    area_for_location,
    area_visits,
    from_files,
    from_gateway,
    latest_scores,
    load_config,
    run,
    summarise,
    timestamp,
)
from healthchain.fhir import FHIRValidationError, get_resources
from healthchain.fhir.r4b import Bundle, Encounter, Location, Observation

AS_OF = timestamp("2026-10-23T12:00:00Z")


def site_inputs(site: str = "a") -> tuple:
    site_dir = DATA_DIR / f"site_{site}"
    config = load_config(site_dir)
    return from_files(site_dir, config), config


def encounter(data: SiteData, encounter_id: str) -> Encounter:
    return next(
        e for e in get_resources(data.encounters, Encounter) if e.id == encounter_id
    )


class StubGateway:
    """Answers FHIRGateway.search from in-memory Bundles."""

    def __init__(self, data: SiteData, next_link: bool = False) -> None:
        self.bundles = {
            Encounter: data.encounters,
            Location: data.locations,
            Observation: data.observations,
        }
        self.next_link = next_link

    def search(self, resource_type: type, params: dict, source: str) -> Bundle:
        bundle = self.bundles[resource_type].model_copy(deep=True)
        if self.next_link:
            bundle.link = [{"relation": "next", "url": "https://example.org/next"}]
        return bundle


@pytest.mark.parametrize("site", ["a", "b"])
@pytest.mark.parametrize(
    "admissions,expected",
    [
        ("still-present", "expected_still_present.json"),
        ("all-arrivals", "expected_all_arrivals.json"),
    ],
)
def test_both_sites_match_hand_derived_results(
    site: str, admissions: str, expected: str
) -> None:
    assert run(site=site, admissions=admissions) == json.loads(
        (DATA_DIR / expected).read_text()
    )


def test_gateway_input_matches_file_input() -> None:
    data, config = site_inputs()
    from_server = from_gateway(StubGateway(data), "stub", config)
    assert summarise(from_server, config, as_of=AS_OF) == summarise(data, config)


def test_gateway_refuses_partial_results() -> None:
    data, config = site_inputs()
    with pytest.raises(ValueError, match=">1 page"):
        from_gateway(StubGateway(data, next_link=True), "stub", config)


def test_site_b_status_fails_validation_without_mapping() -> None:
    site_dir = DATA_DIR / "site_b"
    config = load_config(site_dir).model_copy(update={"location_status_map": {}})
    with pytest.raises(FHIRValidationError, match=r"location\[0\]\.status"):
        from_files(site_dir, config)


def test_same_area_bed_move_keeps_area_entry() -> None:
    data, config = site_inputs()
    visits = area_visits(
        encounter(data, "same-area-move"), data.locations, config, AS_OF
    )
    assert len(visits) == 1
    assert visits[0].bed == "n2"
    assert visits[0].entered_at == timestamp("2026-10-22T16:00:00Z")
    assert visits[0].present


def test_cross_area_move_starts_new_visit() -> None:
    data, config = site_inputs()
    visits = area_visits(
        encounter(data, "cross-area-move"), data.locations, config, AS_OF
    )
    assert [(v.area, v.present) for v in visits] == [("W7-N", False), ("W7-S", True)]
    assert visits[1].entered_at == timestamp("2026-10-23T07:00:00Z")


def test_encounter_after_reference_time_is_excluded() -> None:
    data, config = site_inputs()
    assert (
        area_visits(encounter(data, "not-yet-arrived"), data.locations, config, AS_OF)
        == []
    )


def test_acuity_ignores_stale_and_future_scores() -> None:
    data, config = site_inputs()
    scores = latest_scores(data, config, AS_OF)
    assert scores["same-area-move"] == 2  # 22:00 the day before is too old
    assert scores["older-south"] == 1  # 12:30 is after the reference time
    assert "cross-area-move" not in scores
    assert "missing-time" not in scores


def test_location_cycle_is_reported() -> None:
    data, config = site_inputs()
    outpatients = next(
        loc for loc in get_resources(data.locations, Location) if loc.id == "opd"
    )
    outpatients.partOf = {"reference": "Location/opd-1"}
    with pytest.raises(ValueError, match="Cycle"):
        chair = next(
            loc for loc in get_resources(data.locations, Location) if loc.id == "opd-1"
        )
        area_for_location(chair, data.locations, config)


def test_unresolved_location_is_reported() -> None:
    data, config = site_inputs()
    encounter(data, "recent").location[0].location.reference = "Location/missing"
    with pytest.raises(ValueError, match="Unresolved"):
        summarise(data, config)


def test_duplicate_bed_is_reported() -> None:
    data, config = site_inputs()
    duplicate = data.encounters.entry[0].model_copy(deep=True)
    duplicate.resource.id = "duplicate"
    data.encounters.entry.append(duplicate)
    with pytest.raises(ValueError, match="same bed"):
        summarise(data, config)


def test_multiple_active_locations_are_reported() -> None:
    data, config = site_inputs()
    recent = encounter(data, "recent")
    recent.location.append(recent.location[0].model_copy(deep=True))
    with pytest.raises(ValueError, match="multiple active locations"):
        summarise(data, config)


def test_missing_configured_area_is_reported() -> None:
    data, config = site_inputs()
    areas = {**config.areas, "W7-X": config.areas["W7-E"]}
    with pytest.raises(ValueError, match="W7-X"):
        summarise(data, config.model_copy(update={"areas": areas}))


@pytest.mark.parametrize("hours", [0, -6])
def test_nonpositive_windows_are_rejected(hours: int) -> None:
    with pytest.raises(ValueError, match="positive"):
        run(window_hours=hours)


def test_timestamp_requires_timezone() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        timestamp(datetime(2026, 10, 23, 12))


def test_output_is_aggregate_only() -> None:
    data, _ = site_inputs()
    text = json.dumps(run())
    for resource in get_resources(data.encounters, Encounter):
        assert f'"{resource.id}"' not in text
    assert all(
        set(row)
        == {
            "area",
            "occupied_beds",
            "bed_capacity",
            "occupancy_percent",
            "admissions",
            "unknown_entry_times",
            "high_acuity",
            "acuity_unknown",
        }
        for row in run()["areas"]
    )


@pytest.mark.parametrize(
    "hour,beds,admissions,high",
    [("00", 3, 3, 2), ("04", 5, 4, 4), ("08", 4, 2, 2), ("12", 4, 2, 2)],
)
def test_north_at_earlier_reference_times(
    hour: str, beds: int, admissions: int, high: int
) -> None:
    data, config = site_inputs()
    north = summarise(data, config, as_of=f"2026-10-23T{hour}:00:00Z")["areas"][0]
    assert (north["occupied_beds"], north["admissions"], north["high_acuity"]) == (
        beds,
        admissions,
        high,
    )


def test_score_goes_stale_between_reference_times() -> None:
    data, config = site_inputs()
    south_08 = summarise(data, config, as_of="2026-10-23T08:00:00Z")["areas"][1]
    south_12 = summarise(data, config)["areas"][1]
    assert south_08["high_acuity"] == 1
    assert south_12["high_acuity"] == 0


def test_reference_time_after_data_pull_is_rejected() -> None:
    data, config = site_inputs()
    with pytest.raises(ValueError, match="after the data was pulled"):
        summarise(data, config, as_of="2026-10-23T13:00:00Z")
