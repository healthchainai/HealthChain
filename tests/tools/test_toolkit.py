import importlib.util
import json

import pytest

from healthchain.terminology import Coding, LocalCodeLookup
from healthchain.tools import FHIRToolkit, Tool

BUNDLE_PATH = "tests/data/test_reference_bundle.json"


class QueryOnlyLookup:
    """A TerminologyLookup without entries() — e.g. a remote service."""

    def search(self, text, system=None):
        return []


def test_get_tools_names_and_capability_gated_list_codes():
    """The default toolkit ships all tools; list_codes only with an enumerable lookup."""
    names = [t.name for t in FHIRToolkit().get_tools()]
    assert names == [
        "build_resource",
        "validate_resource",
        "load_bundle",
        "get_resources",
        "get_coded_entries",
        "resolve_reference",
        "lookup_code",
        "list_codes",
    ]

    remote = FHIRToolkit(lookup=QueryOnlyLookup())
    assert "list_codes" not in [t.name for t in remote.get_tools()]


def test_tool_specs_are_flat_and_json_safe():
    """Every spec is {name, description, input_schema} and JSON-serializable."""
    tools = FHIRToolkit().get_tools()

    dumped = json.loads(json.dumps([t.spec for t in tools]))

    for spec in dumped:
        assert spec["description"]
        assert spec["input_schema"]["type"] == "object"
    build = next(s for s in dumped if s["name"] == "build_resource")
    assert build["input_schema"]["required"] == ["resource_type"]
    assert "subject" in build["input_schema"]["properties"]


def test_build_resource_ok_and_json_dumpable():
    """A valid build returns ok + a JSON-mode resource dict."""
    kit = FHIRToolkit()

    result = kit.run_tool(
        "build_resource",
        {
            "resource_type": "MedicationStatement",
            "subject": "Patient/1",
            "code": "860975",
            "display": "metformin ER 500 MG",
            "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
            "dose_value": 500,
            "dose_unit": "mg",
            "frequency_per_day": 2,
        },
    )

    assert result["ok"] is True
    json.dumps(result)  # must cross a JSON boundary without error
    resource = result["resource"]
    assert resource["status"] == "unknown"
    assert resource["dosage"][0]["doseAndRate"][0]["doseQuantity"]["value"] == 500
    assert resource["dosage"][0]["timing"]["repeat"]["frequency"] == 2


def test_build_resource_invalid_returns_issues_not_raise():
    """Spec-invalid builds return issues as values an agent can correct."""
    kit = FHIRToolkit()

    result = kit.run_tool(
        "build_resource",
        {
            "resource_type": "MedicationStatement",
            "subject": "Patient/1",
            "status": "recorded",  # R5 vocabulary — invalid in R4B
            "code": "1",
        },
    )

    assert result["ok"] is False
    assert any("recorded" in i["diagnostics"] for i in result["issues"])


def test_build_resource_error_values():
    """Unknown types and missing requireds are errors as values, never raises."""
    kit = FHIRToolkit()

    assert (
        "Unsupported"
        in kit.run_tool("build_resource", {"resource_type": "Basic"})["error"]
    )
    assert kit.run_tool("build_resource", {"resource_type": "Condition"})["ok"] is False
    assert (
        kit.run_tool(
            "build_resource", {"resource_type": "Observation", "code": "8867-4"}
        )["ok"]
        is False
    )


def test_validate_resource_passthrough():
    """validate_resource returns the library report as a JSON-safe dict."""
    report = FHIRToolkit().run_tool(
        "validate_resource",
        {
            "resource": {
                "resourceType": "MedicationStatement",
                "status": "recorded",
                "subject": {"reference": "Patient/1"},
                "medicationCodeableConcept": {"text": "Aspirin"},
            }
        },
    )

    assert report["valid"] is False
    assert report["issues"][0]["expression"] == "MedicationStatement.status"


def test_load_bundle_and_read_tools():
    """load_bundle sets the working bundle; read tools operate on it."""
    kit = FHIRToolkit()

    loaded = kit.run_tool("load_bundle", {"source": BUNDLE_PATH})
    assert loaded["ok"] is True
    assert loaded["resource_counts"]["Patient"] == 1

    resources = kit.run_tool("get_resources", {"resource_type": "Condition"})
    assert len(resources) == 1

    entries = kit.run_tool("get_coded_entries", {"resource_type": "MedicationRequest"})
    assert len(entries) == 1
    json.dumps(entries)

    # The agent-facing date field is authored_on (renamed from `date`)
    from healthchain.fhir import CodedEntry

    assert "authored_on" in CodedEntry.model_fields
    assert "date" not in CodedEntry.model_fields


