import json

from healthchain.terminology import (
    ICD10CM,
    LOINC,
    RXNORM,
    Coding,
    LocalCodeLookup,
    TerminologyLookup,
)


def test_search_by_name():
    """A single-word query matches displays containing it."""
    lookup = LocalCodeLookup()

    results = lookup.search("lisinopril")

    assert len(results) == 1
    assert results[0].code == "314076"
    assert results[0].system == RXNORM


def test_search_multi_token_narrows():
    """Every query token must match, so strengths narrow brand/ingredient hits."""
    lookup = LocalCodeLookup()

    all_metoprolol = lookup.search("metoprolol")
    assert len(all_metoprolol) == 2

    narrowed = lookup.search("metoprolol 25")
    assert [coding.code for coding in narrowed] == ["866427"]


def test_search_case_insensitive():
    """Matching ignores case in both query and display."""
    lookup = LocalCodeLookup()

    assert lookup.search("AMLODIPINE") == lookup.search("amlodipine")
    assert len(lookup.search("Hypertension")) == 1


def test_search_system_filter():
    """The system argument restricts results to one code system."""
    lookup = LocalCodeLookup()

    assert lookup.search("hemoglobin", system=LOINC) != []
    assert lookup.search("hemoglobin", system=RXNORM) == []
    assert lookup.search("hypertension", system=ICD10CM)[0].code == "I10"


def test_search_ranked_shortest_display_first():
    """Results are ranked with the tightest (shortest) display first."""
    lookup = LocalCodeLookup()

    results = lookup.search("acetaminophen")

    assert len(results) == 2
    displays = [coding.display for coding in results]
    assert displays == sorted(displays, key=len)


def test_search_no_match_returns_empty():
    """Unmatched or empty queries return an empty list, never raise."""
    lookup = LocalCodeLookup()

    assert lookup.search("warfarin") == []
    assert lookup.search("") == []
    assert lookup.search("   ") == []


def test_custom_catalog():
    """A site-specific catalog replaces the demo catalog entirely."""
    lookup = LocalCodeLookup(
        catalog=[
            Coding(code="123", display="Testdrug 10 MG Tablet", system=RXNORM),
            {"code": "456", "display": "Other Testdrug", "system": RXNORM},
        ]
    )

    assert [coding.code for coding in lookup.search("testdrug")] == ["456", "123"]
    assert lookup.search("aspirin") == []


def test_entries_returns_whole_catalog():
    """entries() exposes the catalog publicly — e.g. to derive a mention lexicon."""
    lookup = LocalCodeLookup()

    entries = lookup.entries()

    assert len(entries) == len(lookup._catalog)
    assert all(isinstance(entry, Coding) for entry in entries)
    # A copy, not the internal list
    entries.clear()
    assert len(lookup.entries()) > 0


def test_lookup_is_iterable():
    """Iterating a lookup walks the catalog; len() reports its size."""
    catalog = [
        Coding(code="123", display="Testdrug 10 MG Tablet", system=RXNORM),
        Coding(code="456", display="Other Testdrug", system=RXNORM),
    ]
    lookup = LocalCodeLookup(catalog=catalog)

    assert len(lookup) == 2
    assert [coding.code for coding in lookup] == ["123", "456"]


def test_local_lookup_satisfies_protocol():
    """LocalCodeLookup structurally implements TerminologyLookup."""
    assert isinstance(LocalCodeLookup(), TerminologyLookup)


def test_demo_catalog_has_no_snomed():
    """The bundled catalog ships license-free systems only."""
    lookup = LocalCodeLookup()

    systems = {coding.system for coding in lookup._catalog}

    assert systems == {RXNORM, LOINC, ICD10CM}
    assert not any("snomed" in system for system in systems)


def test_coding_serializes_to_json():
    """Codings are JSON-serializable for agent tool output."""
    coding = LocalCodeLookup().search("aspirin")[0]

    dumped = json.loads(coding.model_dump_json())

    assert dumped == {
        "code": "243670",
        "display": "aspirin 81 MG Oral Tablet",
        "system": RXNORM,
    }
