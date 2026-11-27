# InteropEngine

The `InteropEngine` is the core component of the HealthChain interoperability module. It provides a unified interface for converting between different healthcare data formats.

The interop/CDA layer requires the `cda` extra: `pip install healthchain[cda]`.

## Basic Usage

```python
from healthchain.interop import create_interop, FormatType

# Create an interoperability engine
engine = create_interop()

# Convert CDA XML to FHIR resources
fhir_resources = engine.to_fhir(cda_xml, src_format=FormatType.CDA)

# Convert FHIR resources to CDA XML
cda_xml = engine.from_fhir(fhir_resources, dest_format=FormatType.CDA)
```

## Creating an Engine

The `create_interop()` function is the recommended way to create an engine instance:

```python
from healthchain.interop import create_interop

# Create with default configuration
engine = create_interop()
```

### Custom Configuration

```python
# Use custom config directory
engine = create_interop(config_dir="/path/to/custom/configs")

# Create with custom validation level and environment
engine = create_interop(validation_level="warn", environment="production")
```

> **💡 Tip:** To eject the built-in templates for customization, run:
>
> ```bash
> healthchain eject-templates ./my_configs
> ```
>
> This will create a `my_configs` directory with editable default configuration templates.

## Conversion Methods

All conversions convert to and from FHIR.

| Method                              | Description                                       |
| ----------------------------------- | ------------------------------------------------- |
| `to_fhir(data, src_format)`         | Convert from source format to FHIR resources      |
| `from_fhir(resources, dest_format)` | Convert from FHIR resources to destination format |

### Converting to FHIR

```python
# From CDA
fhir_resources = engine.to_fhir(cda_xml, src_format=FormatType.CDA)
```

### Converting from FHIR

```python
# To CDA
cda_xml = engine.from_fhir(fhir_resources, dest_format=FormatType.CDA)
```

## Accessing Configuration

The engine provides direct access to the underlying configuration manager:

```python
# Access configuration directly
engine.config.set_environment("production")
engine.config.set_validation_level("warn")
value = engine.config.get_config_value("cda.sections.problems.resource")
```

## Custom Components

You can register custom parsers and generators to extend the engine's capabilities. Note that registering a custom parser / generator for an existing format type will replace the default.

```python
from healthchain.interop import FormatType

# Register a custom parser
engine.register_parser(FormatType.CDA, custom_parser)

# Register a custom generator
engine.register_generator(FormatType.FHIR, custom_generator)
```

## Advanced Configuration

For more information on the configuration options, see the [Configuration](https://healthchainai.github.io/HealthChain/reference/interop/configuration/index.md) page.
