# Ward Monitoring on Live FHIR Data

**Level:** Intermediate

Hospital wards come under strain when demand outpaces the beds and staff available. Research on ward capacity strain links it to measures that routine electronic health record (EHR) data already holds: how many patients are on the ward, how many arrived recently, and how unwell they are ([Kerlin et al., 2014](https://doi.org/10.1513/AnnalsATS.201306-141OC); [Kohn et al., 2018](https://pmc.ncbi.nlm.nih.gov/articles/PMC6206345/)).

Measures like these are usually developed on a hospital's research database or a one-off data extract. Using them in day-to-day care means reading the same facts from the hospital's live systems, increasingly through [FHIR](https://hl7.org/fhir/), the standard API for health data, and getting the results to the people who act on them. The research doesn't stop at that point, so the software has to keep three things working:

- **Timely, repeated assessment:** the measures are recomputed from current data as the ward changes.
- **Variables from several domains:** patient movements and clinical measurements, which each hospital, and sometimes each ward, records in its own way.
- **Definitions that change:** what counts as an admission, or a high score, is refined as the research develops.

This example is a generalised ward-monitoring workflow, built with synthetic data. HealthChain reads, checks and serves the FHIR data; the research definitions stay in one small Python file you can revise without touching any of that.

**The research workflow.** At each reference time, the workflow:

1. pulls `Encounter` (hospital stays), `Location` (wards, areas and beds) and `Observation` (measurements such as a clinical score) resources from a FHIR API, or from saved files;
2. checks them against the FHIR standard before anything is counted;
3. maps the site's own location codes to research areas, and its observation code to a research variable;
4. computes occupancy, recent admissions and acuity under the current definitions;
5. repeats at later times, with revised definitions or on another site's data, and serves the summary to a dashboard.

![Ward monitoring application: FHIR data from a live API or saved files enters HealthChain, which reads and checks it with FHIRGateway, load_bundle, validation and reference resolution. Inside the HealthChain boundary, your site config maps local locations and codes and ward_definitions.py computes the measures. HealthChainAPI serves the per-area summary at GET /ward-summary to a dashboard.](../assets/images/cards/hc-flow-ward-monitoring-light.svg#only-light)
![Ward monitoring application: FHIR data from a live API or saved files enters HealthChain, which reads and checks it with FHIRGateway, load_bundle, validation and reference resolution. Inside the HealthChain boundary, your site config maps local locations and codes and ward_definitions.py computes the measures. HealthChainAPI serves the per-area summary at GET /ward-summary to a dashboard.](../assets/images/cards/hc-flow-ward-monitoring-dark.svg#only-dark)

| HealthChain does                                                            | You define                                                           |
| --------------------------------------------------------------------------- | -------------------------------------------------------------------- |
| Queries FHIR servers (`FHIRGateway`) or loads saved Bundles (`load_bundle`) | Which resources and query a site needs                               |
| Validates every resource and names the exact failing field                  | How to fix a site's non-standard export (site config)                |
| Returns typed R4B resources and resolves references (`resolve_reference`)   | Which locations form each area, and which code carries each variable |
| Serves results over HTTP (`HealthChainAPI`)                                 | The measures: windows, admission rules, thresholds                   |

!!! question "Research input boxes"

    Boxes like this mark open research decisions. The code runs with clearly
    labelled placeholders until they are agreed. R2–R3 are placeholders in
    `ward_definitions.py`; R1 is about the research context and use.

!!! question "Research input R1: research context"

    **Decide:** how to describe the research context publicly: how often wards
    need monitoring and why, why the measures need variables from several
    domains and definitions that can change, which public citations
    support it, and what the research team will use the workflow for.
    **Placeholder now:** this introduction and its two citations.

Full working example: [cookbook/ward_monitoring.py](https://github.com/healthchainai/HealthChain/tree/main/cookbook/ward_monitoring.py) (FHIR access and mapping) and [cookbook/ward_definitions.py](https://github.com/healthchainai/HealthChain/tree/main/cookbook/ward_definitions.py) (research definitions)

---

## Quick Start

**The example ward.** A made-up hospital ward, Ward 7, at noon (UTC) on 23 October 2026:

- **Three areas:** North (5 beds), South (3 beds) and one Escalation bed opened when the ward is full.
- **A day of movement:** patients have arrived, moved between beds and gone home.
- **An acuity score** for how unwell each patient is (synthetic; 3 or more is high).

![Synthetic Ward 7 at 12:00. North, 5 beds: bed 1 new, score 3; bed 2 moved within North, score 2; bed 3 new, score 4; bed 4 entry time unknown, no recent score; bed 5 empty. South, 3 beds: bed 1 new, no recent score; bed 2 new, score 1; bed 3 empty. Escalation, 1 bed: bed 1 new, score 4. Scores of 3 or more are high acuity.](../assets/images/cards/hc-flow-ward-board-light.svg#only-light)
![Synthetic Ward 7 at 12:00. North, 5 beds: bed 1 new, score 3; bed 2 moved within North, score 2; bed 3 new, score 4; bed 4 entry time unknown, no recent score; bed 5 empty. South, 3 beds: bed 1 new, no recent score; bed 2 new, score 1; bed 3 empty. Escalation, 1 bed: bed 1 new, score 4. Scores of 3 or more are high acuity.](../assets/images/cards/hc-flow-ward-board-dark.svg#only-dark)

**What the workflow does.** It reads the ward as FHIR data and summarises each area:

- **Occupied beds:** how full the area is.
- **Admissions:** patients who entered the area in the last 12 hours.
- **High acuity:** patients whose latest score is 3 or more.

**Run it.** All the data is included. From a checkout of the HealthChain repository:

```bash
pip install healthchain
python cookbook/ward_monitoring.py                       # site A
python cookbook/ward_monitoring.py --admissions all-arrivals
python cookbook/ward_monitoring.py --site b               # same result
python cookbook/ward_monitoring.py --as-of 2026-10-23T04:00:00Z
```

The first command summarises the board above, one row per area:

| Area       | Occupied beds | Capacity | Admissions (12h) | Unknown entry times | High acuity | Acuity unknown |
| ---------- | ------------- | -------- | ---------------- | ------------------- | ----------- | -------------- |
| North      | 4             | 5        | 2                | 1                   | 2           | 1              |
| South      | 2             | 3        | 2                | 0                   | 0           | 1              |
| Escalation | 1             | 1        | 1                | 0                   | 1           | 0              |

The other commands each change one thing:

- **`--admissions all-arrivals`:** a different definition of admissions.
- **`--site b`:** a second site's data format, with the same result.
- **`--as-of`:** an earlier reference time. Noon is when the data was pulled (each Bundle's `timestamp`), so it is the default.

Every case on the board is listed in the [fixture notes](https://github.com/healthchainai/HealthChain/tree/main/cookbook/data/ward_monitoring/README.md).

---

## How It Works

### Step 1: Get the FHIR data

The workflow needs three kinds of record: hospital stays (`Encounter`), the places they happen in (`Location`), and measurements taken during them (`Observation`). In a hospital these come from a live FHIR API.

[**FHIRGateway**](../reference/gateway/fhir_gateway.md) connects to it, handles authentication and returns typed `Bundles`, so each query is a fresh snapshot rather than last night's extract:

```python
from healthchain.gateway import FHIRGateway
from healthchain.gateway.clients import FHIRAuthConfig
from healthchain.fhir.r4b import Encounter

# Needs a Medplum sandbox and MEDPLUM_* in .env (see "Run the live query yourself")
gateway = FHIRGateway()
gateway.add_source(
    "medplum", FHIRAuthConfig.from_env("MEDPLUM").to_connection_string()
)
encounters = gateway.search(
    Encounter,
    {"_tag": "https://example.org/healthchain-demo|ward-monitoring-site-a"},
    source="medplum",
)
```

The rest of this cookbook loads the same Bundles from saved files with [`load_bundle`](../reference/utilities/fhir_helpers.md), so it runs offline.

```python
from healthchain.fhir import load_bundle
from cookbook.ward_monitoring import DATA_DIR, from_files, load_config

site_dir = DATA_DIR / "site_a"
encounters = load_bundle(site_dir / "encounters.json", version="R4B")
print(encounters.entry[0].resource.location[0].location.reference)

config = load_config(site_dir)
data = from_files(site_dir, config)  # encounters, locations, observations
```

```text
Location/n1
```

??? details "Run the live query yourself (Medplum)"

    Set up a free sandbox with the [Medplum guide](./setup_fhir_sandboxes.md#medplum)
    and add `MEDPLUM_*` variables to `.env`. Upload the synthetic site once,
    then query it whenever you need a fresh snapshot:

    ```bash
    healthchain seed medplum cookbook/data/ward_monitoring/site_a/medplum_upload.json
    python cookbook/ward_monitoring.py --source medplum --as-of 2026-10-23T12:00:00Z
    ```

    The upload file links the site's resources in one transaction, tags them,
    and only creates what's missing, so seeding twice is safe. `from_gateway`
    runs the three searches with the site's `search_params`, checks each
    resource with `validate_resource`, and stops if the server returns more
    than one page:

    ```python
    from cookbook.ward_monitoring import from_gateway

    live = from_gateway(gateway, "medplum", config)
    ```

    A live query is pulled *now*, so pass the fixtures' time with `--as-of` to
    compare with the offline run. A hospital site would set `search_params` to
    query by ward and date instead of a demo tag; agree that query with its
    technical team. The server assigns new resource IDs, which is why areas are
    mapped by `Location.identifier` rather than by ID.

### Step 2: Check what arrived

Hospital exports don't always follow the standard. Site B could write a bed's status as `current`, which isn't a FHIR value; the standard says `active`. Code that looks for `active` would quietly drop those patients from the count. `load_bundle` validates every resource as it loads and names the exact field that failed:

```python
from healthchain.fhir import FHIRValidationError

try:
    load_bundle(DATA_DIR / "site_b" / "encounters.json", version="R4B")
except FHIRValidationError as error:
    for issue in error.report.issues:
        print(issue.expression, "-", issue.diagnostics)
```

```text
Bundle.entry[0].resource.location[0].status - Value 'current' is not in the required value set. Allowed values: planned, active, reserved, completed
```

The quirk belongs to site B, not to the research, so the fix goes in site B's config. `from_files` applies it before validating:

```json
"location_status_map": { "current": "active" }
```

### Step 3: Map to research variables

FHIR records say "bed `W7-N-1`" or "code `ACU`"; the research talks about "North" and "acuity". Each site's config is the translation between the two, kept in one file you can review and replace. It also holds how to query the site's FHIR API. Site A's:

```json
{
  "search_params": {
    "_tag": "https://example.org/healthchain-demo|ward-monitoring-site-a"
  },
  "location_system": "https://example.org/site-a/location",
  "areas": {
    "W7-N": { "name": "North", "capacity": 5 },
    "W7-S": { "name": "South", "capacity": 3 },
    "W7-E": { "name": "Escalation", "capacity": 1 }
  },
  "acuity_code": {
    "system": "https://example.org/site-a/observation",
    "code": "ACU"
  }
}
```

To find a bed's area, we can walk up the location tree with `resolve_reference` (each `Location.partOf` points to its parent) until it reaches a configured area. The same function links each score to its stay through `Observation.encounter`, so patient movements and clinical measurements join without hand-written ID lookups:

```text
Location  W7          Ward 7
  └─ W7-N             North      ← configured area: stop here
       └─ W7-N-1      bed 1
            ↑ Encounter.location        (a stay in bed 1)
                 ↑ Observation.encounter   (a score taken during that stay)
```

Let's say Site B adds a bay between area and bed (`WEST-NORTH` → bay A → `WN-A01`); because nothing is hard-coded, the walk simply takes one more step and nothing breaks.

Each stay's bed history then becomes a list of _area visits_. Moving beds within an area keeps the original arrival time; moving to a different area starts a new visit:

```python
from healthchain.fhir import get_resources
from healthchain.fhir.r4b import Encounter
from cookbook.ward_monitoring import area_visits

for encounter in get_resources(data.encounters, Encounter)[:2]:
    for visit in area_visits(encounter, data.locations, config, data.pulled_at):
        print(encounter.id, visit.area, visit.entered_at.isoformat(), visit.present)
```

```text
recent W7-N 2026-10-23T08:00:00+00:00 True
same-area-move W7-N 2026-10-22T16:00:00+00:00 True
```

!!! question "Research input R3: the clinical variable"

    **Decide:** whether this synthetic score is a fair stand-in for the clinical variables that sit alongside occupancy, or a published score can be named; which published work supports patient acuity as part of capacity strain; and what a missing or out-of-date score should mean.
    **Placeholder now:** one synthetic 1–4 acuity score, counted per area when 3 or more; values older than 12 hours count as unknown.

### Step 4: Define the measures

Everything the research team is likely to revise lives in `ward_definitions.py`: how far back counts as "recent", what counts as an admission, and when a score counts as high. Each definition is plain Python over the area visits, and nothing in the file knows about FHIR:

```python
WINDOW_HOURS = 12  # R2: how far back counts as "recent"? Both ends included.

def admissions_still_present(visits, cutoff, as_of):
    """R2 option A: entries to the area in the window, among people still there."""
    return sum(
        v.present and v.entered_at is not None and cutoff <= v.entered_at <= as_of
        for v in visits
    )

def admissions_all_arrivals(visits, cutoff, as_of):
    """R2 option B: every entry to the area in the window, including people who left."""
    return sum(
        v.entered_at is not None and cutoff <= v.entered_at <= as_of for v in visits
    )

ACUITY_HIGH = 3            # R3 placeholder
ACUITY_MAX_AGE_HOURS = 12  # R3 placeholder
```

`summarise` applies the definitions to every configured area:

```python
import json
from cookbook.ward_monitoring import summarise

result = summarise(data, config)
print(json.dumps(result["areas"][0], indent=2))
```

```json
{
  "area": "North",
  "occupied_beds": 4,
  "bed_capacity": 5,
  "occupancy_percent": 80.0,
  "admissions": 2,
  "unknown_entry_times": 1,
  "high_acuity": 2,
  "acuity_unknown": 1
}
```

One North patient has no recorded arrival time in the area. They count towards occupancy and appear under `unknown_entry_times`, but never as an admission: the gap stays visible instead of being guessed.

!!! question "Research input R2: what counts"

    **Decide:** the unit of occupancy (beds, encounters or patients); whether an admission means people still present (A) or all arrivals (B); the window length; whether a move between beds or areas counts as a new admission; and which of these changes [Revise a definition](#revise-a-definition) should show, and why.

    **Placeholder now:** beds, option A, 12 hours, bed moves within an area don't count.

### Step 5: Serve it to a dashboard

The summary is ready; the last step is getting it to the people who use it. [`HealthChainAPI`](../reference/gateway/api.md) wraps `run` in an HTTP endpoint that a dashboard can call. With `source="medplum"`, each request queries the FHIR API again, so the dashboard always shows current data:

```python
from fastapi import Query
from healthchain.gateway import HealthChainAPI
from cookbook.ward_monitoring import run

app = HealthChainAPI(title="Ward summary")

@app.get("/ward-summary")
def ward_summary(
    site: str = "a",
    admissions: str = "still-present",
    window_hours: int = Query(default=12, gt=0),
):
    return run(site, admissions, window_hours, source="files")

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000)
```

Save it as `ward_demo_app.py` in the repository root, run it, and open `http://127.0.0.1:8000/ward-summary`. That's the whole application: FHIR in, your definitions in the middle, a summary out.

---

## Develop the Research

The application is built. The research keeps moving, and these three short sections use it the way the research will: looking back over time, revising a definition, and running on another site.

### Look back in time

_Research need: timely, repeated assessment._ A ward changes hour by hour, so the same measures are needed again and again. Pass `as_of` to compute them at any earlier time; arrivals, departures and scores are all read from their recorded times:

```python
for hour in ("00", "04", "08", "12"):
    north = summarise(data, config, as_of=f"2026-10-23T{hour}:00:00Z")["areas"][0]
    print(hour, north["occupied_beds"], north["admissions"], north["high_acuity"])
```

```text
00 3 3 2
04 5 4 4
08 4 2 2
12 4 2 2
```

| Time  | Beds | Admissions | High acuity | What happened in North                                                                       |
| ----- | ---- | ---------- | ----------- | -------------------------------------------------------------------------------------------- |
| 00:00 | 3    | 3          | 2           | Three patients, all arrived in the last 12 hours                                             |
| 04:00 | 5    | 4          | 4           | Two more arrive; one has no recorded arrival time, so isn't counted as an admission          |
| 08:00 | 4    | 2          | 2           | One goes home, one moves to South, one arrives; an earlier arrival is now outside the window |
| 12:00 | 4    | 2          | 2           | No movement                                                                                  |

Two rules keep the repeated numbers honest:

- **Scores go stale.** The patient who moved to South at 07:00 counts as high acuity at 08:00. By 12:00 their last score is more than 12 hours old (`ACUITY_MAX_AGE_HOURS`), so it counts as unknown.
- **Time only goes back.** The data was pulled at 12:00 (`data.pulled_at`). A stay with no end time is only known to be ongoing up to then, so later reference times raise an error.

Against a live server, each run is a fresh query, and the dashboard endpoint from Step 5 recomputes on every request.

### Revise a definition

_Research need: definitions that change._ Suppose the team asks whether "admissions" should count everyone who arrived in the window, or only those still on the ward. Both versions are in `ward_definitions.py`; pass the one you want:

```python
for definition in ("still-present", "all-arrivals"):
    north = summarise(data, config, admissions=definition)["areas"][0]
    print(definition, north["admissions"])
```

```text
still-present 2
all-arrivals 3
```

The difference is one patient who arrived in North at 01:00 and left at 05:00: "all-arrivals" counts them, "still-present" doesn't. Nothing else moves:

|                   | This revision                                                                                      |
| ----------------- | -------------------------------------------------------------------------------------------------- |
| Changed           | Which admission function is used (`ward_definitions.py`)                                           |
| Reused unchanged  | FHIR query or file loading, validation, reference resolution, location and code mappings, fixtures |
| Output difference | North admissions 2 → 3; every other value identical                                                |

Each definition keeps its own frozen expected output (`expected_still_present.json`, `expected_all_arrivals.json`), and the tests check both. A revision comes with a before-and-after on the same data, rather than overwriting the old result.

### Run on another site

_Research need: variables from several domains, each recorded in its own way._ Another hospital, or another ward, records the same facts differently. Site B is the same synthetic ward written in a different local style, and only its config changes:

|                      | Site A                   | Site B                        |
| -------------------- | ------------------------ | ----------------------------- |
| Location identifiers | `W7-N`, `W7-N-1` …       | `WEST-NORTH`, `WN-A01` …      |
| Hierarchy            | ward → area → bed        | ward → area → bay → bed       |
| Acuity code          | `site-a/observation#ACU` | `site-b/flowsheet#DEPENDENCY` |
| Location status      | standard                 | `current` (fixed in config)   |

```python
site_b = DATA_DIR / "site_b"
config_b = load_config(site_b)
print(summarise(from_files(site_b, config_b), config_b) == summarise(data, config))
```

```text
True
```

Validation is what makes the swap safe. Without the check in Step 2, site B's patients with status `current` would have vanished from the count, and the two sites would disagree without any error.

### What changed between runs

Every run above used the same research code. This is what changed each time:

| Run                                  | What changed                                          | Research code changed? | Result                              |
| ------------------------------------ | ----------------------------------------------------- | ---------------------- | ----------------------------------- |
| Saved files → live FHIR API (Step 1) | Data source                                           | No                     | Identical summary                   |
| Earlier reference times              | `as_of`                                               | No                     | The ward as it was; scores go stale |
| Still present → all arrivals         | One definition in `ward_definitions.py`               | That definition only   | North admissions 2 → 3              |
| Site A → site B                      | Site config: identifiers, hierarchy, code, status fix | No                     | Identical summary                   |

---

## What You've Built

The research definitions never touch FHIR. Moving them from saved files to a live server, or to a data source recorded differently, changes nothing in them, and the results reach a dashboard through a standard HTTP endpoint.

| Research need                  | How this example shows it                                                                                                                                                                                                |
| ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Timely, repeated assessment    | `FHIRGateway` queries current data instead of waiting for an extract; measures recompute at any reference time; scores have a freshness rule; an endpoint recomputes on request                                          |
| Variables from several domains | Patient flow (`Encounter`, `Location`) and a clinical variable (`Observation`) are joined with `resolve_reference`; each site's codes are mapped in config, so adding a domain means adding a resource type and its code |
| Definitions that change        | Definitions live in their own file, apart from HealthChain's loading, validation and reference resolution; a revision changes that file only and is checked against its own frozen output                                |

!!! tip "Next Steps"

    - Point `--source medplum` at your own sandbox and compare its output with the offline run.
    - Add a site: copy `site_a/config.json` and change the identifiers, codes and capacities.
    - Add a domain: search one more resource type, add its code to the site config, and count it in `ward_definitions.py`.
    - Comment on the open research inputs in [issue #273](https://github.com/healthchainai/HealthChain/issues/273).
