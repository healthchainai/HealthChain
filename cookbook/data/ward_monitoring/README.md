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

From the repository root, with HealthChain and pytest installed:

```bash
python -m pytest tests/cookbook/test_ward_monitoring.py -q
```

The expected result at this revision is **15 passed**. The gateway test uses an
in-memory stub; for a hosted server, see the
[live comparison](#live-comparison).

For a versioned reproduction, check out the release tag being evaluated,
install it with `python -m pip install .`, and record `git rev-parse HEAD`,
`python --version` and `python -m pip freeze` with the results.

## Scope of the checks

Matching these outputs shows reuse across the supplied variations, not clinical
validity or compatibility with every hospital; the
[validation reference](../../../docs/reference/utilities/fhir_helpers.md#validation-loading)
says what resource validation covers. History can't be rebuilt from records
that weren't supplied, so a site's query must include what the chosen measure
needs: all arrivals, for example, needs stays that have ended.

## Live comparison

Follow the cookbook's [live-source step](../../../docs/cookbook/ward_monitoring.md#use-a-live-fhir-source)
to configure Medplum and seed site A. The seed command reports `Uploaded (no
Patient resources found)`, because the fixtures contain no Patient resources.

Compare the live output with the offline expected output (`--acuity-high 5`
compares with `expected_acuity_5.json`, and so on):

```bash
python cookbook/ward_monitoring.py --json --source medplum --as-of 2026-10-23T12:00:00Z
```

Without `--as-of`, admissions and score freshness are judged at the current
time.
