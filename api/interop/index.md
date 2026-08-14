# Interoperability Engine

## `InteropEngine`

Generic interoperability engine for converting between healthcare formats

The InteropEngine provides capabilities for converting between different healthcare data format standards, such as HL7 FHIR and CDA.

The engine uses a template-based approach for transformations, with templates stored in the configured template directory. Transformations are handled by format-specific parsers and generators that are lazily loaded as needed.

Configuration is handled through the `config` property, which provides direct access to the underlying ConfigManager instance. This allows for setting validation levels, changing environments, and accessing configuration values.

The engine supports registering custom parsers, generators, and validators to extend or override the default functionality.

Example

engine = InteropEngine()

### Convert CDA to FHIR

fhir_resources = engine.to_fhir(cda_xml, src_format="cda")

### Convert FHIR to CDA

cda_xml = engine.from_fhir(fhir_resources, dest_format="cda")

### Access config directly:

engine.config.set_environment("production") engine.config.set_validation_level("warn") value = engine.config.get_config_value("cda.sections.problems.resource")

### Access the template registry:

template = engine.template_registry.get_template("cda_fhir/condition") engine.template_registry.add_filter()

### Register custom components:

engine.register_parser(FormatType.CDA, custom_parser) engine.register_generator(FormatType.FHIR, custom_generator)

### Register custom configuration validators:

engine.register_cda_section_config_validator("Procedure", ProcedureSectionConfig) engine.register_cda_document_config_validator("CCD", CCDDocumentConfig)

### `cda_generator`

Lazily load the CDA generator

### `cda_parser`

Lazily load the CDA parser

### `fhir_generator`

Lazily load the FHIR generator

### `__init__(config_dir=None, validation_level=ValidationLevel.STRICT, environment=None)`

Initialize the InteropEngine

| PARAMETER          | DESCRIPTION                                                                                                                            |
| ------------------ | -------------------------------------------------------------------------------------------------------------------------------------- |
| `config_dir`       | Base directory containing configuration files. If None, will search standard locations. **TYPE:** `Optional[Path]` **DEFAULT:** `None` |
| `validation_level` | Level of configuration validation (strict, warn, ignore) **TYPE:** `str` **DEFAULT:** `STRICT`                                         |
| `environment`      | Optional environment to use (development, testing, production) **TYPE:** `Optional[str]` **DEFAULT:** `None`                           |

### `from_fhir(resources, dest_format, **kwargs)`

Convert FHIR resources to a target format

| PARAMETER     | DESCRIPTION                                                                                                                                                |
| ------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `resources`   | List of FHIR resources to convert or a FHIR Bundle **TYPE:** `Union[List[Resource], Bundle]`                                                               |
| `dest_format` | Destination format type, either as string ("cda") or FormatType enum **TYPE:** `Union[str, FormatType]`                                                    |
| `**kwargs`    | Additional arguments to pass to generator. For CDA: document_type (str) - Type of CDA document (e.g. "ccd", "discharge") **TYPE:** `Any` **DEFAULT:** `{}` |

| RETURNS | DESCRIPTION                                        |
| ------- | -------------------------------------------------- |
| `str`   | Converted data as string (CDA XML) **TYPE:** `str` |

| RAISES       | DESCRIPTION                     |
| ------------ | ------------------------------- |
| `ValueError` | If dest_format is not supported |

Example

#### Convert FHIR resources to CDA XML

cda_xml = engine.from_fhir(fhir_resources, dest_format="cda")

### `register_cda_document_config_validator(document_type, document_model)`

Register a custom document validator model for a document type

| PARAMETER        | DESCRIPTION                                                  |
| ---------------- | ------------------------------------------------------------ |
| `document_type`  | Document type (e.g., "ccd", "discharge") **TYPE:** `str`     |
| `document_model` | Pydantic model for document validation **TYPE:** `BaseModel` |

| RETURNS         | DESCRIPTION              |
| --------------- | ------------------------ |
| `InteropEngine` | Self for method chaining |

Example

#### Register a config validator for the CCD document type

engine.register_cda_document_validator( "ccd", CCDDocumentConfig )

