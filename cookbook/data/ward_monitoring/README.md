# Synthetic ward-monitoring fixtures

All names, identifiers, times and scores here are invented for the tutorial.
Patients appear only as synthetic identifiers on `Encounter.subject`; there are
no Patient resources or patient attributes. Resources are FHIR R4B.

The data was pulled at **23 October 2026, 12:00 UTC** (each Bundle's
`timestamp`). That is the default reference time. Closed location periods give
the history before it, so earlier reference times work; open-ended stays rely
on their status at 12:00, so later ones are refused.

## Files

Each site folder holds:

| File | What it is |
| --- | --- |
| `locations.json`, `encounters.json`, `observations.json` | The site's export, as collection Bundles |
| `config.json` | The site's mappings: FHIR query, area identifiers and capacities, acuity code, status fixes |
| `medplum_upload.json` | The same resources as one transaction Bundle for `healthchain seed medplum`: linked with `urn:uuid`, tagged per site, conditional creates (safe to rerun), status fixes applied |

## Sites

`site_a/` and `site_b/` describe the same census in two local styles, so the
same research definitions must give identical results.

| | Site A | Site B |
| --- | --- | --- |
| Area identifiers | `W7-N`, `W7-S`, `W7-E` | `WEST-NORTH`, `WEST-SOUTH`, `WEST-SURGE` |
| Hierarchy (`physicalType`) | ward → area → bed | ward → area → bay (room) → bed |
| Acuity code | `https://example.org/site-a/observation#ACU` | `https://example.org/site-b/flowsheet#DEPENDENCY` |
| Location status | standard | `recent` uses non-standard `current`; mapped to `active` in `config.json` |

## Encounter scenarios

Window: 12 hours, both ends included (00:00–12:00).

| Encounter | Scenario | Still present (A) | All arrivals (B) |
| --- | --- | --- | --- |
| recent | North bed 1 since 08:00 | Occupied; admission | Admission |
| same-area-move | North bed 5 from 16:00 the day before, bed 2 from 09:00 | Occupied; not an admission (area entry the day before) | Not an admission |
| boundary | North bed 3 since exactly 00:00 | Occupied; admission | Admission |
| missing-time | North bed 4, no location period | Occupied; unknown entry time | Not counted |
| cross-area-move | North bed 1 20:00–07:00, then South bed 1 from 07:00 | South occupied; South admission | South admission only |
| older-south | South bed 2 since 04:00 | Occupied; admission | Admission |
| left-early | North bed 2 01:00–05:00, finished | Not occupied | North admission |
| overflow | Escalation bed opened at 10:00 | Occupied; admission | Admission |
| not-yet-arrived | Starts 13:00, after the reference time | Excluded | Excluded |
| outside-ward | Outpatient chair outside the configured areas | Excluded | Excluded |

## Acuity observations

Scores are NEWS2 totals; high is 7 or more. Only the latest score within 12
hours before the reference time is used.

| Encounter | Scores | Result |
| --- | --- | --- |
| recent | 7 at 10:00 | High |
| same-area-move | 8 at 22:00 the day before (too old); 3 at 11:00 | Not high |
| boundary | 9 at 01:00 | High |
| missing-time | none | Unknown |
| cross-area-move | 7 at 23:00 the day before (too old) | Unknown |
| older-south | 2 at 09:00; 8 at 12:30 (after the reference time) | Not high |
| left-early | 8 at 02:00 | Ignored (not present) |
| overflow | 10 at 10:30 | High |

## Earlier reference times

North over the morning (still-present admissions, 12-hour window):

| Time | Occupied | Admissions | High acuity | Why it changes |
| --- | --- | --- | --- | --- |
| 00:00 | 3 | 3 | 2 | same-area-move (bed 5), boundary (arrives 00:00), cross-area-move (bed 1); boundary has no score yet |
| 04:00 | 5 | 4 | 4 | missing-time (from 03:00, unknown entry) and left-early (01:00–05:00) arrive |
| 08:00 | 4 | 2 | 2 | left-early gone; cross-area-move left for South at 07:00; recent arrives at 08:00; same-area-move's entry is now outside the window |
| 12:00 | 4 | 2 | 2 | as the main expected output |

South: cross-area-move is high acuity at 08:00 (score 7 at 23:00 the day
before, within 12 hours) and acuity unknown at 12:00 (too old).

## Revised window: 8 hours

With an 8-hour window (04:00–12:00, both ends included), boundary's 00:00
arrival falls outside it, so North admissions drop from 2 to 1 (still present).
older-south's 04:00 arrival is on the boundary and still counts. Nothing else
changes.

## Expected outputs

`expected_still_present.json`, `expected_all_arrivals.json` and
`expected_window_8h.json` were written by hand from the tables above before the
script was run. Both sites must match all three files. North admissions are 2
under definition A, 3 under B, and 1 under A with the 8-hour window. Other
values: North 4/5 occupied, 1 unknown entry time, 2 high acuity, 1 acuity
unknown; South 2/3 occupied, 2 admissions, 0 high, 1 unknown; Escalation 1/1
occupied, 1 admission, 1 high.

