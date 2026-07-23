# Sandbox Client

Simplified client for testing healthcare services with various data sources.

This class provides an intuitive interface for:

- Loading test datasets (MIMIC-on-FHIR, Synthea)
- Generating synthetic FHIR data
- Sending requests to healthcare services
- Managing request/response lifecycle

Examples:

Load from dataset registry:

```pycon
>>> client = SandboxClient(
...     url="http://localhost:8000/cds/cds-services/my-service"
... )
>>> client.load_from_registry("mimic-on-fhir", sample_size=10)
>>> responses = client.send_requests()
```

Load CDA file from path:

```pycon
>>> client = SandboxClient(
...     url="http://localhost:8000/notereader/?wsdl",
...     protocol="soap"
... )
>>> client.load_from_path("./data/clinical_note.xml")
>>> responses = client.send_requests()
```

Generate data from free text:

```pycon
>>> client = SandboxClient(
...     url="http://localhost:8000/cds/cds-services/discharge-summarizer"
... )
>>> client.load_free_text(
...     csv_path="./data/notes.csv",
...     column_name="text",
...     workflow="encounter-discharge"
... )
>>> responses = client.send_requests()
```

## `__enter__()`

Context manager entry.

## `__exit__(exc_type, exc_val, exc_tb)`

Context manager exit - auto-save results if responses exist.

Only saves if no exception occurred and responses were generated.

## `__init__(url, workflow, protocol='rest', timeout=10.0)`

Initialize SandboxClient.

| PARAMETER  | DESCRIPTION                                                                                                             |
| ---------- | ----------------------------------------------------------------------------------------------------------------------- |
| `url`      | Full service URL (e.g., "http://localhost:8000/cds/cds-services/my-service") **TYPE:** `str`                            |
| `workflow` | Workflow specification (required) - determines request type and validation **TYPE:** `Union[Workflow, str]`             |
| `protocol` | Communication protocol - "rest" for CDS Hooks, "soap" for CDA **TYPE:** `Literal['rest', 'soap']` **DEFAULT:** `'rest'` |
| `timeout`  | Request timeout in seconds **TYPE:** `float` **DEFAULT:** `10.0`                                                        |

| RAISES       | DESCRIPTION                                        |
| ------------ | -------------------------------------------------- |
| `ValueError` | If url or workflow-protocol combination is invalid |

## `__repr__()`

String representation of SandboxClient.

## `clear_requests()`

Clear all queued requests.

Useful when you want to start fresh without creating a new client instance.

| RETURNS         | DESCRIPTION              |
| --------------- | ------------------------ |
| `SandboxClient` | Self for method chaining |

## `get_request_data(format='dict')`

Get transformed request data for inspection.

Allows access to serialized request data for debugging or custom processing. For direct access to Pydantic models, use the `requests` attribute:

> > > for request in client.requests: print(request.model_dump())

| PARAMETER | DESCRIPTION                                                                                                                       |
| --------- | --------------------------------------------------------------------------------------------------------------------------------- |
| `format`  | Return format - "dict" for list of dictionaries, "json" for JSON string **TYPE:** `Literal['dict', 'json']` **DEFAULT:** `'dict'` |

| RETURNS                  | DESCRIPTION                      |
| ------------------------ | -------------------------------- |
| `Union[List[Dict], str]` | Request data in specified format |

| RAISES       | DESCRIPTION                       |
| ------------ | --------------------------------- |
| `ValueError` | If format is not "dict" or "json" |

Examples:

```pycon
>>> client.load_from_path("data.xml")
>>> # Access raw Pydantic models directly
>>> for request in client.requests:
>>>     print(request.model_dump(exclude_none=True))
>>> # Get as dictionaries
>>> dicts = client.get_request_data("dict")
>>> # Get as JSON string
>>> json_str = client.get_request_data("json")
>>> print(json_str)
```

## `get_status()`

Get current client status and statistics.

| RETURNS          | DESCRIPTION                                     |
| ---------------- | ----------------------------------------------- |
| `Dict[str, Any]` | Dictionary containing client status information |

## `load_free_text(csv_path, column_name, generate_synthetic=True, random_seed=None, **kwargs)`

Load free-text notes from a CSV column and create FHIR DocumentReferences for CDS prefetch. Optionally include synthetic FHIR resources based on the current workflow.

| PARAMETER            | DESCRIPTION                                                                                  |
| -------------------- | -------------------------------------------------------------------------------------------- |
| `csv_path`           | Path to the CSV file **TYPE:** `str`                                                         |
| `column_name`        | Name of the text column **TYPE:** `str`                                                      |
| `generate_synthetic` | Whether to add synthetic FHIR resources (default: True) **TYPE:** `bool` **DEFAULT:** `True` |
| `random_seed`        | Seed for reproducible results **TYPE:** `Optional[int]` **DEFAULT:** `None`                  |
| `**kwargs`           | Extra parameters for data generation **TYPE:** `Any` **DEFAULT:** `{}`                       |

