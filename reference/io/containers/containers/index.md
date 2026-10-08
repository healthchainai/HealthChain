# Containers

The `healthchain.io.containers` module provides FHIR-native containers for healthcare data processing. These containers handle the complexities of clinical data formats while providing a clean Python interface for pipelines.

## Available Containers

| Container                                                                                             | Purpose                        | Use Cases                                          |
| ----------------------------------------------------------------------------------------------------- | ------------------------------ | -------------------------------------------------- |
| [**Document**](https://healthchainai.github.io/HealthChain/reference/io/containers/document/index.md) | Clinical text + FHIR resources | Clinical notes, discharge summaries, CDS workflows |

## BaseDocument 📦

`BaseDocument` is the base container that `Document` inherits from. It holds the original input in `data`, exposes a text view in `text`, and provides serialization helpers that skip private (`_`-prefixed) attributes.

```python
from healthchain.io.containers import BaseDocument

doc = BaseDocument("Some data")

# Convert to dictionary and JSON
data_dict = doc.to_dict()
data_json = doc.to_json()
```
