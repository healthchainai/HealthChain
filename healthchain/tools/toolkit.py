"""FHIRToolkit — the healthchain.fhir surface packaged as agent tools.

The toolkit is stateful by design: it holds one loaded bundle, validated once
at load time, so read tools operate on "the loaded bundle" instead of
shuttling bundle JSON through tool arguments (which agents cannot do at
realistic bundle sizes, and which would re-validate on every call).

Prior art: LangChain's toolkit idiom (``SQLDatabaseToolkit(db=...).get_tools()``)
for the stateful-object-bundling-tools shape; MCP FastMCP and LangChain
``StructuredTool.from_function`` both wrap plain typed callables, which is
what ``get_tools()`` returns via the ``Tool`` core.
"""

import json

from typing import Any, Dict, List, Optional, Union

from fhir.resources.R4B.bundle import Bundle

from healthchain.fhir import (
    count_resources,
    create_allergy_intolerance,
    create_condition,
    create_dosage,
    create_medication_statement,
    create_patient,
    create_value_quantity_observation,
    get_coded_entries,
    get_resources,
    load_bundle,
    resolve_reference,
    validate_resource,
)
from healthchain.fhir.validation import FHIRValidationError
from healthchain.terminology import LocalCodeLookup, TerminologyLookup
from healthchain.tools.base import Tool

_JSON_DUMP = {"mode": "json", "exclude_none": True}

_BUILDABLE_TYPES = (
    "Condition",
    "MedicationStatement",
    "Observation",
    "AllergyIntolerance",
    "Patient",
)

_NO_BUNDLE_ERROR = {
    "ok": False,
    "error": "No bundle loaded. Call load_bundle first, or the host application "
    "must supply a bundle to the toolkit.",
}


def _error(message: str, **extra: Any) -> Dict[str, Any]:
    return {"ok": False, "error": message, **extra}


