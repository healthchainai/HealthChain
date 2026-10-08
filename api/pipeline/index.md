# Pipeline

## `BasePipeline`

Bases: `ABC`

Base class for creating and managing data processing pipelines.

The BasePipeline class provides a framework for building modular data processing pipelines by allowing users to add, remove, and configure components with defined dependencies and execution order. Components can be added at specific positions and grouped into stages.

Pipelines operate on :class:`~healthchain.io.containers.Document` objects: raw input is wrapped into a Document on entry, each component receives and returns a Document, and the final Document is returned.

| ATTRIBUTE         | DESCRIPTION                                                                  |
| ----------------- | ---------------------------------------------------------------------------- |
| `_components`     | Ordered list of pipeline components **TYPE:** `List[PipelineNode]`           |
| `_stages`         | Components grouped by processing stage **TYPE:** `Dict[str, List[Callable]]` |
| `_built_pipeline` | Compiled pipeline function **TYPE:** `Optional[Callable]`                    |

Example

> > > pipeline = Pipeline() @pipeline.add_node ... def annotate(doc: Document) -> Document: ... ... ... return doc result = pipeline(document) # Document → Document

### `stages`

Returns a human-readable representation of the pipeline stages.

### `add_node(component=None, *, position='default', reference=None, stage=None, name=None, input_model=None, output_model=None, dependencies=[])`

Adds a component node to the pipeline.

| PARAMETER      | DESCRIPTION                                                                                                                                                                                                       |
| -------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `component`    | The component to be added. It can be either a BaseComponent object or a callable function. Defaults to None. **TYPE:** `Union[BaseComponent, Callable[[Document], Document]]` **DEFAULT:** `None`                 |
| `position`     | The position at which the component should be added in the pipeline. Valid values are "default", "first", "last", "after", and "before". Defaults to "default". **TYPE:** `PositionType` **DEFAULT:** `'default'` |
| `reference`    | The name of the component after or before which the new component should be added. Only applicable when position is "after" or "before". Defaults to None. **TYPE:** `str` **DEFAULT:** `None`                    |
| `stage`        | The stage to which the component belongs. Defaults to None. **TYPE:** `str` **DEFAULT:** `None`                                                                                                                   |
| `name`         | The name of the component. Defaults to None, in which case the name of the function will be used. **TYPE:** `str` **DEFAULT:** `None`                                                                             |
| `input_model`  | The input Pydantic model class for validating the input data. Defaults to None. **TYPE:** `Type[BaseModel]` **DEFAULT:** `None`                                                                                   |
| `output_model` | The output Pydantic model class for validating the output data. Defaults to None. **TYPE:** `Type[BaseModel]` **DEFAULT:** `None`                                                                                 |
| `dependencies` | The list of component names that this component depends on. Defaults to an empty list. **TYPE:** `List[str]` **DEFAULT:** `[]`                                                                                    |

| RETURNS | DESCRIPTION                                                                  |
| ------- | ---------------------------------------------------------------------------- |
| `None`  | The original component if component is None, otherwise the wrapper function. |

### `build()`

Builds and returns a pipeline function that applies a series of components to the input data. Returns: pipeline: A function that takes input data and applies the ordered components to it. Raises: ValueError: If a circular dependency is detected among the components.

### `remove(component_name)`

Removes a component from the pipeline.

| PARAMETER        | DESCRIPTION                                              |
| ---------------- | -------------------------------------------------------- |
| `component_name` | The name of the component to be removed. **TYPE:** `str` |

| RAISES       | DESCRIPTION                                    |
| ------------ | ---------------------------------------------- |
| `ValueError` | If the component is not found in the pipeline. |

| RETURNS | DESCRIPTION |
| ------- | ----------- |
| `None`  | None        |

Logs

DEBUG: When the component is successfully removed. WARNING: If the component fails to be removed after attempting to do so.

### `replace(old_component_name, new_component)`

Replaces a component in the pipeline with a new component.

| PARAMETER            | DESCRIPTION                                                                                                           |
| -------------------- | --------------------------------------------------------------------------------------------------------------------- |
| `old_component_name` | The name of the component to be replaced. **TYPE:** `str`                                                             |
| `new_component`      | The new component to replace the old component with. **TYPE:** `Union[BaseComponent, Callable[[Document], Document]]` |

| RETURNS | DESCRIPTION |
| ------- | ----------- |
| `None`  | None        |

| RAISES       | DESCRIPTION                                                       |
| ------------ | ----------------------------------------------------------------- |
| `ValueError` | If the old component is not found in the pipeline.                |
| `ValueError` | If the new component is not a BaseComponent or a callable.        |
| `ValueError` | If the new component callable doesn't have the correct signature. |

Logs

DEBUG: When the component is successfully replaced.

## `Pipeline`

Bases: `BasePipeline`

Default pipeline for composing Document processing steps.

Add steps with :meth:`add_node` (as a decorator or by passing a callable), then call the pipeline with text or a :class:`~healthchain.io.containers.Document`. Raw input is wrapped into a Document automatically.

Example

> > > pipeline = Pipeline() @pipeline.add_node ... def annotate(doc: Document) -> Document: ... return doc result = pipeline("some clinical text") # str → Document

## `PipelineNode`

Represents a node in a pipeline.

| ATTRIBUTE      | DESCRIPTION                                                                                                                                 |
| -------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| `func`         | The function to be applied to the document. **TYPE:** `Callable[[Document], Document]`                                                      |
| `position`     | The position of the node in the pipeline. Defaults to "default". **TYPE:** `PositionType`                                                   |
| `reference`    | The reference for the relative position of the node. Name should be the "name" attribute of another node. Defaults to None. **TYPE:** `str` |
| `stage`        | The stage of the node in the pipeline. Group nodes by stage e.g. "preprocessing". Defaults to None. **TYPE:** `str`                         |
| `name`         | The name of the node. Defaults to None. **TYPE:** `str`                                                                                     |
| `dependencies` | The list of dependencies for the node. Defaults to an empty list. **TYPE:** `List[str]`                                                     |
