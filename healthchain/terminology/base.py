"""Terminology lookup protocol and coding model.

Defines the seam between HealthChain and terminology services: anything with
a ``search(text, system) -> list[Coding]`` method is a terminology lookup.
``LocalCodeLookup`` is the shipped in-process implementation; real terminology
services (a FHIR ``$lookup`` endpoint, a hosted MCP server) plug in behind the
same signature.
"""

from typing import List, Optional, Protocol, runtime_checkable

from pydantic import BaseModel, Field


class Coding(BaseModel):
    """A terminology coding: code, display, and the system it belongs to.

    Version-agnostic and JSON-serializable via ``model_dump()`` so it can be
    returned directly from agent tools.
    """

    code: str = Field(description="The code within the system")
    display: str = Field(description="Human-readable display name")
    system: str = Field(description="Canonical URI of the code system")


@runtime_checkable
class TerminologyLookup(Protocol):
    """Protocol for terminology lookup implementations.

    Implementations search a code system (or all systems they know) for
    codings matching a free-text query and return ranked candidates —
    never a guess. Agents should use a returned code, not invent one.
    """

    def search(self, text: str, system: Optional[str] = None) -> List[Coding]:
        """Search for codings matching free text.

        Args:
            text: Free-text query (e.g. a medication or condition name)
            system: Restrict results to this code system URI

        Returns:
            Ranked list of candidate codings; empty if nothing matches
        """
        ...
