# Ward Monitoring on Live FHIR Data

## Research Context

Ward strain is a concept used in healthcare research to describe how busy a hospital ward is. Specifically, ward strain describes the extent to which an overwhelmed hospital ward is no longer able to safely deliver care. Through qualitative research, such as interviews with ward staff and hospital managers, the factors which cause ward strain have become increasingly well understood. Typical factors that cause increasing ward strain include: number of patients on a ward, new patients being admitted to the ward, average illness severity of patients across the ward, number of staff, and staff workload ([Page et al., 2024](https://doi.org/10.1136/bmjqs-2023-016686)). Retrospective evidence shows that patients admitted to hospital areas with high ward strain have an increased risk of death ([Gabler et al., 2013](https://doi.org/10.1164/rccm.201304-0622OC)); however, technological solutions for live monitoring of ward strain have been lacking, limiting the ability of hospitals to intervene in real time.

The individual metrics required to measure ward strain (e.g. newly admitted patients, patient illness severity measures) are already held within widely used electronic health record (EHR) databases. However, these EHRs are primarily designed for keeping records for individual patients, and do not include any interfaces or dashboards specifically designed to allow clinicians (e.g. ward nurses or doctors) or managers to monitor ward strain.

Recently, healthcare researchers have started to attempt quantitative measurement of ward strain by combining these individual metrics and averaging them across a hospital ward ([Kohn et al., 2018](https://doi.org/10.1007/s11606-018-4564-x)). Measurements like these are usually developed on a hospital's research database or with a one-off data extract. These research efforts have not yet progressed into a system that can be used in daily practice by healthcare workers. To begin to use them in day-to-day care will mean reading the same facts from the hospital's live systems, increasingly through [FHIR](https://hl7.org/fhir/), the standard API for health data, and getting the results to the people who act on them. One major challenge is that the underlying data is constantly changing, so the software has to keep three things working:

1. **Timely, repeated assessment:** the metrics must be recomputed from current data as the ward changes.<br>_e.g. hour by hour, which patients are on the ward can change, as can the information used to calculate their illness severity (such as heart rate and blood pressure)._

1. **Variables recorded differently across systems:** the required individual metrics may be recorded in different databases in different hospitals, or recorded in different ways by different wards.<br>_e.g. an intensive care unit may record its patients' illness severity scores in a different EHR to the one used by the general hospital wards._

1. **Definitions that change:** users will demand metrics which can evolve as healthcare research progresses or ways of working change.<br>_e.g. [NEWS2 (National Early Warning Score 2)](https://www.rcp.ac.uk/resources/national-early-warning-score-news-2/) is a standard illness severity (acuity) metric used across England and Wales, but its definition changed when hospitals moved from NEWS to NEWS2, and will likely change again as new severity scores are developed. Or staff working patterns evolve from 12-hour shifts to 8-hour shifts, and users request a "patient admissions per shift" metric that counts admissions in an 8-hour window rather than the previous 12 hours._

### Example Scenario

The following is based on a fictional example scenario based on a real hospital's Intensive Care Unit (ICU). The ICU contains three areas: North (12 beds), South (18 beds) and one escalation bay (6 beds) which can be used when the ICU is at full capacity.

The Nurse in Charge of the ICU will assess several factors at the beginning of the shift, and at several points throughout the day:

- **Bed occupancy:** how many patients are currently on the ICU and how many beds are available for new admissions, including assessing whether the escalation beds may be required on this shift.
- **Patient acuity (illness severity):** how unwell are the patients currently admitted? In ICU, patients will typically be assigned a "level" based on the number of life support machines or interventions used (e.g. "level 2", "level 3"). On general NHS hospital wards, the more complex NEWS2 score is calculated instead. NEWS2 is derived from the patient's vital observations: heart rate, blood pressure, oxygen levels, breathing rate, temperature, and level of consciousness ([Royal College of Physicians, 2017](https://www.rcp.ac.uk/resources/national-early-warning-score-news-2/)). A higher NEWS2 score indicates a more unwell patient. NEWS2 is used for the purposes of this example.
- **Patient flow:** the number of new patients being admitted to the ward, patients who need to be moved to different beds, and patients who are due to be discharged or stepped down to the ward.

The board below shows the ICU as the Nurse in Charge might see it at noon (UTC) on 23 October 2026. To keep the example's tables short, it is cut down to North 5 beds, South 3, Escalation 1.

![Synthetic ICU at 12:00, drawn as a floor plan. North, 5 beds: bed 1 new, NEWS2 7; bed 2 moved within North, NEWS2 3; bed 3 new, NEWS2 9; bed 4 entry time unknown, no recent score; bed 5 empty. South, 3 beds: bed 1 new, no recent score; bed 2 new, NEWS2 2; bed 3 empty. Escalation, 1 bed: bed 1 new, NEWS2 10. NEWS2 of 7 or more is high acuity.](../assets/images/cards/hc-flow-ward-board-light.svg#only-light)
![Synthetic ICU at 12:00, drawn as a floor plan. North, 5 beds: bed 1 new, NEWS2 7; bed 2 moved within North, NEWS2 3; bed 3 new, NEWS2 9; bed 4 entry time unknown, no recent score; bed 5 empty. South, 3 beds: bed 1 new, no recent score; bed 2 new, NEWS2 2; bed 3 empty. Escalation, 1 bed: bed 1 new, NEWS2 10. NEWS2 of 7 or more is high acuity.](../assets/images/cards/hc-flow-ward-board-dark.svg#only-dark)

### Workflow

This example is built with synthetic data and draws on an ongoing ward monitoring research collaboration. It turns each of the Nurse in Charge's checks into a measure per area, computed from records the hospital's EHR already holds:

| Nurse in Charge's check | FHIR records used                                                                                                                                     | Measure per area                                                       |
| ----------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------- |
| Bed occupancy           | Hospital stays ([`Encounter`](https://hl7.org/fhir/R4/encounter.html)) and the beds they are in ([`Location`](https://hl7.org/fhir/R4/location.html)) | Occupied beds: how many patients are currently on the ward             |
| Patient flow            | When each stay entered the area ([`Encounter.location`](https://hl7.org/fhir/R4/encounter-definitions.html#Encounter.location) periods)               | Admissions: patients who have moved onto the ward in the last 12 hours |
| Patient acuity          | Each patient's latest NEWS2 score ([`Observation`](https://hl7.org/fhir/R4/observation.html))                                                         | High acuity: patients whose latest NEWS2 score is 7 or more            |

The synthetic records come in two versions, as two hospitals might hold the same ICU. Site A follows the FHIR standard closely. Site B uses its own bed and score codes, groups beds into bays, and marks a patient in a bed with a non-standard status. The same workflow handles both.

At each check (the _reference time_), the workflow runs five steps:

1. **Read** (HealthChain): pull the stays, locations and NEWS2 observations from the hospital's FHIR API.
2. **Check** (HealthChain): validate every record against the FHIR standard, so a non-standard export fails loudly instead of silently dropping patients from the count.
3. **Map** (site config): translate the site's own bed codes into research areas, and its local score code into NEWS2.
4. **Compute** (`ward_definitions.py`): apply the current definitions (time window, admission rule, acuity threshold) to give the three measures per area.
5. **Serve** (HealthChain): return the per-area summary to a dashboard. The next check reruns the cycle on current data.

![Ward monitoring architecture: records from a hospital FHIR API enter HealthChain, which reads them with FHIRGateway, validates them and resolves references. Inside the HealthChain boundary sits the project logic: a site config, then ward_definitions.py. HealthChainAPI serves the per-area summary to a dashboard.](../assets/images/cards/hc-flow-ward-monitoring-light.svg#only-light)
![Ward monitoring architecture: records from a hospital FHIR API enter HealthChain, which reads them with FHIRGateway, validates them and resolves references. Inside the HealthChain boundary sits the project logic: a site config, then ward_definitions.py. HealthChainAPI serves the per-area summary to a dashboard.](../assets/images/cards/hc-flow-ward-monitoring-dark.svg#only-dark)

HealthChain handles everything that touches FHIR. The project's own logic sits in two small files: a site config for one hospital's local names, and `ward_definitions.py`, which holds the research definitions as plain Python with no FHIR in it. Keeping them apart matters because they change for different reasons:

- The definitions change as the research does (a new shift pattern, a new severity score), and each revision needs checking against the previous results.
- The mapping changes when the workflow moves to another hospital or ward.

Mixed together, every research revision would mean retesting data access, and every new site would mean editing the research code. With HealthChain holding the FHIR boundary, a research team can revise a definition or add a hospital by editing one small file, compare the result with the last run, and keep the same validated path from the hospital's records to the ward's dashboard.

| HealthChain handles                                                                                                                                                         | The project defines                                                  |
| --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------- |
| Queries FHIR servers ([`FHIRGateway`](../reference/gateway/fhir_gateway.md)) or loads saved Bundles ([`load_bundle()`](../reference/utilities/fhir_helpers.md#load_bundle)) | Which resources and query a site needs                               |
| Validates every resource and names the exact failing field                                                                                                                  | How to fix a site's non-standard export (site config)                |
| Returns typed [FHIR R4](https://hl7.org/fhir/R4/) resources and resolves references ([`resolve_reference()`](../reference/utilities/fhir_helpers.md#resolve_reference))     | Which locations form each area, and which code carries each variable |
| Serves results over HTTP ([`HealthChainAPI`](../reference/gateway/api.md))                                                                                                  | The measures: windows, admission rules, thresholds                   |

Full working example: [cookbook/ward_monitoring.py](https://github.com/healthchainai/HealthChain/tree/main/cookbook/ward_monitoring.py) (FHIR access and mapping) and [cookbook/ward_definitions.py](https://github.com/healthchainai/HealthChain/tree/main/cookbook/ward_definitions.py) (research definitions).

---

## Setup

The example and its data live in the HealthChain repository:

```bash
git clone https://github.com/healthchainai/HealthChain.git
cd HealthChain
uv sync  # or: pip install .
```

## Quick Start

Run the workflow on the saved synthetic ICU records:

```bash
python cookbook/ward_monitoring.py
```

This serves the ward summary at <http://127.0.0.1:8000/ward-summary>, the endpoint a dashboard frontend would call at each of the Nurse in Charge's checks. Every request reruns the workflow.

The command also prints the summary at startup. By default it shows the board above at the moment the records were saved (23 October 2026, 12:00 UTC), one row per area:

| Area       | Occupied beds | Capacity | Admissions (12h) | Unknown entry times | High acuity | Acuity unknown |
| ---------- | ------------- | -------- | ---------------- | ------------------- | ----------- | -------------- |
| North      | 4             | 5        | 2                | 1                   | 2           | 1              |
| South      | 2             | 3        | 2                | 0                   | 0           | 1              |
| Escalation | 1             | 1        | 1                | 0                   | 1           | 0              |

The endpoint takes four parameters:

| Parameter      | Default         | What it changes                                   |
| -------------- | --------------- | ------------------------------------------------- |
| `as_of`        | data pull time  | Reference time of the check (not after the pull)  |
| `window_hours` | `12`            | Admissions window, e.g. `8` for an 8-hour shift   |
| `admissions`   | `still-present` | Admission rule: `still-present` or `all-arrivals` |
| `site`         | `a`             | Site format: `a` or `b`, same ICU and same result |

To try them, open <http://127.0.0.1:8000/docs>, choose **GET /ward-summary**, then **Try it out**. For example, set `as_of` to `2026-10-23T04:00:00Z` to see the ICU at 04:00.

Stop the server with **Ctrl+C**; to print the JSON once without serving, add `--json`. Every case on the board is listed in the [fixture notes](https://github.com/healthchainai/HealthChain/tree/main/cookbook/data/ward_monitoring/README.md).

---

## How It Works

The Quick Start ran the whole workflow in one call, the steps below take that call apart in the order the workflow runs: read the records, check them, map them to the ICU's areas, compute the measures and serve the summary.

The project setup is small, and each part has one job:

```text
cookbook/
├── ward_monitoring.py      # reads the hospital's records and serves the summary
├── ward_definitions.py     # the research definitions, in plain Python
└── data/ward_monitoring/
    ├── site_a/             # one hospital: its saved records and config
    └── site_b/             # a second hospital: same ICU, different conventions
```

A research team spends most of its time in `ward_definitions.py` and the config files. HealthChain carries the FHIR work inside `ward_monitoring.py`.

### Step 1: Read the FHIR data

The Nurse in Charge takes in the board at a glance, but the hospital holds that picture as separate FHIR records, or [**Resources**](https://hl7.org/fhir/R4/resource.html), grouped into [**Bundles**](https://hl7.org/fhir/R4/bundle.html). We need three kinds:

- [**Encounter**](https://hl7.org/fhir/R4/encounter.html): hospital stays, for who is on the ICU
- [**Location**](https://hl7.org/fhir/R4/location.html): beds and areas, for where they are
- [**Observation**](https://hl7.org/fhir/R4/observation.html): measurements, for each patient's NEWS2 score

The project has two loading functions that return the same thing: `from_files` for synthetic or local data, and `from_gateway` for a [hospital's FHIR API](#use-a-live-fhir-source). This example loads a saved snapshot of the synthetic ICU at noon on 23 October, along with the site's config, which holds that hospital's own bed names and codes:

```python
from cookbook.ward_monitoring import DATA_DIR, from_files, load_config

site_dir = DATA_DIR / "site_a"
config = load_config(site_dir)
data = from_files(site_dir, config)
```

Raw FHIR data arrives as long, nested, messy JSON. [`load_bundle()`](../reference/utilities/fhir_helpers.md#load_bundle), which `from_files` uses, turns it into Pydantic models and Python types such as `datetime`, so the records are easy to navigate:

=== "Raw FHIR JSON"

    ``` { .json .scroll-code }
    {
      "resourceType": "Bundle",
      "type": "collection",
      "timestamp": "2026-10-23T12:00:00Z",
      "entry": [
        {
          "fullUrl": "https://example.org/site-a/fhir/Encounter/recent",
          "resource": {
            "resourceType": "Encounter",
            "id": "recent",
            "identifier": [
              {
                "system": "https://example.org/site-a/encounter",
                "value": "recent"
              }
            ],
            "status": "in-progress",
            "class": {
              "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
              "code": "IMP"
            },
            "subject": {
              "identifier": {
                "system": "https://example.org/site-a/patient",
                "value": "P01"
              }
            },
            "period": {
              "start": "2026-10-23T07:30:00Z"
            },
            "location": [
              {
                "location": {
                  "reference": "Location/n1"
                },
                "status": "active",
                "period": {
                  "start": "2026-10-23T08:00:00Z"
                }
              }
            ]
          }
        }
      ]
    }
    ```

=== "After load_bundle"

    ```python
    stay = data.encounters.entry[0].resource  # a typed Encounter

    stay.status                          # 'in-progress'
    stay.location[0].location.reference  # 'Location/n1'
    stay.location[0].period.start        # datetime: 2026-10-23 08:00:00+00:00
    ```

### Step 2: Check what arrived

Hospital data don't always follow the standard, which makes integrating records across sites and systems painful: each site has its own quirks, and each quirk tends to end up hard-coded into the logic. For example, site B, the second hospital in this example, marks a patient in a bed as `current`, whereas the FHIR spec will only accept `active`.

As well as converting records, `load_bundle()` checks each one against the FHIR standard, so a quirk like this surfaces as soon as the data loads, with the exact field named:

```python
from healthchain.fhir import FHIRValidationError, load_bundle

try:
    load_bundle(DATA_DIR / "site_b" / "encounters.json", version="R4B")
except FHIRValidationError as error:
    for issue in error.report.issues:
        print(issue.expression, "-", issue.diagnostics)
```

```text
Bundle.entry[0].resource.location[0].status - Value 'current' is not in the required value set. Allowed values: planned, active, reserved, completed
```

[`FHIRValidationError`](../reference/utilities/fhir_helpers.md#load_bundle) collects every problem in the Bundle into one report, so adding a new site means working through a single list of its quirks, rather than finding them one at a time when the data looks wrong on the other side. The fix is one line in site B's config, not a special case in the logic:

```json
"location_status_map": { "current": "active" }
```

`from_files` applies the config before validating, so site B loads as standard FHIR and everything downstream treats it like any other site:

```python
site_b_dir = DATA_DIR / "site_b"
site_b_config = load_config(site_b_dir)
site_b_data = from_files(site_b_dir, site_b_config)
print(site_b_data.encounters.entry[0].resource.location[0].status)
```

```text
active
```

See [**Validation Reference**](../reference/utilities/fhir_helpers.md#validation-loading) for more detail on what these checks cover.

### Step 3: Map to research variables

Passing structural validation doesn't make data ready for research. FHIR checks the shape of a record, but not the names inside it, and every site has its own internal jargon. What shows up as "bed `W7-N-1`" or "code `ACU`" in FHIR needs to be converted to "North" and "acuity". At site B, that same bed may be referred to as "bed `WN-A01`" and "code `DEPENDENCY`".

| In the research           | Site A   | Site B       |
| ------------------------- | -------- | ------------ |
| North                     | `W7-N`   | `WEST-NORTH` |
| South                     | `W7-S`   | `WEST-SOUTH` |
| Escalation                | `W7-E`   | `WEST-SURGE` |
| Acuity score (NEWS2)      | `ACU`    | `DEPENDENCY` |
| Patient in a bed (status) | `active` | `current`    |

To keep track of these mappings, we'll use a config. Each site's config is the translation between the research variable and FHIR, kept in one file that can be easily reviewed and replaced, while everything else stays the same:

=== "Site A"

    ```json
    {
      "site": "Site A",
      // How to query this site's FHIR API
      "search_params": {
        "_tag": "https://example.org/healthchain-demo|ward-monitoring-site-a"
      },
      // The identifier system that holds this site's location codes
      "location_system": "https://example.org/site-a/location",
      // Local area codes, translated to research areas
      "areas": {
        "W7-N": { "name": "North", "capacity": 5 },
        "W7-S": { "name": "South", "capacity": 3 },
        "W7-E": { "name": "Escalation", "capacity": 1 }
      },
      // The local code that carries the NEWS2 score
      "acuity_code": {
        "system": "https://example.org/site-a/observation",
        "code": "ACU"
      },
      // Format fixes from Step 2 (site A has none)
      "location_status_map": {}
    }
    ```

=== "Site B"

    ```json
    {
      "site": "Site B",
      // How to query this site's FHIR API
      "search_params": {
        "_tag": "https://example.org/healthchain-demo|ward-monitoring-site-b"
      },
      // The identifier system that holds this site's location codes
      "location_system": "https://example.org/site-b/bed-board",
      // Local area codes, translated to research areas
      "areas": {
        "WEST-NORTH": { "name": "North", "capacity": 5 },
        "WEST-SOUTH": { "name": "South", "capacity": 3 },
        "WEST-SURGE": { "name": "Escalation", "capacity": 1 }
      },
      // The local code that carries the NEWS2 score
      "acuity_code": {
        "system": "https://example.org/site-b/flowsheet",
        "code": "DEPENDENCY"
      },
      // Format fixes from Step 2
      "location_status_map": { "current": "active" }
    }
    ```

Other mapping quirks can be more subtle. For example, to count the NEWS2 score of 7 from North bed 1 as "high acuity in North", the workflow has to know which area it came from, and that information isn't in the record. Each record only points to the next one through a reference field:

| Record                    | Reference field        | Points to (site A)    |
| ------------------------- | ---------------------- | --------------------- |
| `Observation` (score 7)   | `encounter`            | `Encounter/recent`    |
| `Encounter` (the stay)    | `location[0].location` | `Location/n1`         |
| `Location` (bed `W7-N-1`) | `partOf`               | `Location/w7-n`       |
| `Location` (area `W7-N`)  | —                      | North, via the config |

Here is that chain we'd walk through for the same patient at two different hospital sites. Site B has an extra bay between the bed and the area:

![The same NEWS2 score of 7 at two hospitals. Site A: the score links to the stay, the stay to bed W7-N-1, the bed to area W7-N. Site B: the score, coded DEPENDENCY, links to the stay, the stay to bed WN-A01, the bed to bay A, the bay to area WEST-NORTH. resolve_reference follows each link, and each site's config translates its area to the research area North.](../assets/images/cards/hc-flow-ward-links-light.svg#only-light)
![The same NEWS2 score of 7 at two hospitals. Site A: the score links to the stay, the stay to bed W7-N-1, the bed to area W7-N. Site B: the score, coded DEPENDENCY, links to the stay, the stay to bed WN-A01, the bed to bay A, the bay to area WEST-NORTH. resolve_reference follows each link, and each site's config translates its area to the research area North.](../assets/images/cards/hc-flow-ward-links-dark.svg#only-dark)

A reference is only a string naming another record. Following it by hand means searching the Bundle for the record with that name, and the same link can arrive as `Location/n1`, as a full URL, or as a `urn:uuid:` (as in this example's Medplum upload).

Using [`resolve_reference()`](../reference/utilities/fhir_helpers.md#resolve_reference) we can follow a link in any of these forms, so each hop is one line, and site B's extra bay needs no extra code, because the workflow follows links until it reaches an area named in the config:

```python
from healthchain.fhir import resolve_reference

score = data.observations.entry[0].resource
stay = resolve_reference(data.encounters, score.encounter)
bed = resolve_reference(data.locations, stay.location[0].location)
area = resolve_reference(data.locations, bed.partOf)

area_name = config.areas[area.identifier[0].value].name
print(score.valueInteger, bed.name, "->", area_name)
```

```text
7 North bed 1 -> North
```

Site B, mapped through its own config, gives exactly the same summary as site A, and the cookbook tests check this for every definition.

### Step 4: Compute the measures

Now that the validated records are handed over in research terms, the measures can be defined in plain Python in `ward_definitions.py`. Each measure rests on a definition the research team has chosen:

- **Window:** 12 hours (the length of the shift for the ward/ICU nurses).
- **Admissions, option A (still present, default):** entries to the area in the window, among people still there.
- **Admissions, option B (all arrivals):** every entry to the area in the window, including people who have since left.
- **High patient acuity:** a NEWS2 score of 7 or more.
- **Freshness:** scores older than 12 hours count as unknown.

The thresholds are constants at the top of the file:

```python
ACUITY_HIGH = 7            # NEWS2 of 7 or more is high
ACUITY_MAX_AGE_HOURS = 12  # older scores count as unknown
WINDOW_HOURS = 12          # admissions window: one shift, both ends included
```

The cookbook's `summarise` function (in `ward_monitoring.py`) runs these definitions over the mapped records from Step 3 and returns one row per area, as in the [Quick Start table](#quick-start). Under the current definitions, North has two high-acuity patients (beds 1 and 3, with scores of 7 and 9) and one with unknown acuity (bed 4, no recent score).

### Step 5: Serve the summary

A dashboard inside a hospital needs more than an HTTP route. The service must restrict who can call it, log every request, and accept browser calls only from the dashboard's origin.

[`HealthChainAPI`](../reference/gateway/api.md) is a FastAPI app with these built in. `create_app` defines the route as it would in FastAPI, and each request reruns the workflow on current data:

```python
def create_app(site="a", admissions="still-present", window_hours=WINDOW_HOURS,
               source="files", as_of=None) -> HealthChainAPI:
    app = HealthChainAPI(title="Ward summary")

    @app.get("/ward-summary")
    def ward_summary(
        site: Literal["a", "b"] = site,
        admissions: Literal[tuple(ADMISSION_DEFINITIONS)] = admissions,
        window_hours: int = Query(default=window_hours, gt=0),
        as_of: str | None = as_of,
    ) -> dict:
        return run(site, admissions, window_hours, source, as_of)

    return app
```

The controls are switched on by a [`healthchain.yaml`](../reference/config.md) file in the directory the app runs from:

```yaml
security:
  auth: api-key # key read from HEALTHCHAIN_API_KEY
  allowed_origins:
    - "https://dashboard.example.org" # the dashboard's address (CORS)
compliance:
  audit_log: ./logs/audit.jsonl # one JSON line per request
```

See [**Configuration Reference**](../reference/config.md) and [**Security**](../security.md) for more information on TLS and other options.

---

## Use a Live FHIR Source

The measures must be recomputed from current data as the ward changes. Switching from saved files to a live source usually means rewriting the data access: authentication, search queries, and parsing whatever the server returns.

[`FHIRGateway`](../reference/gateway/fhir_gateway.md) handles that part. A source is registered once with its credentials and returns the same validated, typed Bundles, so the mappings, definitions and endpoint stay as they are. The `search_params` field in each site's config tells the gateway which records belong where.

```python
from healthchain.gateway import FHIRGateway
from healthchain.gateway.clients import FHIRAuthConfig
from cookbook.ward_monitoring import from_gateway

gateway = FHIRGateway()
gateway.add_source(
    "medplum", FHIRAuthConfig.from_env("MEDPLUM").to_connection_string()
)
live_data = from_gateway(gateway, "medplum", config)
```

!!! note "Observations from HL7 v2"

    This example assumes every record arrives as FHIR, for simplicity. In practice, bedside observations such as vital signs are often sent as [HL7 v2 messages](https://hl7.org/fhir/comparison-v2.html) rather than FHIR Observations. Converting them fits HealthChain's [interoperability engine](../reference/interop/interop.md), which turns other formats into FHIR through pluggable parsers and templates.

??? tip "Set up a Medplum sandbox to run this"

    Follow the [Medplum sandbox setup](setup_fhir_sandboxes.md#medplum) to configure `MEDPLUM_*` in `.env`, using a demo project that can read, create and delete Encounters, Locations and Observations. Then upload site A's records from the repository root with [`healthchain seed medplum`](../cli.md#healthchain-seed-medplum):

    ```bash
    healthchain seed medplum cookbook/data/ward_monitoring/site_a/medplum_upload.json
    ```

    To serve the live data, run
    ```bash
    python cookbook/ward_monitoring.py --source medplum --as-of 2026-10-23T12:00:00Z
    ```

    The [fixture notes](https://github.com/healthchainai/HealthChain/tree/main/cookbook/data/ward_monitoring/README.md#live-comparison-and-cleanup) include a full output comparison and cleanup instructions.

Every check is now a fresh query to the server, describing the ward as it is at that moment. The synthetic events are dated 23 October 2026, so four checks through that morning, with `as_of` set to each check's time, show North changing through the shift:

| Time  | Occupied beds | Admissions | High acuity | What happened in North                                                                                              |
| ----- | ------------- | ---------- | ----------- | ------------------------------------------------------------------------------------------------------------------- |
| 00:00 | 3             | 3          | 2           | Three patients, all arrived in the last 12 hours                                                                    |
| 04:00 | 5             | 4          | 4           | Two more arrive; one has no recorded arrival time, so isn't counted as an admission                                 |
| 08:00 | 4             | 2          | 2           | One moves to a general hospital ward, one moves to South, one arrives; an earlier arrival is now outside the window |
| 12:00 | 4             | 2          | 2           | No movement                                                                                                         |

Definitions change too. They live in `ward_definitions.py`, and the ones this example expects to revise are also request parameters, so a new version can be tried on the same live data without digging through the code. This example has two:

- **`window_hours`:** how far back counts as recent. The default of 12 hours matches one ICU shift. If the ICU moved to 8-hour shifts, the team would want admissions counted per shift.
- **`admissions`:** which patients count as admissions. Option A, the default, counts only patients still in the area. Option B counts everyone who arrived in the window, which may be more realistic because every admission creates work, even when the patient doesn't stay long.

The query, validation and site mappings stay fixed, so any difference comes from the definition alone. At 12:00, the 8-hour window drops the patient who arrived at exactly 00:00, and option B adds the patient who was in North from 01:00 to 05:00:

| Definition                         | Parameter                 | North admissions |
| ---------------------------------- | ------------------------- | ---------------- |
| Current (12-hour window, option A) | defaults                  | 2                |
| 8-hour shift                       | `window_hours=8`          | 1                |
| Option B, all arrivals             | `admissions=all-arrivals` | 3                |

The NEWS2 cutoff of 7 would be a natural third parameter, since new evidence could move it.

---

## What You've Built

Ward strain measures are usually built on a research database or a one-off extract, so they can't follow the ward as it changes, move to another hospital, or keep up with revised definitions. This example runs one on live FHIR data instead. HealthChain holds the boundary on both sides: records come in through `FHIRGateway` and validation, and results go out through `HealthChainAPI`. The research team owns only what sits between them, a site config for each hospital and `ward_definitions.py`, and each need is met without changing the boundary:

| Research need                                 | What changed                                          | Research code changed? | HealthChain's part                                                                                        |
| --------------------------------------------- | ----------------------------------------------------- | ---------------------- | --------------------------------------------------------------------------------------------------------- |
| Timely, repeated assessment                   | Reference time (`as_of`); saved files → live FHIR API | No                     | `FHIRGateway` queries current data, validated on every pull; `HealthChainAPI` recomputes on every request |
| Variables recorded differently across systems | Site A → site B config                                | No                     | Validation surfaces each site's non-standard data; `resolve_reference` joins stays, beds and scores       |
| Definitions that change                       | `window_hours` and `admissions` parameters            | No                     | Query, validation and mappings stay fixed, so old and new results compare on the same records             |

## References

- Gabler, N. B. _et al._ (2013) "Mortality among patients admitted to strained intensive care units", _American Journal of Respiratory and Critical Care Medicine_, 188(7), pp. 800–806. [doi:10.1164/rccm.201304-0622OC](https://doi.org/10.1164/rccm.201304-0622OC)
- Kohn, R. _et al._ (2018) "Ward Capacity Strain: A Novel Predictor of 30-Day Hospital Readmissions", _Journal of General Internal Medicine_, 33(11), pp. 1851–1853. [doi:10.1007/s11606-018-4564-x](https://doi.org/10.1007/s11606-018-4564-x)
- Page, B. _et al._ (2024) "Health services under pressure: a scoping review and development of a taxonomy of adaptive strategies", _BMJ Quality and Safety_, 33(11), pp. 738–747. [doi:10.1136/bmjqs-2023-016686](https://doi.org/10.1136/bmjqs-2023-016686)
- Royal College of Physicians (2017) _National Early Warning Score (NEWS) 2: Standardising the assessment of acute-illness severity in the NHS_. Updated report of a working party. [rcp.ac.uk](https://www.rcp.ac.uk/resources/national-early-warning-score-news-2/)