def test_load_bundle_invalid_returns_issues():
    """An invalid bundle returns the validation report, not a raise."""
    result = FHIRToolkit().run_tool(
        "load_bundle",
        {"source": json.dumps({"resourceType": "Bundle", "type": "bogus"})},
    )

    assert result["ok"] is False
    assert result["issues"]


def test_read_tools_without_bundle_return_error_value():
    """Read tools explain the missing bundle instead of failing opaquely."""
    kit = FHIRToolkit()

    for name, args in [
        ("get_resources", {"resource_type": "Condition"}),
        ("get_coded_entries", {"resource_type": "Condition"}),
        ("resolve_reference", {"reference": "Patient/1"}),
    ]:
        result = kit.run_tool(name, args)
        assert result["ok"] is False
        assert "load_bundle" in result["error"]


def test_resolve_reference_plain_and_contained():
    """Plain refs resolve directly; contained refs need parent_resource_id."""
    kit = FHIRToolkit(bundle=BUNDLE_PATH)

    plain = kit.run_tool("resolve_reference", {"reference": "Patient/patient-1"})
    assert plain["ok"] is True
    assert plain["resource"]["resourceType"] == "Patient"

    hint = kit.run_tool("resolve_reference", {"reference": "#requester-1"})
    assert hint["ok"] is False
    assert "parent_resource_id" in hint["error"]

    contained = kit.run_tool(
        "resolve_reference",
        {"reference": "#requester-1", "parent_resource_id": "medicationrequest-1"},
    )
    assert contained["ok"] is True
    assert contained["resource"]["id"] == "requester-1"

    missing = kit.run_tool("resolve_reference", {"reference": "Patient/nope"})
    assert missing["ok"] is False


def test_lookup_code_and_list_codes():
    """lookup_code needs a query and points at list_codes for browsing."""
    kit = FHIRToolkit()

    results = kit.run_tool("lookup_code", {"query": "hypertension"})
    assert results[0]["code"] == "I10"

    empty = kit.run_tool("lookup_code", {"query": "  "})
    assert empty["ok"] is False
    assert "list_codes" in empty["error"]

    catalog = kit.run_tool("list_codes", {})
    assert len(catalog) == len(LocalCodeLookup().entries())

    filtered = kit.run_tool("list_codes", {"system": "http://loinc.org"})
    assert {c["system"] for c in filtered} == {"http://loinc.org"}


def test_custom_lookup_is_used():
    """A site lookup plugs in behind the same tools."""
    kit = FHIRToolkit(
        lookup=LocalCodeLookup(
            catalog=[Coding(code="X1", display="Sitedrug", system="urn:site")]
        )
    )

    assert kit.run_tool("lookup_code", {"query": "sitedrug"})[0]["code"] == "X1"


def test_run_tool_unknown_and_json_arguments():
    """run_tool accepts JSON-string arguments and reports unknown tools."""
    kit = FHIRToolkit()

    assert kit.run_tool("nope", {})["ok"] is False
    results = kit.run_tool("lookup_code", '{"query": "aspirin"}')
    assert results[0]["code"] == "243670"


def test_tool_from_callable_schema_generation():
    """Schemas come from signatures: requireds, optionals, and types."""

    def sample(a: str, b: float = 1.0, c: str = None) -> dict:
        """Sample tool."""
        return {}

    tool = Tool.from_callable(sample)

    assert tool.name == "sample"
    assert tool.description == "Sample tool."
    assert tool.input_schema["required"] == ["a"]
    assert tool.input_schema["properties"]["a"]["type"] == "string"


@pytest.mark.skipif(importlib.util.find_spec("mcp") is None, reason="mcp not installed")
def test_as_mcp_smoke():
    """as_mcp registers every tool on a FastMCP server."""
    import anyio

    server = FHIRToolkit().as_mcp()

    tool_names = {t.name for t in anyio.run(server.list_tools)}
    assert {"build_resource", "lookup_code", "list_codes"} <= tool_names


@pytest.mark.skipif(
    importlib.util.find_spec("langchain_core") is None,
    reason="langchain-core not installed",
)
def test_as_langchain_smoke():
    """as_langchain wraps every tool as a StructuredTool."""
    tools = FHIRToolkit().as_langchain()

    assert [t.name for t in tools][0] == "build_resource"
    assert tools[0].args_schema is not None


def test_view_import_errors_name_the_extra():
    """Missing optional deps produce install hints, not bare ImportErrors."""
    if importlib.util.find_spec("mcp") is None:
        with pytest.raises(ImportError, match="healthchain\\[mcp\\]"):
            FHIRToolkit().as_mcp()
    if importlib.util.find_spec("langchain_core") is None:
        with pytest.raises(ImportError, match="healthchain\\[langchain\\]"):
            FHIRToolkit().as_langchain()
