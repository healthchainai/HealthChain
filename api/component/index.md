# Component

## `BaseComponent`

Bases: `ABC`

Abstract base class for all components in the pipeline.

This class should be subclassed to create specific components. Subclasses must implement the **call** method.

### `__call__(data)`

Process the input document and return the processed document.

| PARAMETER | DESCRIPTION                                              |
| --------- | -------------------------------------------------------- |
| `data`    | The input document to be processed. **TYPE:** `Document` |

| RETURNS    | DESCRIPTION                                  |
| ---------- | -------------------------------------------- |
| `Document` | The processed document. **TYPE:** `Document` |

## `Component`

Bases: `BaseComponent`

A concrete implementation of the BaseComponent class.

This class can be used as a base for creating specific components that do not require any additional processing logic.

| METHOD     | DESCRIPTION                                                                                                                                             |
| ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `__call__` | Document) -> Document: Process the input document and return the processed document. In this implementation, the input document is returned unmodified. |
