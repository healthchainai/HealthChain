# Terminology

Terminology lookup for HealthChain.

A small seam for mapping free text to codings: the `TerminologyLookup` protocol, the `Coding` model, and `LocalCodeLookup` — an in-process implementation over a demo catalog (RxNorm/LOINC/ICD-10-CM) for offline demos and tests. Real terminology services implement the same protocol.

## `Coding`

Bases: `BaseModel`

A terminology coding: code, display, and the system it belongs to.

Version-agnostic and JSON-serializable via `model_dump()` so it can be returned directly from agent tools.

## `LocalCodeLookup`

Terminology lookup over an in-memory catalog.

Implements the `TerminologyLookup` protocol. Matching: every word of the query must appear (case-insensitive substring) in some word of the display name, so brand names, ingredients, and strengths all narrow the match. Results are ranked shortest-display-first — the tightest match for the query comes first.

| PARAMETER | DESCRIPTION                                                                                                                                                                                         |
| --------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `catalog` | Codings to search over instead of the bundled demo catalog. Accepts Coding instances or dicts with code/display/system keys **TYPE:** `Optional[Iterable[Union[Coding, dict]]]` **DEFAULT:** `None` |

Example

> > > lookup = LocalCodeLookup() lookup.search("metoprolol 25")[0].code '866427' lookup.search("hypertension", system=ICD10CM)[0].code 'I10' site_lookup = LocalCodeLookup(catalog=my_formulary) all_codings = list(lookup) # or lookup.entries()

### `entries()`

Return every coding in the catalog.

A local catalog (e.g. a site formulary) is data an application may legitimately want to walk — to build a mention lexicon, render a picker, or export — not just probe via `search`. Enumeration is a capability of *local* lookups, not part of the `TerminologyLookup` protocol: a remote terminology service generally cannot list itself.

| RETURNS        | DESCRIPTION                                         |
| -------------- | --------------------------------------------------- |
| `List[Coding]` | A new list of all catalog codings, in catalog order |

### `search(text, system=None)`

Search the catalog for codings matching free text.

| PARAMETER | DESCRIPTION                                                                            |
| --------- | -------------------------------------------------------------------------------------- |
| `text`    | Free-text query (e.g. "metoprolol 25", "type 2 diabetes") **TYPE:** `str`              |
| `system`  | Restrict results to this code system URI **TYPE:** `Optional[str]` **DEFAULT:** `None` |

| RETURNS        | DESCRIPTION                                                |
| -------------- | ---------------------------------------------------------- |
| `List[Coding]` | Ranked list of candidate codings (shortest display first); |
| `List[Coding]` | empty if nothing matches                                   |

## `TerminologyLookup`

Bases: `Protocol`

Protocol for terminology lookup implementations.

Implementations search a code system (or all systems they know) for codings matching a free-text query and return ranked candidates — never a guess. Agents should use a returned code, not invent one.

### `search(text, system=None)`

Search for codings matching free text.

| PARAMETER | DESCRIPTION                                                                            |
| --------- | -------------------------------------------------------------------------------------- |
| `text`    | Free-text query (e.g. a medication or condition name) **TYPE:** `str`                  |
| `system`  | Restrict results to this code system URI **TYPE:** `Optional[str]` **DEFAULT:** `None` |

| RETURNS        | DESCRIPTION                                                |
| -------------- | ---------------------------------------------------------- |
| `List[Coding]` | Ranked list of candidate codings; empty if nothing matches |

## `base`

Terminology lookup protocol and coding model.

Defines the seam between HealthChain and terminology services: anything with a `search(text, system) -> list[Coding]` method is a terminology lookup. `LocalCodeLookup` is the shipped in-process implementation; real terminology services (a FHIR `$lookup` endpoint, a hosted MCP server) plug in behind the same signature.

### `Coding`

Bases: `BaseModel`

A terminology coding: code, display, and the system it belongs to.

Version-agnostic and JSON-serializable via `model_dump()` so it can be returned directly from agent tools.

### `TerminologyLookup`

Bases: `Protocol`

Protocol for terminology lookup implementations.

Implementations search a code system (or all systems they know) for codings matching a free-text query and return ranked candidates — never a guess. Agents should use a returned code, not invent one.

#### `search(text, system=None)`

Search for codings matching free text.

| PARAMETER | DESCRIPTION                                                                            |
| --------- | -------------------------------------------------------------------------------------- |
| `text`    | Free-text query (e.g. a medication or condition name) **TYPE:** `str`                  |
| `system`  | Restrict results to this code system URI **TYPE:** `Optional[str]` **DEFAULT:** `None` |

| RETURNS        | DESCRIPTION                                                |
| -------------- | ---------------------------------------------------------- |
| `List[Coding]` | Ranked list of candidate codings; empty if nothing matches |

## `local`

In-process terminology lookup backed by a small demo catalog.

The bundled catalog covers common medications (RxNorm), lab and vital-sign observations (LOINC), and conditions (ICD-10-CM) — license-free systems only, deliberately no SNOMED CT. It exists so demos, tests, and generated projects work offline with zero setup; it is NOT a terminology service and covers only a few dozen concepts. For real coverage, put a proper terminology service behind the same `TerminologyLookup` protocol.

### `LocalCodeLookup`

Terminology lookup over an in-memory catalog.

Implements the `TerminologyLookup` protocol. Matching: every word of the query must appear (case-insensitive substring) in some word of the display name, so brand names, ingredients, and strengths all narrow the match. Results are ranked shortest-display-first — the tightest match for the query comes first.

| PARAMETER | DESCRIPTION                                                                                                                                                                                         |
| --------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `catalog` | Codings to search over instead of the bundled demo catalog. Accepts Coding instances or dicts with code/display/system keys **TYPE:** `Optional[Iterable[Union[Coding, dict]]]` **DEFAULT:** `None` |

Example

> > > lookup = LocalCodeLookup() lookup.search("metoprolol 25")[0].code '866427' lookup.search("hypertension", system=ICD10CM)[0].code 'I10' site_lookup = LocalCodeLookup(catalog=my_formulary) all_codings = list(lookup) # or lookup.entries()

#### `entries()`

Return every coding in the catalog.

A local catalog (e.g. a site formulary) is data an application may legitimately want to walk — to build a mention lexicon, render a picker, or export — not just probe via `search`. Enumeration is a capability of *local* lookups, not part of the `TerminologyLookup` protocol: a remote terminology service generally cannot list itself.

| RETURNS        | DESCRIPTION                                         |
| -------------- | --------------------------------------------------- |
| `List[Coding]` | A new list of all catalog codings, in catalog order |

#### `search(text, system=None)`

Search the catalog for codings matching free text.

| PARAMETER | DESCRIPTION                                                                            |
| --------- | -------------------------------------------------------------------------------------- |
| `text`    | Free-text query (e.g. "metoprolol 25", "type 2 diabetes") **TYPE:** `str`              |
| `system`  | Restrict results to this code system URI **TYPE:** `Optional[str]` **DEFAULT:** `None` |

| RETURNS        | DESCRIPTION                                                |
| -------------- | ---------------------------------------------------------- |
| `List[Coding]` | Ranked list of candidate codings (shortest display first); |
| `List[Coding]` | empty if nothing matches                                   |
