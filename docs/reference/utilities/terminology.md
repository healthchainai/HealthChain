# Terminology

Free text is where clinical data starts — "aspirin", "type 2 diabetes", "blood pressure" — but FHIR resources need codings. `healthchain.terminology` is the seam for mapping text to codes: a small protocol any terminology service can implement, and an in-process lookup that works offline with zero setup.

!!! warning "The demo catalog is not a terminology service"
    `LocalCodeLookup`'s bundled catalog covers a few dozen common concepts so demos, tests, and generated projects run without network access or licenses. For real coverage, put a proper terminology service behind the same `TerminologyLookup` protocol.

## Quick Start

```python
from healthchain.terminology import LocalCodeLookup

lookup = LocalCodeLookup()

# Every query word must match — strengths and brands narrow results
results = lookup.search("metoprolol 25")
print(results[0].code, results[0].display)
# 866427 24 HR metoprolol succinate 25 MG Extended Release Oral Tablet

# Restrict to one code system
from healthchain.terminology import ICD10CM
condition = lookup.search("hypertension", system=ICD10CM)[0]
print(condition.code)  # I10
```

Results are `Coding` models (`code` / `display` / `system`), ranked tightest-match-first, and serialize with `model_dump()` — so a lookup can be returned directly from an agent tool. The point of handing a model a lookup tool is that it uses a **returned code instead of inventing one**.

## The catalog

The bundled demo catalog ships license-free code systems only:

| System | Constant | Contents |
|--------|----------|----------|
| RxNorm | `RXNORM` | Common medications with strengths |
| LOINC | `LOINC` | Common labs and vital signs |
| ICD-10-CM | `ICD10CM` | Common conditions |

(No SNOMED CT — its license doesn't permit redistribution in an open-source package.)

Replace it with your own formulary or code list:

```python
from healthchain.terminology import Coding, LocalCodeLookup, RXNORM

site_lookup = LocalCodeLookup(catalog=[
    Coding(code="197361", display="amLODIPine 5 MG Oral Tablet", system=RXNORM),
    {"code": "314076", "display": "lisinopril 10 MG Oral Tablet", "system": RXNORM},
])
```

A local catalog is data your application may want to walk, not just probe — to build a mention lexicon for an extractor, render a picker, or export. `LocalCodeLookup` is iterable and exposes the full catalog via `entries()`:

```python
lexicon = {coding.display.lower() for coding in site_lookup}
all_codings = site_lookup.entries()
len(site_lookup)  # catalog size
```

(Enumeration is a capability of *local* lookups, not part of the `TerminologyLookup` protocol — a remote terminology service generally can't list itself.)

## The protocol

Anything with a `search(text, system) -> list[Coding]` method is a `TerminologyLookup` — the protocol is [runtime-checkable](https://docs.python.org/3/library/typing.html#typing.runtime_checkable), and structural, so implementations don't need to inherit anything:

```python
from healthchain.terminology import Coding, TerminologyLookup

class MyTerminologyService:
    """e.g. backed by a FHIR $lookup endpoint or a hosted MCP server."""

    def search(self, text: str, system: str | None = None) -> list[Coding]:
        ...

assert isinstance(MyTerminologyService(), TerminologyLookup)
```

Write code against the protocol, and swap `LocalCodeLookup` for a real service when you deploy.

## Putting it together

Look up a code, build the resource, validate it — the write loop an agent (or you) runs:

```python
from healthchain.fhir import create_medication_statement, validate_resource
from healthchain.terminology import LocalCodeLookup, RXNORM

lookup = LocalCodeLookup()

coding = lookup.search("acetaminophen 325", system=RXNORM)[0]
medication = create_medication_statement(
    subject="Patient/123",
    status="active",
    code=coding.code,
    display=coding.display,
    system=coding.system,
)
report = validate_resource(medication)
assert report.valid
```