| RETURNS         | DESCRIPTION |
| --------------- | ----------- |
| `SandboxClient` | self        |

| RAISES              | DESCRIPTION                    |
| ------------------- | ------------------------------ |
| `FileNotFoundError` | If the CSV file does not exist |
| `ValueError`        | If the column is not found     |

## `load_from_path(path, pattern=None)`

Load data from a file or directory.

Supports single files or all matching files in a directory (with optional glob pattern). For .xml (SOAP protocol) loads CDA; for .json (REST protocol) loads Prefetch.

| PARAMETER | DESCRIPTION                                                                                         |
| --------- | --------------------------------------------------------------------------------------------------- |
| `path`    | File or directory path. **TYPE:** `Union[str, Path]`                                                |
| `pattern` | Glob pattern for files in directory (e.g., "\*.xml"). **TYPE:** `Optional[str]` **DEFAULT:** `None` |

| RETURNS         | DESCRIPTION |
| --------------- | ----------- |
| `SandboxClient` | Self.       |

| RAISES              | DESCRIPTION                                                |
| ------------------- | ---------------------------------------------------------- |
| `FileNotFoundError` | If path does not exist.                                    |
| `ValueError`        | If no matching files are found or if path is not file/dir. |

## `load_from_registry(source, data_dir, **kwargs)`

Load data from the dataset registry.

Loads pre-configured datasets like MIMIC-on-FHIR, Synthea, or custom registered datasets.

| PARAMETER  | DESCRIPTION                                                                                       |
| ---------- | ------------------------------------------------------------------------------------------------- |
| `source`   | Dataset name (e.g., "mimic-on-fhir", "synthea") **TYPE:** `str`                                   |
| `data_dir` | Path to the dataset directory **TYPE:** `str`                                                     |
| `**kwargs` | Dataset-specific parameters (e.g., resource_types, sample_size) **TYPE:** `Any` **DEFAULT:** `{}` |

| RETURNS         | DESCRIPTION              |
| --------------- | ------------------------ |
| `SandboxClient` | Self for method chaining |

| RAISES              | DESCRIPTION                      |
| ------------------- | -------------------------------- |
| `ValueError`        | If dataset not found in registry |
| `FileNotFoundError` | If data_dir doesn't exist        |

Examples:

Load MIMIC dataset:

```pycon
>>> client = SandboxClient(
...     url="http://localhost:8000/cds/patient-view",
...     workflow="patient-view",
... )
>>> client.load_from_registry(
...     "mimic-on-fhir",
...     data_dir="./data/mimic-fhir",
...     resource_types=["MimicMedication"],
...     sample_size=10
... )
```

## `load_synthetic(n=1, random_seed=None)`

Generate n synthetic CDS requests for the configured workflow.

Useful for quickly testing a service without real patient data. Supports patient-view and encounter-discharge workflows.

| PARAMETER     | DESCRIPTION                                                                                                                             |
| ------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| `n`           | Number of synthetic requests to generate (default: 1) **TYPE:** `int` **DEFAULT:** `1`                                                  |
| `random_seed` | Seed for reproducible results. Each request gets seed + i so they produce different data. **TYPE:** `Optional[int]` **DEFAULT:** `None` |

| RETURNS         | DESCRIPTION              |
| --------------- | ------------------------ |
| `SandboxClient` | Self for method chaining |

| RAISES       | DESCRIPTION                                               |
| ------------ | --------------------------------------------------------- |
| `ValueError` | If the workflow is not supported for synthetic generation |

## `preview_requests(limit=None)`

Get preview of queued requests without sending them.

Provides a summary view of what requests are queued, useful for debugging and verifying data was loaded correctly before sending.

| PARAMETER | DESCRIPTION                                                                                                |
| --------- | ---------------------------------------------------------------------------------------------------------- |
| `limit`   | Maximum number of requests to preview. If None, preview all. **TYPE:** `Optional[int]` **DEFAULT:** `None` |

| RETURNS                | DESCRIPTION                                              |
| ---------------------- | -------------------------------------------------------- |
| `List[Dict[str, Any]]` | List of request summary dictionaries containing metadata |

## `save_results(directory='./output/', save_request=True, save_response=True)`

Save request and/or response data to disk.

| PARAMETER       | DESCRIPTION                                                                                              |
| --------------- | -------------------------------------------------------------------------------------------------------- |
| `directory`     | Directory to save data to (default: "./output/") **TYPE:** `Union[str, Path]` **DEFAULT:** `'./output/'` |
| `save_request`  | Whether to save request data (default: True) **TYPE:** `bool` **DEFAULT:** `True`                        |
| `save_response` | Whether to save response data (default: True) **TYPE:** `bool` **DEFAULT:** `True`                       |