### `register_cda_section_config_validator(resource_type, template_model)`

Register a custom section config validator model for a resource type

| PARAMETER        | DESCRIPTION                                                                                                     |
| ---------------- | --------------------------------------------------------------------------------------------------------------- |
| `resource_type`  | FHIR resource type (e.g., "Condition", "MedicationStatement") which converts to the CDA section **TYPE:** `str` |
| `template_model` | Pydantic model for CDA section config validation **TYPE:** `BaseModel`                                          |

| RETURNS         | DESCRIPTION              |
| --------------- | ------------------------ |
| `InteropEngine` | Self for method chaining |

Example

#### Register a config validator for the Problem section, which is converted from the Condition resource

engine.register_cda_section_config_validator( "Condition", ProblemSectionConfig )

### `register_generator(format_type, generator_instance)`

Register a custom generator for a format type. This will replace the default generator for the format type.

| PARAMETER            | DESCRIPTION                                                                           |
| -------------------- | ------------------------------------------------------------------------------------- |
| `format_type`        | The format type (CDA, FHIR) to register the generator for **TYPE:** `FormatType`      |
| `generator_instance` | The generator instance that implements the generation logic **TYPE:** `BaseGenerator` |

| RETURNS         | DESCRIPTION                                                |
| --------------- | ---------------------------------------------------------- |
| `InteropEngine` | Returns self for method chaining **TYPE:** `InteropEngine` |

Example

engine.register_generator(FormatType.CDA, CustomCDAGenerator())

### `register_parser(format_type, parser_instance)`

Register a custom parser for a format type. This will replace the default parser for the format type.

| PARAMETER         | DESCRIPTION                                                                  |
| ----------------- | ---------------------------------------------------------------------------- |
| `format_type`     | The format type (CDA) to register the parser for **TYPE:** `FormatType`      |
| `parser_instance` | The parser instance that implements the parsing logic **TYPE:** `BaseParser` |

| RETURNS         | DESCRIPTION                                                |
| --------------- | ---------------------------------------------------------- |
| `InteropEngine` | Returns self for method chaining **TYPE:** `InteropEngine` |

Example

engine.register_parser(FormatType.CDA, CustomCDAParser())

### `to_fhir(src_data, src_format)`

Convert source data to FHIR resources

| PARAMETER    | DESCRIPTION                                                                                        |
| ------------ | -------------------------------------------------------------------------------------------------- |
| `src_data`   | Input data as string (CDA XML) **TYPE:** `str`                                                     |
| `src_format` | Source format type, either as string ("cda") or FormatType enum **TYPE:** `Union[str, FormatType]` |

| RETURNS          | DESCRIPTION                                                             |
| ---------------- | ----------------------------------------------------------------------- |
| `List[Resource]` | List\[Resource\]: List of FHIR resources generated from the source data |

| RAISES       | DESCRIPTION                    |
| ------------ | ------------------------------ |
| `ValueError` | If src_format is not supported |

Example

#### Convert CDA XML to FHIR resources

fhir_resources = engine.to_fhir(cda_xml, src_format="cda")

## `normalize_resource_list(resources)`

Convert input resources to a normalized list format

InteropConfigManager for HealthChain Interoperability Engine

This module provides specialized configuration management for interoperability.

## `InteropConfigManager`

Bases: `ConfigManager`

Specialized configuration manager for the interoperability module

Extends ConfigManager to handle CDA document and section template configurations. Provides functionality for:

- Loading and validating interop configurations
- Managing document and section templates
- Registering custom validation models

Configuration structure:

- Document templates (under "document")
- Section templates (under "sections")
- Default values and settings

Validation levels:

- STRICT: Full validation (default)
- WARN: Warning-only
- IGNORE: No validation

### `__init__(config_dir, validation_level=ValidationLevel.STRICT, environment=None)`

Initialize the InteropConfigManager.

Initializes the configuration manager with the interop module and validates the configuration. The interop module configuration must exist in the specified config directory.

