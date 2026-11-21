import json

import pytest
from fastapi.testclient import TestClient

from cookbook.ward_monitoring import (
    DATA_DIR,
    SiteData,
    create_app,
    from_files,
    from_gateway,
    load_config,
    run,
    summarise,
    timestamp,
)
from healthchain.fhir import FHIRValidationError
from healthchain.fhir.r4b import Bundle, Encounter, Location, Observation


def site_inputs(site: str = "a") -> tuple:
    site_dir = DATA_DIR / f"site_{site}"
    config = load_config(site_dir)
    return from_files(site_dir, config), config


class StubGateway:
    """Answers FHIRGateway.search from in-memory Bundles."""

    def __init__(self, data: SiteData) -> None:
        self.bundles = {
            Encounter: data.encounters,
            Location: data.locations,
            Observation: data.observations,
        }

    def search(
        self,
        resource_type: type,
        params: dict,
        source: str,
        follow_pagination: bool = False,
    ) -> Bundle:
        return self.bundles[resource_type].model_copy(deep=True)


@pytest.mark.parametrize("site", ["a", "b"])
@pytest.mark.parametrize(
    "admissions,window_hours,acuity_high,expected",
    [
        ("still-present", 12, 7, "expected_still_present.json"),
        ("all-arrivals", 12, 7, "expected_all_arrivals.json"),
        ("still-present", 8, 7, "expected_window_8h.json"),
        ("still-present", 12, 5, "expected_acuity_5.json"),
    ],
)
def test_both_sites_match_hand_derived_results(
    site: str, admissions: str, window_hours: int, acuity_high: int, expected: str
) -> None:
    assert run(
        site=site,
        admissions=admissions,
        window_hours=window_hours,
        acuity_high=acuity_high,
    ) == json.loads((DATA_DIR / expected).read_text())


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


def test_site_b_status_fails_validation_without_mapping() -> None:
    site_dir = DATA_DIR / "site_b"
    config = load_config(site_dir).model_copy(update={"location_status_map": {}})
    with pytest.raises(FHIRValidationError, match=r"location\[0\]\.status"):
        from_files(site_dir, config)


def test_gateway_input_matches_file_input() -> None:
    data, config = site_inputs()
    from_server = from_gateway(StubGateway(data), "stub", config)
    as_of = timestamp("2026-10-23T12:00:00Z")
    assert summarise(from_server, config, as_of=as_of) == summarise(data, config)


def test_summary_endpoint_serves_the_summary() -> None:
    client = TestClient(create_app())
    response = client.get("/ward-summary", params={"acuity_high": 5})
    assert response.status_code == 200
    assert response.json() == json.loads(
        (DATA_DIR / "expected_acuity_5.json").read_text()
    )
    assert client.get("/ward-summary", params={"acuity_high": 21}).status_code == 422