## `send_requests()`

Send all queued requests to the service.

| RETURNS      | DESCRIPTION                   |
| ------------ | ----------------------------- |
| `List[Dict]` | List of response dictionaries |

## `CdsDataGenerator`

Generates synthetic CDS (Clinical Decision Support) data for specified workflows.

Uses registered generators to create FHIR resources (e.g., Patient, Encounter, Condition) according to workflow configuration. Can optionally include free text data from a CSV file as DocumentReference.

| ATTRIBUTE        | DESCRIPTION                                                        |
| ---------------- | ------------------------------------------------------------------ |
| `registry`       | Maps generator names to classes. **TYPE:** `dict`                  |
| `mappings`       | Maps workflows to required generators. **TYPE:** `dict`            |
| `generated_data` | Most recently generated resources. **TYPE:** `Dict[str, Resource]` |
| `workflow`       | Currently active workflow. **TYPE:** `str`                         |

Example

> > > generator = CdsDataGenerator() generator.set_workflow("encounter_discharge") data = generator.generate_prefetch(random_seed=42)

### `fetch_generator(generator_name)`

Return the generator class by name from the registry.

| PARAMETER        | DESCRIPTION                                 |
| ---------------- | ------------------------------------------- |
| `generator_name` | Name of the data generator. **TYPE:** `str` |

| RETURNS    | DESCRIPTION                                                 |
| ---------- | ----------------------------------------------------------- |
| `Callable` | Generator class, or None if not found. **TYPE:** `Callable` |

Example

> > > gen = CdsDataGenerator().fetch_generator("PatientGenerator")

### `free_text_parser(path_to_csv, column_name)`

Read a column of free text from a CSV file.

| PARAMETER     | DESCRIPTION                             |
| ------------- | --------------------------------------- |
| `path_to_csv` | Path to CSV file. **TYPE:** `str`       |
| `column_name` | Column name to extract. **TYPE:** `str` |

| RETURNS     | DESCRIPTION                         |
| ----------- | ----------------------------------- |
| `List[str]` | List\[str\]: Extracted text values. |

| RAISES              | DESCRIPTION                     |
| ------------------- | ------------------------------- |
| `FileNotFoundError` | If CSV file does not exist.     |
| `ValueError`        | If column_name is not provided. |

### `generate_prefetch(constraints=None, free_text_path=None, column_name=None, random_seed=None, generate_resources=True)`

Generate prefetch FHIR resources and/or DocumentReference.

| PARAMETER            | DESCRIPTION                                                                         |
| -------------------- | ----------------------------------------------------------------------------------- |
| `constraints`        | Constraints for resource generation. **TYPE:** `Optional[list]` **DEFAULT:** `None` |
| `free_text_path`     | CSV file containing free text. **TYPE:** `Optional[str]` **DEFAULT:** `None`        |
| `column_name`        | CSV column for free text. **TYPE:** `Optional[str]` **DEFAULT:** `None`             |
| `random_seed`        | Random seed. **TYPE:** `Optional[int]` **DEFAULT:** `None`                          |
| `generate_resources` | If True, generate synthetic FHIR resources. **TYPE:** `bool` **DEFAULT:** `True`    |

| RETURNS               | DESCRIPTION                                                                                                                  |
| --------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| `Dict[str, Resource]` | Dict\[str, Resource\]: Generated resources keyed by resource type (lowercase), plus "document" if a free text entry is used. |

| RAISES              | DESCRIPTION                                               |
| ------------------- | --------------------------------------------------------- |
| `ValueError`        | If workflow is not recognized, or column name is missing. |
| `FileNotFoundError` | If free_text_path does not exist.                         |

### `set_workflow(workflow)`

Set the current workflow name to use for data generation.

| PARAMETER  | DESCRIPTION                    |
| ---------- | ------------------------------ |
| `workflow` | Workflow name. **TYPE:** `str` |

## `CDSRequest`

Bases: `BaseModel`

A model representing the data structure for a CDS service call, triggered by specific hooks within a healthcare application.

| ATTRIBUTE           | DESCRIPTION                                                                                                                |
| ------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| `hook`              | The hook that triggered this CDS Service call. For example, 'patient-view'. **TYPE:** `str`                                |
| `hookInstance`      | A universally unique identifier for this particular hook call. **TYPE:** `UUID`                                            |
| `fhirServer`        | The base URL of the CDS Client's FHIR server. This field is required if fhirAuthorization is provided. **TYPE:** `HttpUrl` |
| `fhirAuthorization` | Optional authorization details providing a bearer access token for FHIR resources. **TYPE:** `Optional[FhirAuthorization]` |
| `context`           | Hook-specific contextual data required by the CDS service. **TYPE:** `Dict[str, Any]`                                      |
| `prefetch`          | Optional FHIR data that was prefetched by the CDS Client. **TYPE:** `Optional[Dict[str, Any]]`                             |

