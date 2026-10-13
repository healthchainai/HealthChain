# Agent Tools

Agent tools over the healthchain.fhir surface.

Framework-agnostic tool callables at the core (`Tool`), packaged by `FHIRToolkit` with `.as_mcp()` / `.as_langchain()` views and plain-dict specs for hand-rolled tool-calling loops.

## `FHIRToolkit`

Agent tools over the healthchain.fhir build/validate/read/lookup surface.

| PARAMETER | DESCRIPTION                                                                                                                                                                                                                                                              |
| --------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `bundle`  | Optional bundle to preload — a Bundle instance, dict, JSON string, or file path. Validated once on assignment (host-injected data path). Agents can also load one via the load_bundle tool. **TYPE:** `Optional[Union[Bundle, Dict[str, Any], str]]` **DEFAULT:** `None` |
| `lookup`  | Any TerminologyLookup. Defaults to LocalCodeLookup's demo catalog. If the lookup is enumerable (has entries()), a list_codes tool is registered alongside lookup_code. **TYPE:** `Optional[TerminologyLookup]` **DEFAULT:** `None`                                       |

Example

> > > kit = FHIRToolkit(bundle="synthea_patient.json") tools = kit.get_tools() [t.name for t in tools] # doctest: +ELLIPSIS ['build_resource', 'validate_resource', 'load_bundle', ...] kit.as_mcp().run() # MCP server (pip install healthchain[mcp]) kit.as_langchain() # LangChain tools (healthchain[langchain]) [t.spec for t in tools] # plain dicts for a hand-rolled loop

### `bundle`

The loaded bundle the read tools operate on.

### `as_langchain()`

Package the toolkit as LangChain tools (requires healthchain[langchain]).

### `as_mcp(name='healthchain', **fastmcp_kwargs)`

Package the toolkit as an MCP server (requires healthchain[mcp]).

Returns a FastMCP instance; call `.run()` on it to serve over stdio, or `.run(transport="streamable-http")` for HTTP.

### `get_tools()`

The toolkit as framework-agnostic tools (LangChain toolkit idiom).

### `run_tool(name, arguments)`

Run a tool by name with dict or JSON-string arguments.

Convenience for hand-rolled agent loops: pass the tool_use block's name and input straight through.

## `Tool`

Bases: `BaseModel`

An agent tool: name, when-to-call description, flat schema, callable.

`run()` returns JSON-safe values (dicts/lists of plain types) and reports failures as values (`{"ok": False, "error": ...}`) rather than raising — a raised exception kills an agent loop, an error value is something the model can read and correct.

### `spec`

The tool definition as a plain dict (Anthropic tools= shape).

### `from_callable(fn, name=None, description=None)`

Wrap a plain typed callable, inferring the schema from its signature.

### `run(**kwargs)`

Call the tool. Returns JSON-safe values; errors come back as values.

### `run_json(**kwargs)`

Call the tool and serialize the result to a JSON string.

## `base`

Framework-agnostic agent tool core.

A `Tool` wraps a plain typed callable with the three fields every tool-calling stack understands — `name`, `description`, `input_schema` — plus a `run` that returns JSON-safe values with errors as values, never exceptions. The same shape plugs into MCP (`FHIRToolkit.as_mcp`), LangChain (`as_langchain`), or a hand-rolled Anthropic/OpenAI loop (`tool.spec`).

### `Tool`

Bases: `BaseModel`

An agent tool: name, when-to-call description, flat schema, callable.

`run()` returns JSON-safe values (dicts/lists of plain types) and reports failures as values (`{"ok": False, "error": ...}`) rather than raising — a raised exception kills an agent loop, an error value is something the model can read and correct.

#### `spec`

The tool definition as a plain dict (Anthropic tools= shape).

#### `from_callable(fn, name=None, description=None)`

Wrap a plain typed callable, inferring the schema from its signature.

#### `run(**kwargs)`

Call the tool. Returns JSON-safe values; errors come back as values.

#### `run_json(**kwargs)`

Call the tool and serialize the result to a JSON string.

## `toolkit`

FHIRToolkit — the healthchain.fhir surface packaged as agent tools.

The toolkit is stateful by design: it holds one loaded bundle, validated once at load time, so read tools operate on "the loaded bundle" instead of shuttling bundle JSON through tool arguments (which agents cannot do at realistic bundle sizes, and which would re-validate on every call).

Prior art: LangChain's toolkit idiom (`SQLDatabaseToolkit(db=...).get_tools()`) for the stateful-object-bundling-tools shape; MCP FastMCP and LangChain `StructuredTool.from_function` both wrap plain typed callables, which is what `get_tools()` returns via the `Tool` core.

### `FHIRToolkit`

Agent tools over the healthchain.fhir build/validate/read/lookup surface.

| PARAMETER | DESCRIPTION                                                                                                                                                                                                                                                              |
| --------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `bundle`  | Optional bundle to preload — a Bundle instance, dict, JSON string, or file path. Validated once on assignment (host-injected data path). Agents can also load one via the load_bundle tool. **TYPE:** `Optional[Union[Bundle, Dict[str, Any], str]]` **DEFAULT:** `None` |
| `lookup`  | Any TerminologyLookup. Defaults to LocalCodeLookup's demo catalog. If the lookup is enumerable (has entries()), a list_codes tool is registered alongside lookup_code. **TYPE:** `Optional[TerminologyLookup]` **DEFAULT:** `None`                                       |

Example

> > > kit = FHIRToolkit(bundle="synthea_patient.json") tools = kit.get_tools() [t.name for t in tools] # doctest: +ELLIPSIS ['build_resource', 'validate_resource', 'load_bundle', ...] kit.as_mcp().run() # MCP server (pip install healthchain[mcp]) kit.as_langchain() # LangChain tools (healthchain[langchain]) [t.spec for t in tools] # plain dicts for a hand-rolled loop

#### `bundle`

The loaded bundle the read tools operate on.

#### `as_langchain()`

Package the toolkit as LangChain tools (requires healthchain[langchain]).

#### `as_mcp(name='healthchain', **fastmcp_kwargs)`

Package the toolkit as an MCP server (requires healthchain[mcp]).

Returns a FastMCP instance; call `.run()` on it to serve over stdio, or `.run(transport="streamable-http")` for HTTP.

#### `get_tools()`

The toolkit as framework-agnostic tools (LangChain toolkit idiom).

#### `run_tool(name, arguments)`

Run a tool by name with dict or JSON-string arguments.

Convenience for hand-rolled agent loops: pass the tool_use block's name and input straight through.
