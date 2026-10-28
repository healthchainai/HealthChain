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

High is 3 or more. Only the latest score within 12 hours before the reference
time is used.

| Encounter | Scores | Result |
| --- | --- | --- |
| recent | 3 at 10:00 | High |
| same-area-move | 4 at 22:00 the day before (too old); 2 at 11:00 | Not high |
| boundary | 4 at 01:00 | High |
| missing-time | none | Unknown |
| cross-area-move | 3 at 23:00 the day before (too old) | Unknown |
| older-south | 1 at 09:00; 4 at 12:30 (after the reference time) | Not high |
| left-early | 4 at 02:00 | Ignored (not present) |
| overflow | 4 at 10:30 | High |

## Earlier reference times

North over the morning (still-present admissions, 12-hour window):

| Time | Occupied | Admissions | High acuity | Why it changes |
| --- | --- | --- | --- | --- |
| 00:00 | 3 | 3 | 2 | same-area-move (bed 5), boundary (arrives 00:00), cross-area-move (bed 1); boundary has no score yet |
| 04:00 | 5 | 4 | 4 | missing-time (from 03:00, unknown entry) and left-early (01:00–05:00) arrive |
| 08:00 | 4 | 2 | 2 | left-early gone; cross-area-move left for South at 07:00; recent arrives at 08:00; same-area-move's entry is now outside the window |
| 12:00 | 4 | 2 | 2 | as the main expected output |

South: cross-area-move is high acuity at 08:00 (score 3 at 23:00 the day
before, within 12 hours) and acuity unknown at 12:00 (too old).

## Expected outputs

`expected_still_present.json` and `expected_all_arrivals.json` were written by
hand from the tables above before the script was run. Both sites must match
both files. North admissions are 2 under definition A and 3 under B. Other
values: North 4/5 occupied, 1 unknown entry time, 2 high acuity, 1 acuity
unknown; South 2/3 occupied, 2 admissions, 0 high, 1 unknown; Escalation 1/1
occupied, 1 admission, 1 high.

The fixtures were generated once by a script and then checked against these
tables. They are illustrative inputs, not clinical results.
