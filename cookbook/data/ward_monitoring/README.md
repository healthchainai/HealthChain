# Synthetic ward-monitoring fixtures

All names, identifiers, times and scores are invented. Patients appear only as
synthetic identifiers on `Encounter.subject`; there are no Patient resources.
Resources are FHIR R4B.

The data was pulled at **23 October 2026, 12:00 UTC** (each Bundle's
`timestamp`), the default reference time. Closed location periods give the
history before it, so earlier reference times work; open-ended stays rely on
their status at 12:00, so later ones are refused.

## Files

| File | What it is |
| --- | --- |
| `site_*/locations.json`, `encounters.json`, `observations.json` | The site's export, as collection Bundles |
| `site_*/config.json` | The site's mappings: FHIR query, area identifiers and capacities, acuity code, status fixes |
| `site_*/medplum_upload.json` | The same resources as one transaction Bundle for `healthchain seed medplum`: `urn:uuid` links, a per-site tag, conditional creates, status fixes applied |
| `expected_*.json` | Expected summaries, one per definition (see below) |

## Sites

`site_a/` and `site_b/` hold the same census in two local styles, so the same
definitions must give identical results.

| | Site A | Site B |
| --- | --- | --- |
| Area identifiers | `W7-N`, `W7-S`, `W7-E` | `WEST-NORTH`, `WEST-SOUTH`, `WEST-SURGE` |
| Hierarchy (`physicalType`) | ward → area → bed | ward → area → bay (room) → bed |
| Acuity code | `https://example.org/site-a/observation#ACU` | `https://example.org/site-b/flowsheet#DEPENDENCY` |
| Location status | standard | `recent` uses non-standard `current`; mapped to `active` in `config.json` |

## Scenarios

Default definitions: 12-hour window (00:00–12:00, both ends included); high
acuity is the latest NEWS2 score of 7 or more within the 12 hours before the
reference time.

| Encounter | Stay | Scores | Option A (still present) | Option B (all arrivals) | Acuity |
| --- | --- | --- | --- | --- | --- |
| recent | North bed 1 from 08:00 | 7 at 10:00 | Occupied; admission | Admission | High |
| same-area-move | North bed 5 from 16:00 the day before, bed 2 from 09:00 | 8 at 22:00 the day before (too old); 6 at 11:00 | Occupied; not an admission (entered the day before) | Not an admission | Not high (high at cutoff 5) |
| boundary | North bed 3 from exactly 00:00 | 9 at 01:00 | Occupied; admission | Admission | High |
| missing-time | North bed 4, no location period | none | Occupied; unknown entry time | Not counted | Unknown |
| cross-area-move | North bed 1 20:00–07:00, then South bed 1 from 07:00 | 7 at 23:00 the day before (too old) | South occupied; South admission | South admission only | Unknown |
| older-south | South bed 2 from 04:00 | 2 at 09:00; 8 at 12:30 (after the reference time) | Occupied; admission | Admission | Not high |
| left-early | North bed 2 01:00–05:00, finished | 8 at 02:00 | Not occupied | North admission | Ignored (not present) |
| overflow | Escalation bed from 10:00 | 10 at 10:30 | Occupied; admission | Admission | High |
| not-yet-arrived | Starts 13:00, after the reference time | — | Excluded | Excluded | — |
| outside-ward | Outpatient chair outside the configured areas | — | Excluded | Excluded | — |

## Expected outputs

Written by hand from the table above before the script was run. Both sites
must match every file. Each file records its definition in `window_hours`,
`admissions_definition` and `acuity_high`.

| File | Definition | North admissions | North high acuity | What changes |
| --- | --- | --- | --- | --- |
| `expected_still_present.json` | defaults | 2 | 2 | — |
| `expected_window_8h.json` | `window_hours=8` | 1 | 2 | boundary's 00:00 arrival falls outside 04:00–12:00; older-south's 04:00 arrival is on the boundary and still counts |
| `expected_acuity_5.json` | `acuity_high=5` | 2 | 3 | same-area-move's 6 counts |
| `expected_all_arrivals.json` | `admissions=all-arrivals` | 3 | 2 | left-early counts |

