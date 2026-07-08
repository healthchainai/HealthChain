"""Framework-agnostic agent tool core.

A ``Tool`` wraps a plain typed callable with the three fields every
tool-calling stack understands — ``name``, ``description``, ``input_schema``
— plus a ``run`` that returns JSON-safe values with errors as values, never
exceptions. The same shape plugs into MCP (``FHIRToolkit.as_mcp``), LangChain
(``as_langchain``), or a hand-rolled Anthropic/OpenAI loop (``tool.spec``).
"""

import inspect
import json

from typing import Any, Callable, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field, create_model


def _schema_from_signature(fn: Callable[..., Any]) -> Dict[str, Any]:
    """Build a flat JSON Schema for a callable's parameters.

    Uses the same signature-driven generation LangChain and FastMCP apply to
    plain callables, so the schema agents see through ``tool.spec`` matches
    what those frameworks would infer.
    """
    fields: Dict[str, Any] = {}
    for name, param in inspect.signature(fn).parameters.items():
        if name == "self":
            continue
        annotation = (
            param.annotation if param.annotation is not inspect.Parameter.empty else Any
        )
        default = ... if param.default is inspect.Parameter.empty else param.default
        fields[name] = (annotation, default)

    schema = create_model(f"{fn.__name__}_input", **fields).model_json_schema()
    schema.pop("title", None)
    for prop in schema.get("properties", {}).values():
        prop.pop("title", None)
    return schema


class Tool(BaseModel):
    """An agent tool: name, when-to-call description, flat schema, callable.

    ``run()`` returns JSON-safe values (dicts/lists of plain types) and
    reports failures as values (``{"ok": False, "error": ...}``) rather than
    raising — a raised exception kills an agent loop, an error value is
    something the model can read and correct.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str = Field(description="Tool name, snake_case")
    description: str = Field(
        description="Agent-facing description; prescriptive about when to call"
    )
    input_schema: Dict[str, Any] = Field(
        description="Flat JSON Schema for the tool's arguments"
    )
    fn: Callable[..., Any] = Field(exclude=True, repr=False)

    @classmethod
    def from_callable(
        cls,
        fn: Callable[..., Any],
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> "Tool":
        """Wrap a plain typed callable, inferring the schema from its signature."""
        return cls(
            name=name or fn.__name__,
            description=description or inspect.getdoc(fn) or "",
            input_schema=_schema_from_signature(fn),
            fn=fn,
        )

    @property
    def spec(self) -> Dict[str, Any]:
        """The tool definition as a plain dict (Anthropic tools= shape)."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
        }

    def run(self, **kwargs: Any) -> Any:
        """Call the tool. Returns JSON-safe values; errors come back as values."""
        return self.fn(**kwargs)

    def run_json(self, **kwargs: Any) -> str:
        """Call the tool and serialize the result to a JSON string."""
        return json.dumps(self.run(**kwargs))