| PARAMETER          | DESCRIPTION                                                                                                                                                                        |
| ------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `config_dir`       | Base directory containing configuration files **TYPE:** `Path`                                                                                                                     |
| `validation_level` | Level of validation to perform. Default is STRICT. Can be STRICT, WARN, or IGNORE. **TYPE:** `str` **DEFAULT:** `STRICT`                                                           |
| `environment`      | Optional environment name to load environment-specific configs. If provided, will load and merge environment-specific configuration. **TYPE:** `Optional[str]` **DEFAULT:** `None` |

| RAISES       | DESCRIPTION                                                     |
| ------------ | --------------------------------------------------------------- |
| `ValueError` | If the interop module configuration is not found in config_dir. |

### `get_cda_document_config(document_type)`

Get CDA document configuration for a specific document type.

Retrieves the configuration for a CDA document type from the loaded configs. The configuration contains template settings and other document-specific parameters.

| PARAMETER       | DESCRIPTION                                                                   |
| --------------- | ----------------------------------------------------------------------------- |
| `document_type` | Type of document (e.g., "ccd", "discharge") to get config for **TYPE:** `str` |

| RETURNS | DESCRIPTION                                |
| ------- | ------------------------------------------ |
| `Dict`  | Dict containing the document configuration |

| RAISES       | DESCRIPTION                                                   |
| ------------ | ------------------------------------------------------------- |
| `ValueError` | If document_type is not found or the configuration is invalid |

### `get_cda_section_configs(section_key=None)`

Get CDA section configuration(s).

Retrieves section configurations from the loaded configs. When section_key is provided, retrieves configuration for a specific section; otherwise, returns all section configurations. Section configurations define how different CDA sections should be processed and mapped to FHIR resources.

| PARAMETER     | DESCRIPTION                                                                                                                                                                   |
| ------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `section_key` | Optional section identifier (e.g., "problems", "medications"). If provided, returns only that specific section's configuration. **TYPE:** `Optional[str]` **DEFAULT:** `None` |

| RETURNS | DESCRIPTION                                                                                                                                                    |
| ------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `Dict`  | Dictionary mapping section keys to their configurations if section_key is None. Single section configuration dict if section_key is provided. **TYPE:** `Dict` |

| RAISES       | DESCRIPTION                                                                                 |
| ------------ | ------------------------------------------------------------------------------------------- |
| `ValueError` | If section_key is provided but not found in configurations or if no sections are configured |

### `register_cda_document_config(document_type, config_model)`

Register a validation model for a CDA document configuration.

Registers a Pydantic model that will be used to validate configuration for a CDA document type. The model defines the required and optional fields that should be present in the document configuration.

| PARAMETER       | DESCRIPTION                                                                                                 |
| --------------- | ----------------------------------------------------------------------------------------------------------- |
| `document_type` | Document type identifier (e.g., "ccd", "discharge") **TYPE:** `str`                                         |
| `config_model`  | Pydantic model class that defines the validation schema for the document config **TYPE:** `Type[BaseModel]` |

### `register_cda_section_config(resource_type, config_model)`

Register a validation model for a CDA section configuration.

Registers a Pydantic model that will be used to validate configuration for a CDA section that maps to a specific FHIR resource type. The model defines the required and optional fields that should be present in the section configuration.

| PARAMETER       | DESCRIPTION                                                                                                |
| --------------- | ---------------------------------------------------------------------------------------------------------- |
| `resource_type` | FHIR resource type that the section maps to (e.g. "Condition") **TYPE:** `str`                             |
| `config_model`  | Pydantic model class that defines the validation schema for the section config **TYPE:** `Type[BaseModel]` |

### `validate()`

Validate that all required configurations are present for the interop module.

Validates both section and document configurations according to their registered validation models. Section configs are required and will cause validation to fail if missing or invalid. Document configs are optional but will be validated if present.

The validation behavior depends on the validation_level setting:

- IGNORE: Always returns True without validating
- WARN: Logs warnings for validation failures but returns True
- ERROR: Returns False if any validation fails

| RETURNS | DESCRIPTION                                                                                                        |
| ------- | ------------------------------------------------------------------------------------------------------------------ |
| `bool`  | True if validation passes or is ignored, False if validation fails when validation_level is ERROR **TYPE:** `bool` |

## `TemplateRegistry`