The fixtures were generated once by a script and then checked against these
tables. They are illustrative inputs, not clinical results.

## Checking the results

From the repository root, with HealthChain installed in the active environment:

```bash
python -m pip install pytest
python -m pytest tests/cookbook/test_ward_monitoring.py -q
```

The expected result at this revision is **32 passed**. The tests compare both
sites with all three expected-output files and check earlier reference times,
stale scores, invalid input, reference errors and duplicate occupied beds.
Keep the supplied definitions unchanged when checking these baseline results;
use explicit window and admission-rule arguments to compare alternatives.

The gateway test uses an in-memory stub. For a hosted-server comparison, follow
the [live comparison below](#live-comparison-and-cleanup).

For a versioned reproduction, check out the release tag or commit being
evaluated before installing HealthChain with `python -m pip install .`. Use
the documentation and fixtures from the same revision. Record the commands,
results and any local edits alongside:

```bash
git rev-parse HEAD
python --version
python -m pip freeze
```

## Scope of the checks

Matching these outputs demonstrates reuse across the supplied variations, not
clinical validity of a ward-strain model or compatibility with every hospital.
HealthChain's resource validation checks structure and required primitive-code
bindings; it does not cover profile conformance, FHIRPath constraints, clinical
correctness or all terminology bindings. The recipe checks some reference and
occupancy errors separately.

Historical calculations depend on the records supplied. Missing movements and
measurements cannot be reconstructed, and open-ended location periods rely on
recorded status. A site's query must include the history required by the chosen
measure: the all-arrivals rule, for example, needs stays that have already ended.

## Live comparison and cleanup

First follow the cookbook's [live-source step](../../../docs/cookbook/ward_monitoring.md#use-a-live-fhir-source)
to configure Medplum and seed site A. Run the following snippets in one Python
session from the repository root, with the same environment activated.

### Upload behaviour

The seed command reports `Uploaded (no Patient resources found)`: these fixtures
use synthetic identifiers on encounters and contain no Patient resources.
The transaction links resources and marks them with the tag
`https://example.org/healthchain-demo|ward-monitoring-site-a`. Conditional creates
avoid duplicating existing fixture records. They do not update those records
when fixture contents change; remove the old demo records before uploading a
changed fixture set.

### Compare the complete output

```python
import json
from healthchain.gateway import FHIRGateway
from healthchain.gateway.clients import FHIRAuthConfig
from cookbook.ward_monitoring import DATA_DIR, from_gateway, load_config, summarise

gateway = FHIRGateway()
gateway.add_source(
    "medplum", FHIRAuthConfig.from_env("MEDPLUM").to_connection_string()
)
config = load_config(DATA_DIR / "site_a")
live_data = from_gateway(gateway, "medplum", config)
expected = json.loads((DATA_DIR / "expected_still_present.json").read_text())
actual = summarise(live_data, config, as_of="2026-10-23T12:00:00Z")
assert actual == expected
print("Live summary matches the frozen offline output")
```

The command-line equivalent is:

```bash
python cookbook/ward_monitoring.py --json --source medplum --as-of 2026-10-23T12:00:00Z
```

The explicit reference time compares the same synthetic events as the offline
run. Omitting it evaluates records at the current time, so admissions and score
freshness can differ.

`from_gateway` searches for all three resource types using the configured tag,
validates each resource, and refuses results with a next page. The three searches
are separate requests, not an atomic snapshot of a changing server. Server-assigned
IDs can differ from the saved files; areas are mapped by `Location.identifier`,
and references within the upload transaction link the resulting records.

### Remove the demo records

Stop the HTTP app with **Ctrl+C** if it is running. In the Python session above,
retrieve the tagged site A records and inspect the deletion targets:

```python
from healthchain.fhir.r4b import Bundle

demo = from_gateway(gateway, "medplum", config)
targets = [
    f"{entry.resource.__resource_type__}/{entry.resource.id}"
    for bundle in (demo.observations, demo.encounters, demo.locations)
    for entry in bundle.entry or []
]
print("\n".join(targets))
```

The next snippet deletes those targets from the configured Medplum project.
Run it when you no longer need the seeded example:

```python
if targets:
    deletion = Bundle(
        type="transaction",
        entry=[{"request": {"method": "DELETE", "url": url}} for url in targets],
    )
    gateway.transaction(deletion, source="medplum")

remaining = from_gateway(gateway, "medplum", config)
assert all(not bundle.entry for bundle in (
    remaining.encounters, remaining.locations, remaining.observations
))
print("No site A demo records remain in search results")
```

This removes the records from ordinary searches, not from server history.
Seeding again recreates the example. Restore `source="files"` in the local app
before using the offline walkthrough again.
