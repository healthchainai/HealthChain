# Component

Components are the building blocks of the healthchain pipeline. A component is anything callable that takes a [`Document`](../../io/containers/document.md) and returns a `Document` — `.add_node()` accepts a plain function just as readily as a component instance.

HealthChain doesn't ship prebuilt components. Bring your own NLP or ML library (spaCy, HuggingFace Transformers, LangChain), run it inside a node, and hand off the results explicitly using `Document`'s FHIR methods (e.g. `doc.update_problem_list(...)`, `doc.fhir.problem_list`).

## Creating Custom Components

You can create your own custom components by extending the `BaseComponent` class and implementing the `__call__` method.

```python
from healthchain.pipeline.base import BaseComponent

class MyCustomComponent(BaseComponent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __call__(self, data):
        # Your custom processing logic here
        return data
```