Manages loading and accessing Liquid templates for the InteropEngine.

The TemplateRegistry handles loading Liquid template files from a directory and making them available for rendering. It supports custom filter functions that can be used within templates.

Key features:

- Loads .liquid template files recursively from a directory
- Supports adding custom filter functions
- Provides template lookup by name
- Validates template existence

Example

registry = TemplateRegistry(Path("templates")) registry.initialize({ "uppercase": str.upper, "lowercase": str.lower }) template = registry.get_template("cda_fhir/condition")

### `__init__(template_dir)`

Initialize the TemplateRegistry

| PARAMETER      | DESCRIPTION                                          |
| -------------- | ---------------------------------------------------- |
| `template_dir` | Directory containing template files **TYPE:** `Path` |

### `add_filter(name, filter_func)`

Add a custom filter function

| PARAMETER     | DESCRIPTION                                            |
| ------------- | ------------------------------------------------------ |
| `name`        | Name of the filter to use in templates **TYPE:** `str` |
| `filter_func` | Filter function to register **TYPE:** `Callable`       |

| RETURNS            | DESCRIPTION              |
| ------------------ | ------------------------ |
| `TemplateRegistry` | Self for method chaining |

### `add_filters(filters)`

Add multiple custom filter functions

| PARAMETER | DESCRIPTION                                                                    |
| --------- | ------------------------------------------------------------------------------ |
| `filters` | Dictionary of filter names to filter functions **TYPE:** `Dict[str, Callable]` |

| RETURNS            | DESCRIPTION              |
| ------------------ | ------------------------ |
| `TemplateRegistry` | Self for method chaining |

### `get_template(template_key)`

Get a template by key

| PARAMETER      | DESCRIPTION                                                                                                                |
| -------------- | -------------------------------------------------------------------------------------------------------------------------- |
| `template_key` | Template identifier. Can be a full path (e.g., 'cda_fhir/document') or just a filename (e.g., 'document'). **TYPE:** `str` |

| RETURNS    | DESCRIPTION         |
| ---------- | ------------------- |
| `Template` | The template object |

| RAISES     | DESCRIPTION           |
| ---------- | --------------------- |
| `KeyError` | If template not found |

### `has_template(template_key)`

Check if a template exists

| PARAMETER      | DESCRIPTION                                                                                                                |
| -------------- | -------------------------------------------------------------------------------------------------------------------------- |
| `template_key` | Template identifier. Can be a full path (e.g., 'cda_fhir/document') or just a filename (e.g., 'document'). **TYPE:** `str` |

| RETURNS | DESCRIPTION                              |
| ------- | ---------------------------------------- |
| `bool`  | True if template exists, False otherwise |

### `initialize(filters=None)`

Initialize the Liquid environment and load templates.

This method sets up the Liquid template environment by:

1. Storing any provided filter functions
1. Creating the Liquid environment with the template directory
1. Loading all template files from the directory

The environment must be initialized before templates can be loaded or rendered.

| PARAMETER | DESCRIPTION                                                                                                                                                                           |
| --------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `filters` | Optional dictionary mapping filter names to filter functions that can be used in templates. For example: {"uppercase": str.upper} **TYPE:** `Dict[str, Callable]` **DEFAULT:** `None` |

| RETURNS            | DESCRIPTION                                                   |
| ------------------ | ------------------------------------------------------------- |
| `TemplateRegistry` | Returns self for method chaining **TYPE:** `TemplateRegistry` |

| RAISES       | DESCRIPTION                                                              |
| ------------ | ------------------------------------------------------------------------ |
| `ValueError` | If template directory does not exist or environment initialization fails |

CDA Parser for HealthChain Interoperability Engine

This module provides functionality for parsing CDA XML documents.

## `CDAParser`

Bases: `BaseParser`

Parser for CDA XML documents.

The CDAParser class provides functionality to parse Clinical Document Architecture (CDA) XML documents and extract structured data from their sections. It works in conjunction with the InteropConfigManager to identify and process sections based on configuration.

Key capabilities:

- Parse complete CDA XML documents
- Extract entries from configured sections based on template IDs or codes
- Convert and validate section entries into structured dictionaries (xmltodict)

