"""In-process terminology lookup backed by a small demo catalog.

The bundled catalog covers common medications (RxNorm), lab and vital-sign
observations (LOINC), and conditions (ICD-10-CM) — license-free systems only,
deliberately no SNOMED CT. It exists so demos, tests, and generated projects
work offline with zero setup; it is NOT a terminology service and covers only
a few dozen concepts. For real coverage, put a proper terminology service
behind the same ``TerminologyLookup`` protocol.
"""

from typing import Iterable, Iterator, List, Optional, Union

from healthchain.terminology.base import Coding

RXNORM = "http://www.nlm.nih.gov/research/umls/rxnorm"
LOINC = "http://loinc.org"
ICD10CM = "http://hl7.org/fhir/sid/icd-10-cm"

_DEMO_CATALOG: List[Coding] = [
    # Medications (RxNorm)
    Coding(code="243670", display="aspirin 81 MG Oral Tablet", system=RXNORM),
    Coding(
        code="209387",
        display="Acetaminophen 325 MG Oral Tablet [Tylenol]",
        system=RXNORM,
    ),
    Coding(
        code="313820", display="Acetaminophen 160 MG Chewable Tablet", system=RXNORM
    ),
    Coding(
        code="866427",
        display="24 HR metoprolol succinate 25 MG Extended Release Oral Tablet",
        system=RXNORM,
    ),
    Coding(
        code="866412",
        display="24 HR metoprolol succinate 100 MG Extended Release Oral Tablet",
        system=RXNORM,
    ),
    Coding(code="308136", display="amLODIPine 2.5 MG Oral Tablet", system=RXNORM),
    Coding(code="197319", display="Allopurinol 100 MG Oral Tablet", system=RXNORM),
    Coding(code="308192", display="Amoxicillin 500 MG Oral Tablet", system=RXNORM),
    Coding(code="309362", display="Clopidogrel 75 MG Oral Tablet", system=RXNORM),
    Coding(code="310965", display="Ibuprofen 200 MG Oral Tablet", system=RXNORM),
    Coding(code="314076", display="lisinopril 10 MG Oral Tablet", system=RXNORM),
    Coding(
        code="860975",
        display="24 HR metFORMIN hydrochloride 500 MG Extended Release Oral Tablet",
        system=RXNORM,
    ),
    Coding(code="312961", display="simvastatin 20 MG Oral Tablet", system=RXNORM),
    # Conditions (ICD-10-CM)
    Coding(code="I10", display="Essential (primary) hypertension", system=ICD10CM),
    Coding(
        code="E11.9",
        display="Type 2 diabetes mellitus without complications",
        system=ICD10CM,
    ),
    Coding(code="J45.909", display="Unspecified asthma, uncomplicated", system=ICD10CM),
    Coding(
        code="J44.9",
        display="Chronic obstructive pulmonary disease, unspecified",
        system=ICD10CM,
    ),
    Coding(code="I50.9", display="Heart failure, unspecified", system=ICD10CM),
    Coding(code="D64.9", display="Anemia, unspecified", system=ICD10CM),
    # Observations (LOINC)
    Coding(code="8302-2", display="Body height", system=LOINC),
    Coding(code="29463-7", display="Body weight", system=LOINC),
    Coding(
        code="85354-9",
        display="Blood pressure panel with all children optional",
        system=LOINC,
    ),
    Coding(
        code="4548-4",
        display="Hemoglobin A1c/Hemoglobin.total in Blood",
        system=LOINC,
    ),
    Coding(
        code="2093-3",
        display="Cholesterol [Mass/volume] in Serum or Plasma",
        system=LOINC,
    ),
    Coding(code="718-7", display="Hemoglobin [Mass/volume] in Blood", system=LOINC),
]


class LocalCodeLookup:
    """Terminology lookup over an in-memory catalog.

    Implements the ``TerminologyLookup`` protocol. Matching: every word of
    the query must appear (case-insensitive substring) in some word of the
    display name, so brand names, ingredients, and strengths all narrow the
    match. Results are ranked shortest-display-first — the tightest match
    for the query comes first.

    Args:
        catalog: Codings to search over instead of the bundled demo catalog.
            Accepts Coding instances or dicts with code/display/system keys

    Example:
        >>> lookup = LocalCodeLookup()
        >>> lookup.search("metoprolol 25")[0].code
        '866427'
        >>> lookup.search("hypertension", system=ICD10CM)[0].code
        'I10'
        >>> site_lookup = LocalCodeLookup(catalog=my_formulary)
        >>> all_codings = list(lookup)  # or lookup.entries()
    """

    def __init__(self, catalog: Optional[Iterable[Union[Coding, dict]]] = None) -> None:
        source = _DEMO_CATALOG if catalog is None else catalog
        self._catalog: List[Coding] = [
            entry if isinstance(entry, Coding) else Coding.model_validate(entry)
            for entry in source
        ]

    def entries(self) -> List[Coding]:
        """Return every coding in the catalog.

        A local catalog (e.g. a site formulary) is data an application may
        legitimately want to walk — to build a mention lexicon, render a
        picker, or export — not just probe via ``search``. Enumeration is a
        capability of *local* lookups, not part of the ``TerminologyLookup``
        protocol: a remote terminology service generally cannot list itself.

        Returns:
            A new list of all catalog codings, in catalog order
        """
        return list(self._catalog)

    def __iter__(self) -> Iterator[Coding]:
        return iter(self._catalog)

    def __len__(self) -> int:
        return len(self._catalog)

    def search(self, text: str, system: Optional[str] = None) -> List[Coding]:
        """Search the catalog for codings matching free text.

        Args:
            text: Free-text query (e.g. "metoprolol 25", "type 2 diabetes")
            system: Restrict results to this code system URI

        Returns:
            Ranked list of candidate codings (shortest display first);
            empty if nothing matches
        """
        tokens = text.lower().split()
        if not tokens:
            return []

        matches = [
            entry
            for entry in self._catalog
            if (system is None or entry.system == system)
            and all(
                any(token in word for word in entry.display.lower().split())
                for token in tokens
            )
        ]
        return sorted(matches, key=lambda entry: len(entry.display))
