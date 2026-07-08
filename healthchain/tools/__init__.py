"""Agent tools over the healthchain.fhir surface.

Framework-agnostic tool callables at the core (``Tool``), packaged by
``FHIRToolkit`` with ``.as_mcp()`` / ``.as_langchain()`` views and plain-dict
specs for hand-rolled tool-calling loops.
"""

from healthchain.tools.base import Tool
from healthchain.tools.toolkit import FHIRToolkit

__all__ = ["FHIRToolkit", "Tool"]
