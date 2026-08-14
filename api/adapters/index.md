# Adapters

## `CdaAdapter`

Bases: `BaseAdapter[CdaRequest, CdaResponse]`

CdaAdapter class for handling CDA (Clinical Document Architecture) documents.

This adapter facilitates parsing CDA documents into Document objects and formatting Document objects back into CDA responses. It uses the InteropEngine to convert between CDA and FHIR formats, preserving clinical content while allowing for manipulation of the data within HealthChain pipelines.

| ATTRIBUTE                 | DESCRIPTION                                                                                                             |
| ------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| `engine`                  | The interoperability engine for CDA conversions. If not provided, the default engine is used. **TYPE:** `InteropEngine` |
| `original_cda`            | The original CDA document for use in output. **TYPE:** `str`                                                            |
| `note_document_reference` | Reference to the note document extracted from the CDA. **TYPE:** `DocumentReference`                                    |

| METHOD   | DESCRIPTION                                                       |
| -------- | ----------------------------------------------------------------- |
| `parse`  | Parses a CDA document and extracts clinical data into a Document. |
| `format` | Converts a Document back to CDA format and returns a CdaResponse. |

### `__init__(engine=None)`

Initialize CdaAdapter with optional interop engine.

| PARAMETER | DESCRIPTION                                                                                                                           |
| --------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| `engine`  | Custom interop engine for CDA conversions. If None, creates a default engine. **TYPE:** `Optional[InteropEngine]` **DEFAULT:** `None` |

### `format(document)`

Convert a Document object back to CDA format and return the response.

This method takes a Document object containing FHIR resources (problems, medications, allergies) and converts them back to CDA format using the InteropEngine. It combines all resources from the document's FHIR lists and includes the note document reference if available.

| PARAMETER  | DESCRIPTION                                                                                                          |
| ---------- | -------------------------------------------------------------------------------------------------------------------- |
| `document` | A Document object containing FHIR resources in problem_list, medication_list, and allergy_list. **TYPE:** `Document` |

| RETURNS       | DESCRIPTION                                                                                              |
| ------------- | -------------------------------------------------------------------------------------------------------- |
| `CdaResponse` | A response object containing the CDA document generated from the FHIR resources. **TYPE:** `CdaResponse` |

### `parse(cda_request)`

Parse a CDA document and extract clinical data into a HealthChain Document object.

This method takes a CdaRequest object as input, parses it using the InteropEngine to convert CDA to FHIR resources, and creates a Document object with the extracted data. It creates a DocumentReference for the original CDA XML and extracts clinical data (problems, medications, allergies) into FHIR resources.

| PARAMETER     | DESCRIPTION                                                                       |
| ------------- | --------------------------------------------------------------------------------- |
| `cda_request` | Request object containing the CDA XML document to process. **TYPE:** `CdaRequest` |

| RETURNS    | DESCRIPTION                                                                                                                                                                                                                                                                                                                                                                           |
| ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `Document` | A Document object containing: - The extracted note text as the document data - FHIR resources organized into appropriate lists: - problem_list: List of Condition resources - medication_list: List of MedicationStatement resources - allergy_list: List of AllergyIntolerance resources - DocumentReference resources for the original CDA and extracted notes **TYPE:** `Document` |

Note

If a DocumentReference resource is found in the converted FHIR resources, it is assumed to contain the note text and is stored for later use.

## `CdsFhirAdapter`

Bases: `BaseAdapter[CDSRequest, CDSResponse]`

CdsFhirAdapter class for handling FHIR (Fast Healthcare Interoperability Resources) documents for CDS Hooks.

This adapter facilitates the conversion between CDSRequest objects and Document objects, as well as the creation of CDSResponse objects from processed Documents. Unlike CdaAdapter, this adapter works directly with FHIR data and does not require interop conversion.

| ATTRIBUTE   | DESCRIPTION                                                                            |
| ----------- | -------------------------------------------------------------------------------------- |
| `hook_name` | The name of the CDS Hook being used. **TYPE:** `str`                                   |
| `engine`    | Optional interoperability engine (not used by this adapter). **TYPE:** `Optional[Any]` |

| METHOD   | DESCRIPTION                                           |
| -------- | ----------------------------------------------------- |
| `parse`  | Converts a CDSRequest object into a Document object.  |
| `format` | Converts a Document object into a CDSResponse object. |

### `__init__(hook_name=None, engine=None)`

Initialize CdsFhirAdapter with hook name and optional engine.

| PARAMETER   | DESCRIPTION                                                                                                |
| ----------- | ---------------------------------------------------------------------------------------------------------- |
| `hook_name` | The name of the CDS Hook being used. Defaults to None. **TYPE:** `str` **DEFAULT:** `None`                 |
| `engine`    | Optional interoperability engine (not used by this adapter). **TYPE:** `Optional[Any]` **DEFAULT:** `None` |

### `format(document)`

Convert Document to CDSResponse.

This method takes a Document object containing CDS cards and actions, and converts them into a CDSResponse object that follows the CDS Hooks specification.

| PARAMETER  | DESCRIPTION                                                      |
| ---------- | ---------------------------------------------------------------- |
| `document` | The Document object containing CDS results. **TYPE:** `Document` |

| RETURNS       | DESCRIPTION                                                                                                                                                            |
| ------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `CDSResponse` | A response object containing CDS cards and optional system actions. If no cards are found in the Document, an empty list of cards is returned. **TYPE:** `CDSResponse` |

### `parse(cds_request, prefetch_document_key='document')`

Convert a CDSRequest object into a Document object.

Takes a CDSRequest containing FHIR resources and extracts them into a Document object. The Document will contain all prefetched FHIR resources in its fhir.prefetch_resources. If a DocumentReference resource is provided via prefetch_document_key, its text content will be extracted into Document.data. For multiple attachments, the text content will be concatenated with newlines.

| PARAMETER               | DESCRIPTION                                                                                                                                                                |
| ----------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `cds_request`           | The CDSRequest containing FHIR resources in its prefetch and/or a FHIR server URL. **TYPE:** `CDSRequest`                                                                  |
| `prefetch_document_key` | Key in the prefetch data containing a DocumentReference resource whose text content should be extracted. Defaults to "document". **TYPE:** `str` **DEFAULT:** `'document'` |

| RETURNS    | DESCRIPTION                                                                                                                                                                                                                                                             |
| ---------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `Document` | A Document object containing: - All prefetched FHIR resources in fhir.prefetch_resources - Any text content from the DocumentReference in data (empty string if none found) - For multiple attachments, text content is concatenated with newlines **TYPE:** `Document` |

| RAISES                | DESCRIPTION                                                     |
| --------------------- | --------------------------------------------------------------- |
| `ValueError`          | If neither prefetch nor fhirServer is provided in cds_request   |
| `NotImplementedError` | If fhirServer is provided (FHIR server support not implemented) |