Documentation: https://cds-hooks.org/specification/current/#http-request_1

### `model_dump(**kwargs)`

Model dump method to convert any nested datetime and byte objects to strings for readability. This is also a workaround to this Pydantic V2 issue https://github.com/pydantic/pydantic/issues/9571 For proper JSON serialization, should use model_dump_json() instead when issue is resolved.

## `Action`

Bases: `BaseModel`

Within a suggestion, all actions are logically AND'd together, such that a user selecting a suggestion selects all of the actions within it. When a suggestion contains multiple actions, the actions SHOULD be processed as per FHIR's rules for processing transactions with the CDS Client's fhirServer as the base url for the inferred full URL of the transaction bundle entries.

https://cds-hooks.org/specification/current/#action

## `ActionTypeEnum`

Bases: `str`, `Enum`

The type of action being performed

## `CDSResponse`

Bases: `BaseModel`

Represents the response from a CDS service.

This class models the structure of a CDS Hooks response, which includes cards for displaying information or suggestions to the user, and optional system actions that can be executed automatically.

| ATTRIBUTE       | DESCRIPTION                                                                                                                                                                                       |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `cards`         | A list of Card objects to be displayed to the end user. Default is an empty list. **TYPE:** `List[Card]`                                                                                          |
| `systemActions` | A list of Action objects representing actions that the CDS Client should execute as part of performing the decision support requested. This field is optional. **TYPE:** `Optional[List[Action]]` |

For more information, see: https://cds-hooks.org/specification/current/#cds-service-response

## `Card`

Bases: `BaseModel`

Cards can provide a combination of information (for reading), suggested actions (to be applied if a user selects them), and links (to launch an app if the user selects them). The CDS Client decides how to display cards, but this specification recommends displaying suggestions using buttons, and links using underlined text.

https://cds-hooks.org/specification/current/#card-attributes

## `IndicatorEnum`

Bases: `str`, `Enum`

Urgency/importance of what Card conveys. Allowed values, in order of increasing urgency, are: info, warning, critical. The CDS Client MAY use this field to help make UI display decisions such as sort order or coloring.

## `Link`

Bases: `BaseModel`

- CDS Client support for appContext requires additional coordination with the authorization server that is not described or specified in CDS Hooks nor SMART.
- Autolaunchable is experimental

https://cds-hooks.org/specification/current/#link

## `LinkTypeEnum`

Bases: `str`, `Enum`

The type of the given URL. There are two possible values for this field. A type of absolute indicates that the URL is absolute and should be treated as-is. A type of smart indicates that the URL is a SMART app launch URL and the CDS Client should ensure the SMART app launch URL is populated with the appropriate SMART launch parameters.

## `SelectionBehaviorEnum`

Bases: `str`, `Enum`

Describes the intended selection behavior of the suggestions in the card. Allowed values are: at-most-one, indicating that the user may choose none or at most one of the suggestions; any, indicating that the end user may choose any number of suggestions including none of them and all of them. CDS Clients that do not understand the value MUST treat the card as an error.

## `SimpleCoding`

Bases: `BaseModel`

The Coding data type captures the concept of a code. This coding type is a standalone data type in CDS Hooks modeled after a trimmed down version of the FHIR Coding data type.

## `Source`

Bases: `BaseModel`

Grouping structure for the Source of the information displayed on this card. The source should be the primary source of guidance for the decision support Card represents.

https://cds-hooks.org/specification/current/#source

## `Suggestion`

Bases: `BaseModel`

Allows a service to suggest a set of changes in the context of the current activity (e.g. changing the dose of a medication currently being prescribed, for the order-sign activity). If suggestions are present, selectionBehavior MUST also be provided.

https://cds-hooks.org/specification/current/#suggestion

## `CdaRequest`

Bases: `BaseModel`

### `from_dict(data)`

Loads data from dict (xmltodict format)

### `model_dump(*args, **kwargs)`

Dumps document as dict with xmltodict

### `model_dump_xml(*args, **kwargs)`

Decodes and dumps document as an xml string

## `CdaResponse`

Bases: `BaseModel`

### `from_dict(data)`

Loads data from dict (xmltodict format)

### `model_dump(*args, **kwargs)`

Dumps document as dict with xmltodict

### `model_dump_xml(*args, **kwargs)`

Decodes and dumps document as an xml string
