# Ward Monitoring on Live FHIR Data

**Level:** Intermediate

Ward strain is a concept used in healthcare research to describe how busy a hospital ward is. Specifically, ward strain describes the extent to which an overwhelmed hospital ward is no longer able to safely deliver care. Through qualitative research, such as interviews with ward staff and hospital managers, the factors which cause ward strain have become increasingly well understood. Typical factors that cause increasing ward strain include: number of patients on a ward, new patients being admitted to the ward, average illness severity of patients across the ward, number of staff, and staff workload ([Page et al., 2024](https://doi.org/10.1136/bmjqs-2023-016686)). Retrospective evidence shows that patients admitted to hospital areas with high ward strain have an increased risk of death ([Gabler et al., 2013](https://doi.org/10.1164/rccm.201304-0622OC)); however, technological solutions for live monitoring of ward strain have been lacking, limiting the ability of hospitals to intervene in real time.

The individual metrics required to measure ward strain (e.g. newly admitted patients, patient illness severity measures) are already held within widely used electronic health record (EHR) databases. However, these EHRs are primarily designed for keeping records for individual patients, and do not include any interfaces or dashboards specifically designed to allow clinicians (e.g. ward nurses or doctors) or managers to monitor ward strain.

Recently, healthcare researchers have started to attempt quantitative measurement of ward strain by combining these individual metrics and averaging them across a hospital ward ([Kohn et al., 2018](https://doi.org/10.1007/s11606-018-4564-x)). Measurements like these are usually developed on a hospital's research database or with a one-off data extract. These research efforts have not yet progressed into a system that can be used in daily practice by healthcare workers. To begin to use them in day-to-day care will mean reading the same facts from the hospital's live systems, increasingly through [FHIR](https://hl7.org/fhir/), the standard API for health data, and getting the results to the people who act on them. One major challenge is that the underlying data is constantly changing, so the software has to keep three things working:

1. **Timely, repeated assessment:** the metrics must be recomputed from current data as the ward changes.

    _For example, hour by hour, which patients are on the ward can change, as can the information used to calculate their illness severity (such as heart rate and blood pressure)._

2. **Variables from several domains:** the required individual metrics may be recorded in different databases in different hospitals, or recorded in different ways by different wards.

    _For example, an intensive care unit may record its patients' illness severity scores in a different EHR to the one used by the general hospital wards._

3. **Definitions that change:** users will demand metrics which can evolve as healthcare research progresses or ways of working change.

    _For example, NEWS2 (National Early Warning Score 2) is a standard illness severity (acuity) metric used across England and Wales, but its definition changed when hospitals moved from NEWS to NEWS2, and will likely change again as new severity scores are developed. Or staff working patterns evolve from 12-hour shifts to 8-hour shifts, and users request a "patient admissions per shift" metric that counts admissions in an 8-hour window rather than the previous 12 hours._

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

Full working example: [cookbook/ward_monitoring.py](https://github.com/healthchainai/HealthChain/tree/main/cookbook/ward_monitoring.py) (FHIR access and mapping) and [cookbook/ward_definitions.py](https://github.com/healthchainai/HealthChain/tree/main/cookbook/ward_definitions.py) (research definitions)

---

## Quick Start

The following is based on a fictional example scenario based on a real hospital's Intensive Care Unit (ICU). The ICU contains three areas: North (12 beds), South (18 beds) and one escalation bay (6 beds) which can be used when the ICU is at full capacity.

The Nurse in Charge of the ICU will assess several factors at the beginning of the shift, and at several points throughout the day:

- **Bed occupancy:** how many patients are currently on the ICU and how many beds are available for new admissions, including assessing whether the escalation beds may be required on this shift.
- **Patient acuity (illness severity):** how unwell are the patients currently admitted? In ICU, patients will typically be assigned a "level" based on the number of life support machines or interventions used (e.g. "level 2", "level 3"). On general NHS hospital wards, the more complex NEWS2 score is calculated instead. NEWS2 is derived from the patient's vital observations: heart rate, blood pressure, oxygen levels, breathing rate, temperature, and level of consciousness ([Royal College of Physicians, 2017](https://www.rcp.ac.uk/improving-care/resources/national-early-warning-score-news-2/)). A higher NEWS2 score indicates a more unwell patient. NEWS2 is used for the purposes of this example.
- **Patient flow:** the number of new patients being admitted to the ward, patients who need to be moved to different beds, and patients who are due to be discharged or stepped down to the ward.

To keep the tables short, the example board below is a cut-down version of the ICU at noon (UTC) on 23 October 2026: North 5 beds, South 3, Escalation 1.

![Synthetic ICU at 12:00. North, 5 beds: bed 1 new, NEWS2 7; bed 2 moved within North, NEWS2 3; bed 3 new, NEWS2 9; bed 4 entry time unknown, no recent score; bed 5 empty. South, 3 beds: bed 1 new, no recent score; bed 2 new, NEWS2 2; bed 3 empty. Escalation, 1 bed: bed 1 new, NEWS2 10. NEWS2 of 7 or more is high acuity.](../assets/images/cards/hc-flow-ward-board-light.svg#only-light)
![Synthetic ICU at 12:00. North, 5 beds: bed 1 new, NEWS2 7; bed 2 moved within North, NEWS2 3; bed 3 new, NEWS2 9; bed 4 entry time unknown, no recent score; bed 5 empty. South, 3 beds: bed 1 new, no recent score; bed 2 new, NEWS2 2; bed 3 empty. Escalation, 1 bed: bed 1 new, NEWS2 10. NEWS2 of 7 or more is high acuity.](../assets/images/cards/hc-flow-ward-board-dark.svg#only-dark)

**What the workflow does.** It reads the ward as FHIR data and summarises each area:

- **Occupied beds:** how many patients are currently on the ward.
- **Admissions:** patients who have moved onto the ward in the last 12 hours.
- **High acuity:** patients whose latest NEWS2 score is 7 or more.

**Run it.** All the data is included. From a checkout of the HealthChain repository:

```bash
pip install healthchain
python cookbook/ward_monitoring.py                       # site A
python cookbook/ward_monitoring.py --window-hours 8
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

- **`--window-hours 8`:** a different definition of admissions: an 8-hour shift instead of 12.
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
Location  W7          ICU
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

### Step 4: Define the measures

Everything the research team is likely to revise lives in `ward_definitions.py`: how far back counts as "recent", what counts as an admission, and when a score counts as high. Each definition is plain Python over the area visits, and nothing in the file knows about FHIR.

The current definitions:

- **Window:** 12 hours (the length of the shift for the ward/ICU nurses and doctors).
- **Admissions, option A (still present):** entries to the area in the window, among people still there.
- **Admissions, option B (all arrivals):** every entry to the area in the window, including people who have since left.
- **High patient acuity:** a NEWS2 score of 7 or more.
- **Freshness:** scores older than 12 hours count as unknown.

```python
WINDOW_HOURS = 12  # one shift; both ends included

def admissions_still_present(visits, cutoff, as_of):
    """Option A: entries to the area in the window, among people still there."""
    return sum(
        v.present and v.entered_at is not None and cutoff <= v.entered_at <= as_of
        for v in visits
    )

def admissions_all_arrivals(visits, cutoff, as_of):
    """Option B: every entry to the area in the window, including people who left."""
    return sum(
        v.entered_at is not None and cutoff <= v.entered_at <= as_of for v in visits
    )

ACUITY_HIGH = 7            # NEWS2 of 7 or more is high
ACUITY_MAX_AGE_HOURS = 12  # older scores count as unknown
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

| Time  | Beds | Admissions | High acuity | What happened in North                                                                                              |
| ----- | ---- | ---------- | ----------- | ------------------------------------------------------------------------------------------------------------------- |
| 00:00 | 3    | 3          | 2           | Three patients, all arrived in the last 12 hours                                                                    |
| 04:00 | 5    | 4          | 4           | Two more arrive; one has no recorded arrival time, so isn't counted as an admission                                 |
| 08:00 | 4    | 2          | 2           | One moves to a general hospital ward, one moves to South, one arrives; an earlier arrival is now outside the window |
| 12:00 | 4    | 2          | 2           | No movement                                                                                                         |

Two rules keep the repeated numbers honest:

- **Scores go stale.** The patient who moved to South at 07:00 counts as high acuity at 08:00. By 12:00 their last score is more than 12 hours old (`ACUITY_MAX_AGE_HOURS`), so it counts as unknown.
- **Time only goes back.** The data was pulled at 12:00 (`data.pulled_at`). A stay with no end time is only known to be ongoing up to then, so later reference times raise an error.

Against a live server, each run is a fresh query, and the dashboard endpoint from Step 5 recomputes on every request.

### Revise a definition

_Research need: definitions that change._ Suppose the ICU moves from 12-hour to 8-hour shifts, and the team wants "admissions" to mean admissions per shift. In `ward_definitions.py` that is one line, `WINDOW_HOURS = 8`. To compare both versions on the same data, pass `window_hours`:

```python
for hours in (12, 8):
    north = summarise(data, config, window_hours=hours)["areas"][0]
    print(hours, north["admissions"])
```

```text
12 2
8 1
```

The difference is one patient who arrived in North at exactly 00:00: inside a 12-hour window, outside an 8-hour one (04:00–12:00). A South patient who arrived at 04:00 sits on the new boundary and still counts, because both ends are included. Nothing else moves:

|                   | This revision                                                                                        |
| ----------------- | ---------------------------------------------------------------------------------------------------- |
| Changed           | `WINDOW_HOURS` in `ward_definitions.py`: 12 → 8                                                      |
| Reused unchanged  | FHIR query or file loading, validation, reference resolution, location and code mappings, test data |
| Output difference | North admissions 2 → 1; every other value identical                                                  |

Each definition keeps its own frozen expected output (`expected_still_present.json`, `expected_window_8h.json`), and the tests check both. A revision comes with a before-and-after on the same data, rather than overwriting the old result. The two admission rules from Step 4 work the same way: `--admissions all-arrivals` has its own expected output too.

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
| 12h → 8h window                      | One definition in `ward_definitions.py`               | That definition only   | North admissions 2 → 1              |
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

## References

- Gabler, N. B. _et al._ (2013) "Mortality among patients admitted to strained intensive care units", _American Journal of Respiratory and Critical Care Medicine_, 188(7), pp. 800–806. [doi:10.1164/rccm.201304-0622OC](https://doi.org/10.1164/rccm.201304-0622OC)
- Kohn, R. _et al._ (2018) "Ward Capacity Strain: A Novel Predictor of 30-Day Hospital Readmissions", _Journal of General Internal Medicine_, 33(11), pp. 1851–1853. [doi:10.1007/s11606-018-4564-x](https://doi.org/10.1007/s11606-018-4564-x)
- Page, B. _et al._ (2024) "Health services under pressure: a scoping review and development of a taxonomy of adaptive strategies", _BMJ Quality and Safety_, 33(11), pp. 738–747. [doi:10.1136/bmjqs-2023-016686](https://doi.org/10.1136/bmjqs-2023-016686)
- Royal College of Physicians (2017) _National Early Warning Score (NEWS) 2: Standardising the assessment of acute-illness severity in the NHS_. Updated report of a working party. [rcp.ac.uk](https://www.rcp.ac.uk/improving-care/resources/national-early-warning-score-news-2/)