The parser uses configuration from InteropConfigManager to:

- Identify sections by template ID or code
- Map section contents to the appropriate data structures
- Apply any configured transformations

| ATTRIBUTE           | DESCRIPTION                                                     |
| ------------------- | --------------------------------------------------------------- |
| `config`            | Configuration manager instance **TYPE:** `InteropConfigManager` |
| `clinical_document` | Currently loaded CDA document **TYPE:** `ClinicalDocument`      |

### `__init__(config)`

Initialize the CDA parser.

| PARAMETER | DESCRIPTION                                                                                                                                             |
| --------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `config`  | InteropConfigManager instance containing section configurations, templates, and mapping rules for CDA document parsing **TYPE:** `InteropConfigManager` |

### `from_string(data)`

Parse input data and convert it to a structured format.

| PARAMETER | DESCRIPTION                                          |
| --------- | ---------------------------------------------------- |
| `data`    | The CDA XML document string to parse **TYPE:** `str` |

| RETURNS | DESCRIPTION                                                     |
| ------- | --------------------------------------------------------------- |
| `dict`  | A dictionary containing the parsed data structure with sections |

### `parse_document(xml)`

Parse a complete CDA document and extract entries from all configured sections.

This method parses a CDA XML document and extracts entries from each section that is defined in the configuration. It uses xmltodict to parse the XML into a dictionary and then processes each configured section to extract its entries.

| PARAMETER | DESCRIPTION                                          |
| --------- | ---------------------------------------------------- |
| `xml`     | The CDA XML document string to parse **TYPE:** `str` |

| RETURNS                 | DESCRIPTION                                                                                                                                                                               |
| ----------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `Dict[str, List[Dict]]` | Dict\[str, List[Dict]\]: Dictionary mapping section keys (e.g. "problems", "medications") to lists of entry dictionaries containing the parsed data from that section (xmltodict format). |

| RAISES       | DESCRIPTION                                              |
| ------------ | -------------------------------------------------------- |
| `ValueError` | If the XML string is empty or invalid                    |
| `Exception`  | If there is an error parsing the document or any section |

Example

> > > parser = CDAParser(config) sections = parser.from_string(cda_xml) problems = sections.get("problems", [])

CDA Generator for HealthChain Interoperability Engine

This module provides functionality for generating CDA documents.

## `CDAGenerator`

Bases: `BaseGenerator`

Handles generation of CDA documents from FHIR resources.

This class provides functionality to convert FHIR resources into CDA (Clinical Document Architecture) documents using configurable templates. It handles the mapping of resources to appropriate CDA sections, rendering of entries and sections, and generation of the final XML document.

Example

generator = CDAGenerator(config_manager, template_registry)

### Convert FHIR resources to CDA XML document

cda_xml = generator.transform( resources=fhir_resources, document_type="ccd" )

### `generate_document_from_fhir_resources(resources, document_type, validate=True)`

Generate a complete CDA document from FHIR resources

This method handles the entire process of generating a CDA document:

1. Mapping FHIR resources to CDA sections (config)
1. Rendering sections (template)
1. Generating the final document (template)

| PARAMETER       | DESCRIPTION                                                                               |
| --------------- | ----------------------------------------------------------------------------------------- |
| `resources`     | FHIR resources to include in the document **TYPE:** `List[Resource]`                      |
| `document_type` | Type of document to generate **TYPE:** `str`                                              |
| `validate`      | Whether to validate the CDA document (default: True) **TYPE:** `bool` **DEFAULT:** `True` |

| RETURNS | DESCRIPTION                |
| ------- | -------------------------- |
| `str`   | CDA document as XML string |

### `transform(resources, **kwargs)`

Transform FHIR resources to CDA format.

| PARAMETER   | DESCRIPTION                                                           |
| ----------- | --------------------------------------------------------------------- |
| `resources` | List of FHIR resources **TYPE:** `List[Resource]`                     |
| `**kwargs`  | document_type: Type of CDA document **TYPE:** `Any` **DEFAULT:** `{}` |