class FHIRToolkit:
    """Agent tools over the healthchain.fhir build/validate/read/lookup surface.

    Args:
        bundle: Optional bundle to preload — a Bundle instance, dict, JSON
            string, or file path. Validated once on assignment (host-injected
            data path). Agents can also load one via the load_bundle tool.
        lookup: Any TerminologyLookup. Defaults to LocalCodeLookup's demo
            catalog. If the lookup is enumerable (has ``entries()``), a
            ``list_codes`` tool is registered alongside ``lookup_code``.

    Example:
        >>> kit = FHIRToolkit(bundle="synthea_patient.json")
        >>> tools = kit.get_tools()
        >>> [t.name for t in tools]  # doctest: +ELLIPSIS
        ['build_resource', 'validate_resource', 'load_bundle', ...]
        >>> kit.as_mcp().run()          # MCP server (pip install healthchain[mcp])
        >>> kit.as_langchain()          # LangChain tools (healthchain[langchain])
        >>> [t.spec for t in tools]     # plain dicts for a hand-rolled loop
    """

    def __init__(
        self,
        bundle: Optional[Union[Bundle, Dict[str, Any], str]] = None,
        lookup: Optional[TerminologyLookup] = None,
    ) -> None:
        self._bundle: Optional[Bundle] = None
        self.lookup: TerminologyLookup = (
            lookup if lookup is not None else LocalCodeLookup()
        )
        if bundle is not None:
            self.bundle = bundle

    @property
    def bundle(self) -> Optional[Bundle]:
        """The loaded bundle the read tools operate on."""
        return self._bundle

    @bundle.setter
    def bundle(self, source: Union[Bundle, Dict[str, Any], str]) -> None:
        if isinstance(source, Bundle):
            self._bundle = source
        else:
            self._bundle = load_bundle(source)

    # -- tool implementations -------------------------------------------------

    def _build_resource(
        self,
        resource_type: str,
        subject: Optional[str] = None,
        code: Optional[str] = None,
        display: Optional[str] = None,
        system: Optional[str] = None,
        status: Optional[str] = None,
        value: Optional[float] = None,
        unit: Optional[str] = None,
        effective_datetime: Optional[str] = None,
        onset: Optional[str] = None,
        dose_value: Optional[float] = None,
        dose_unit: Optional[str] = None,
        frequency_per_day: Optional[int] = None,
        dosage_text: Optional[str] = None,
        gender: Optional[str] = None,
        birth_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        try:
            if resource_type == "Condition":
                if subject is None:
                    return _error("Condition requires subject (e.g. 'Patient/123')")
                kwargs: Dict[str, Any] = {"subject": subject, "onset": onset}
                if status is not None:
                    kwargs["clinical_status"] = status
                if system is not None:
                    kwargs["system"] = system
                resource = create_condition(
                    code=code, display=display, warn=False, **kwargs
                )
            elif resource_type == "MedicationStatement":
                if subject is None:
                    return _error(
                        "MedicationStatement requires subject (e.g. 'Patient/123')"
                    )
                dosage = None
                if dose_value is not None or dose_unit is not None:
                    if dose_value is None or dose_unit is None:
                        return _error(
                            "dose_value and dose_unit must be provided together"
                        )
                    dosage = create_dosage(
                        text=dosage_text,
                        dose_value=dose_value,
                        dose_unit=dose_unit,
                        frequency=frequency_per_day,
                        period=1.0 if frequency_per_day is not None else None,
                        period_unit="d" if frequency_per_day is not None else None,
                    )
                elif dosage_text is not None:
                    dosage = dosage_text
                kwargs = {"subject": subject, "dosage": dosage}
                if status is not None:
                    kwargs["status"] = status
                if system is not None:
                    kwargs["system"] = system
                resource = create_medication_statement(
                    code=code, display=display, warn=False, **kwargs
                )
            elif resource_type == "Observation":
                if code is None or value is None or unit is None:
                    return _error("Observation requires code, value, and unit")
                kwargs = {
                    "subject": subject,
                    "effective_datetime": effective_datetime,
                    "display": display,
                }
                if status is not None:
                    kwargs["status"] = status
                if system is not None:
                    kwargs["system"] = system
                resource = create_value_quantity_observation(
                    code=code, value=value, unit=unit, warn=False, **kwargs
                )
            elif resource_type == "AllergyIntolerance":
                if subject is None:
                    return _error(
                        "AllergyIntolerance requires subject (e.g. 'Patient/123')"
                    )
                kwargs = {}
                if system is not None:
                    kwargs["system"] = system
                resource = create_allergy_intolerance(
                    patient=subject, code=code, display=display, warn=False, **kwargs
                )
            elif resource_type == "Patient":
                resource = create_patient(
                    gender=gender, birth_date=birth_date, warn=False
                )
            else:
                return _error(
                    f"Unsupported resource_type '{resource_type}'. "
                    f"Supported: {', '.join(_BUILDABLE_TYPES)}"
                )
        except Exception as e:  # errors are values on the build path
            return _error(str(e))

        report = validate_resource(resource)
        if not report.valid:
            return {
                "ok": False,
                "issues": [i.model_dump(**_JSON_DUMP) for i in report.issues],
            }
        return {"ok": True, "resource": resource.model_dump(**_JSON_DUMP)}

    def _validate_resource(
        self, resource: Dict[str, Any], resource_type: Optional[str] = None
    ) -> Dict[str, Any]:
        report = validate_resource(resource, resource_type=resource_type)
        return report.model_dump(**_JSON_DUMP)

    def _load_bundle(self, source: str) -> Dict[str, Any]:
        try:
            self._bundle = load_bundle(source)
        except FHIRValidationError as e:
            return {
                "ok": False,
                "issues": [i.model_dump(**_JSON_DUMP) for i in e.report.issues],
            }
        except Exception as e:
            return _error(str(e))
        return {"ok": True, "resource_counts": count_resources(self._bundle)}

    def _get_resources(self, resource_type: str) -> Any:
        if self._bundle is None:
            return _NO_BUNDLE_ERROR
        try:
            resources = get_resources(self._bundle, resource_type)
        except Exception as e:
            return _error(str(e))
        return [r.model_dump(**_JSON_DUMP) for r in resources]

    def _get_coded_entries(
        self, resource_type: str, status: Optional[str] = None
    ) -> Any:
        if self._bundle is None:
            return _NO_BUNDLE_ERROR
        try:
            entries = get_coded_entries(self._bundle, resource_type, status=status)
        except Exception as e:
            return _error(str(e))
        return [e.model_dump(**_JSON_DUMP) for e in entries]

    def _resolve_reference(
        self, reference: str, parent_resource_id: Optional[str] = None
    ) -> Dict[str, Any]:
        if self._bundle is None:
            return _NO_BUNDLE_ERROR
        parent = None
        if parent_resource_id is not None:
            for entry in self._bundle.entry or []:
                resource = entry.resource
                if resource is not None and resource.id == parent_resource_id:
                    parent = resource
                    break
            if parent is None:
                return _error(
                    f"No resource with id '{parent_resource_id}' in the loaded bundle"
                )
        if reference.startswith("#") and parent is None:
            return _error(
                f"'{reference}' is a contained reference; pass parent_resource_id "
                "(the id of the resource that contains it)"
            )
        target = resolve_reference(self._bundle, reference, parent=parent)
        if target is None:
            return _error(f"Reference '{reference}' not found in the loaded bundle")
        return {"ok": True, "resource": target.model_dump(**_JSON_DUMP)}

    def _lookup_code(self, query: str, system: Optional[str] = None) -> Any:
        if not query or not query.strip():
            hint = (
                " Use list_codes to browse the whole catalog."
                if hasattr(self.lookup, "entries")
                else ""
            )
            return _error(f"query must be a non-empty search string.{hint}")
        return [c.model_dump(**_JSON_DUMP) for c in self.lookup.search(query, system)]

    def _list_codes(self, system: Optional[str] = None) -> Any:
        return [
            c.model_dump(**_JSON_DUMP)
            for c in self.lookup.entries()
            if system is None or c.system == system
        ]

    # -- tool packaging -------------------------------------------------------

    def get_tools(self) -> List[Tool]:
        """The toolkit as framework-agnostic tools (LangChain toolkit idiom)."""
        tools = [
            Tool.from_callable(
                self._build_resource,
                name="build_resource",
                description=(
                    "Build a FHIR resource from flat fields and validate it. Call "
                    "this instead of writing FHIR JSON by hand — it does the "
                    "nesting (CodeableConcepts, Dosage) and returns "
                    "{ok, resource} or {ok: false, issues} to correct. Supported "
                    f"resource_type values: {', '.join(_BUILDABLE_TYPES)}. Use a "
                    "code returned by lookup_code, never an invented one."
                ),
            ),
            Tool.from_callable(
                self._validate_resource,
                name="validate_resource",
                description=(
                    "Validate a FHIR resource (JSON object) against the spec, "
                    "including required value-set bindings. Call this after "
                    "constructing or editing FHIR JSON yourself; read issues[] "
                    "(severity/diagnostics/expression) and correct the resource. "
                    "Never raises."
                ),
            ),
            Tool.from_callable(
                self._load_bundle,
                name="load_bundle",
                description=(
                    "Load a FHIR Bundle from a file path or JSON string and make "
                    "it the working bundle for the read tools. Call this first "
                    "when given bundle data. Invalid bundles return issues[] "
                    "locating each problem (e.g. Bundle.entry[2].resource.subject)."
                ),
            ),
            Tool.from_callable(
                self._get_resources,
                name="get_resources",
                description=(
                    "Get all resources of a type from the loaded bundle as full "
                    "FHIR JSON. Call this when you need fields the flattened "
                    "get_coded_entries view doesn't carry."
                ),
            ),
            Tool.from_callable(
                self._get_coded_entries,
                name="get_coded_entries",
                description=(
                    "Read the coded identity of every resource of a type in the "
                    "loaded bundle as flat records (code/display/system/status/"
                    "authored_on/value/unit). Call this first for questions about "
                    "conditions, medications, allergies, or observations — it "
                    "resolves medicationReference to the actual Medication for you. "
                    "Optionally filter by status (e.g. 'active')."
                ),
            ),
            Tool.from_callable(
                self._resolve_reference,
                name="resolve_reference",
                description=(
                    "Resolve a FHIR reference (e.g. 'Patient/123', 'urn:uuid:...') "
                    "to its target resource within the loaded bundle. For a "
                    "contained reference ('#med1'), also pass parent_resource_id — "
                    "the id of the resource the reference appears in."
                ),
            ),
            Tool.from_callable(
                self._lookup_code,
                name="lookup_code",
                description=(
                    "Search the terminology catalog for codes matching free text "
                    "(e.g. 'metoprolol 25', 'type 2 diabetes'). Call this whenever "
                    "you need a code — use a returned candidate, never invent or "
                    "recall one. Results are ranked tightest-match-first; "
                    "optionally restrict to one code system URI."
                ),
            ),
        ]
        if hasattr(self.lookup, "entries"):
            tools.append(
                Tool.from_callable(
                    self._list_codes,
                    name="list_codes",
                    description=(
                        "List every code in the local terminology catalog, "
                        "optionally filtered to one code system URI. Call this to "
                        "browse what codes are available (e.g. to build a mention "
                        "list); use lookup_code to search by name."
                    ),
                )
            )
        return tools

    def as_mcp(self, name: str = "healthchain", **fastmcp_kwargs: Any):
        """Package the toolkit as an MCP server (requires healthchain[mcp]).

        Returns a FastMCP instance; call ``.run()`` on it to serve over stdio,
        or ``.run(transport="streamable-http")`` for HTTP.
        """
        try:
            from mcp.server.fastmcp import FastMCP
        except ImportError:
            raise ImportError(
                "Could not import mcp. Install it with: `pip install healthchain[mcp]`"
            )

        instructions = fastmcp_kwargs.pop(
            "instructions",
            "FHIR tools for clinical data: build and validate resources, read "
            "loaded bundles, and look up terminology codes. Codes should come "
            "from lookup_code, never from memory.",
        )
        server = FastMCP(name, instructions=instructions, **fastmcp_kwargs)
        for tool in self.get_tools():
            # structured_output=False: results are JSON content. FastMCP cannot
            # derive an output model from Dict[str, Any] returns, and the
            # errors-as-values convention needs no output schema.
            server.add_tool(
                tool.fn,
                name=tool.name,
                description=tool.description,
                structured_output=False,
            )
        return server

    def as_langchain(self) -> List[Any]:
        """Package the toolkit as LangChain tools (requires healthchain[langchain])."""
        try:
            from langchain_core.tools import StructuredTool
        except ImportError:
            raise ImportError(
                "Could not import langchain_core. Install it with: "
                "`pip install healthchain[langchain]`"
            )

        return [
            StructuredTool.from_function(
                func=tool.fn, name=tool.name, description=tool.description
            )
            for tool in self.get_tools()
        ]

    def run_tool(self, name: str, arguments: Union[str, Dict[str, Any]]) -> Any:
        """Run a tool by name with dict or JSON-string arguments.

        Convenience for hand-rolled agent loops: pass the tool_use block's
        name and input straight through.
        """
        if isinstance(arguments, str):
            arguments = json.loads(arguments)
        for tool in self.get_tools():
            if tool.name == name:
                return tool.run(**arguments)
        return _error(f"Unknown tool '{name}'")
