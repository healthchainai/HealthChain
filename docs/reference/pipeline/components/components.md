# Component

Components are the building blocks of the healthchain pipeline. They are designed to process data in a consistent manner, allowing for easy composition and reusability.


## Available Components

| Component | Description | Methods |
|-----------|-------------|---------|
| [FHIRProblemListExtractor](fhirproblemextractor.md) | Extracts entities with medical codes and creates FHIR Condition resources with the problem_list extension | `__call__`: Extracts the problem list |

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