Every other value is the same in all four: North 4/5 occupied, 1 unknown entry
time, 1 acuity unknown; South 2/3 occupied, 2 admissions, 0 high, 1 unknown;
Escalation 1/1 occupied, 1 admission, 1 high.

### Earlier reference times

North with the default definitions:

| Time | Occupied | Admissions | High acuity | Why it changes |
| --- | --- | --- | --- | --- |
| 00:00 | 3 | 3 | 2 | same-area-move (bed 5), boundary (arrives 00:00), cross-area-move (bed 1); boundary has no score yet |
| 04:00 | 5 | 4 | 4 | missing-time (from 03:00, unknown entry) and left-early (01:00–05:00) arrive |
| 08:00 | 4 | 2 | 2 | left-early gone; cross-area-move left for South at 07:00; recent arrives at 08:00; same-area-move's entry is now outside the window |
| 12:00 | 4 | 2 | 2 | as `expected_still_present.json` |

South: cross-area-move is high acuity at 08:00 (score 7 at 23:00 the day
before, within 12 hours) and acuity unknown at 12:00 (too old).

## Checking the results

From the repository root, with HealthChain installed in the active environment:

```bash
python -m pip install pytest
python -m pytest tests/cookbook/test_ward_monitoring.py -q
```

The expected result at this revision is **15 passed**. The tests compare both
sites with all four expected outputs, check North at the earlier reference
times, show that site B fails validation without its status mapping, and check
the gateway path and the HTTP endpoint. The gateway test uses an in-memory
stub; for a hosted server, see the
[live comparison](#live-comparison-and-cleanup).

For a versioned reproduction, check out the release tag or commit being
evaluated, install it with `python -m pip install .`, and use the documentation
and fixtures from the same revision. Record the commands, results and any local
edits alongside:

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
recorded status. A site's query must include the history the chosen measure
needs: the all-arrivals rule, for example, needs stays that have already ended.

## Live comparison and cleanup

Follow the cookbook's [live-source step](../../../docs/cookbook/ward_monitoring.md#use-a-live-fhir-source)
to configure Medplum and seed site A. The seed command reports `Uploaded (no
Patient resources found)`, because the fixtures contain no Patient resources.
Conditional creates skip records that already exist but don't update them, so
remove the old demo records before uploading a changed fixture set.

Compare the live output with the offline expected output (`--acuity-high 5`
compares with `expected_acuity_5.json`, and so on):

```bash
python cookbook/ward_monitoring.py --json --source medplum --as-of 2026-10-23T12:00:00Z
```

The explicit reference time evaluates the same synthetic events as the offline
run; without it, admissions and score freshness are judged at the current time.
`from_gateway` searches each resource type by the site tag, validates every
resource and refuses results with a next page. The three searches are separate
requests, not an atomic snapshot. Server-assigned IDs differ from the saved
files; areas are matched by `Location.identifier`.

To remove the demo records, list the tagged site A records from the repository
root and check the targets:

```python
from healthchain.fhir.r4b import Bundle
from healthchain.gateway import FHIRGateway
from healthchain.gateway.clients import FHIRAuthConfig
from cookbook.ward_monitoring import DATA_DIR, from_gateway, load_config

gateway = FHIRGateway()
gateway.add_source("medplum", FHIRAuthConfig.from_env("MEDPLUM").to_connection_string())
config = load_config(DATA_DIR / "site_a")

demo = from_gateway(gateway, "medplum", config)
targets = [
    f"{entry.resource.__resource_type__}/{entry.resource.id}"
    for bundle in (demo.observations, demo.encounters, demo.locations)
    for entry in bundle.entry or []
]
print("\n".join(targets))
```

Then, in the same session, delete them from the configured Medplum project and
check that none remain in search results (server history keeps them):

```python
if targets:
    deletion = Bundle(
        type="transaction",
        entry=[{"request": {"method": "DELETE", "url": url}} for url in targets],
    )
    gateway.transaction(deletion, source="medplum")

remaining = from_gateway(gateway, "medplum", config)
assert not any(b.entry for b in (remaining.encounters, remaining.locations, remaining.observations))
```

Seeding again recreates the example.