| RETURNS | DESCRIPTION                                |
| ------- | ------------------------------------------ |
| `str`   | CDA document as XML string **TYPE:** `str` |

FHIR Generator for HealthChain Interoperability Engine

This module provides functionality for generating FHIR resources from templates.

## `FHIRGenerator`

Bases: `BaseGenerator`

Handles generation of FHIR resources from templates.

This class provides functionality to convert CDA section entries into FHIR resources using configurable templates. It handles validation, required field population, and error handling during the conversion process.

Key features:

- Template-based conversion of CDA entries (xmltodict format) to FHIR resources
- Automatic population of required FHIR fields based on configuration for common resource types like Condition and MedicationStatement
- Validation of generated FHIR resources

Example

generator = FHIRGenerator(config_manager, template_registry)

### Convert CDA problem entries to FHIR Condition resources

problems = generator.generate_resources_from_cda_section_entries( entries=problem_entries, section_key="problems" # from configs )

### `generate_resources_from_cda_section_entries(entries, section_key)`

Convert CDA section entries into FHIR resources using configured templates.

This method processes entries from a CDA section and generates corresponding FHIR resources based on templates and configuration. It handles validation and error checking during the conversion process.

| PARAMETER     | DESCRIPTION                                                                                                                                     |
| ------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| `entries`     | List of CDA section entries in xmltodict format to convert **TYPE:** `List[Dict]`                                                               |
| `section_key` | Configuration key identifying the section (e.g. "problems", "medications") Used to look up templates and resource type mappings **TYPE:** `str` |

| RETURNS      | DESCRIPTION                                                                   |
| ------------ | ----------------------------------------------------------------------------- |
| `List[Dict]` | List of validated FHIR resource dictionaries. Empty list if conversion fails. |

Example

#### Convert problem list entries to FHIR Condition resources

conditions = generator.generate_resources_from_cda_section_entries( problem_entries, "problems" )

### `transform(data, **kwargs)`

Transform input data to FHIR resources.

| PARAMETER  | DESCRIPTION                                                                                                                 |
| ---------- | --------------------------------------------------------------------------------------------------------------------------- |
| `data`     | List of entries from source format **TYPE:** `List[Dict]`                                                                   |
| `**kwargs` | src_format: The source format type (FormatType.CDA) section_key: For CDA, the section key **TYPE:** `Any` **DEFAULT:** `{}` |

| RETURNS          | DESCRIPTION                      |
| ---------------- | -------------------------------- |
| `List[Resource]` | List\[Resource\]: FHIR resources |

Configuration validators for HealthChain

This module provides validation models and utilities for configuration files.

## `CcdDocumentConfig`

Bases: `DocumentConfigBase`

Configuration model specific to CCD documents

## `ComponentTemplateConfig`

Bases: `BaseModel`

Generic template for CDA/FHIR component configuration

## `DocumentConfigBase`

Bases: `BaseModel`

Generic document configuration model

## `MedicationSectionTemplateConfig`

Bases: `SectionTemplateConfigBase`

Template configuration for SubstanceAdministration Section

## `NoteSectionTemplateConfig`

Bases: `SectionTemplateConfigBase`

Template configuration for Notes Section

## `ProblemSectionTemplateConfig`

Bases: `SectionTemplateConfigBase`

Template configuration for Problem Section

## `RenderingConfig`

Bases: `BaseModel`

Configuration for section rendering

## `SectionBaseConfig`

Bases: `BaseModel`

Base model for all section configurations

## `SectionIdentifiersConfig`

Bases: `BaseModel`

Section identifiers validation

## `SectionTemplateConfigBase`

Bases: `BaseModel`

Base class for section template configurations

### `validate_component_fields(component, required_fields)`

Helper method to validate required fields in a component

## `create_cda_section_validator(resource_type, template_model)`

Create a section validator for a specific resource type

## `register_cda_document_template_config_model(document_type, document_model)`

Register a custom document model

## `register_cda_section_template_config_model(resource_type, template_model)`

Register a custom template model for a section

## `validate_cda_document_config_model(document_type, document_config)`

Validate a document configuration

## `validate_cda_section_config_model(section_key, section_config)`

Validate a section configuration
