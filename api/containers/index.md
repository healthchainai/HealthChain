# Containers

## `BaseDocument`

Base container for document data flowing through a pipeline.

Holds the original input in `data` and a text view in `text`. Serialization helpers skip private (`_`-prefixed) attributes so pipeline-internal state (e.g. the spaCy doc) is never emitted.

| ATTRIBUTE | DESCRIPTION                                                                             |
| --------- | --------------------------------------------------------------------------------------- |
| `data`    | The original input supplied (raw text, FHIR Bundle, resource, or list). **TYPE:** `Any` |
| `text`    | Text view of the document, derived from data. **TYPE:** `str`                           |

## `Document`

Bases: `BaseDocument`

Main document container for processing textual and clinical data in HealthChain.

The Document class is the primary structure used throughout annotation and analytics pipelines, accumulating transformations, extractions, and results from each stage. It seamlessly integrates raw text, FHIR resources, clinical decision support (CDS) results, and ML model outputs in one object.

Features

- Accepts text, FHIR Bundles/resources, or lists of FHIR resources as input.
- Stores and manipulates clinical FHIR data via the .fhir property (access to bundles, problem lists, meds, allergies, etc.).
- Encapsulates CDS Hooks-style decision support cards and suggested actions via the .cds property.

| ATTRIBUTE | DESCRIPTION                                                                                    |
| --------- | ---------------------------------------------------------------------------------------------- |
| `fhir`    | FHIR resources and context (problem list, medication, allergy, etc.) **TYPE:** `FhirData`      |
| `cds`     | Clinical decision support (cards and actions) **TYPE:** `CdsAnnotations`                       |
| `text`    | The text content of the document (if available). **TYPE:** `str`                               |
| `data`    | The original input supplied (raw text, Bundle, resource, or list of resources) **TYPE:** `Any` |

Usage example

> > > doc = Document(data="Patient has hypertension") doc.fhir.problem_list = [Condition(...)] doc.cds.cards = [Card(...)]

Inherits from

BaseDocument

### `__len__()`

Return the length of the document's text.

| RETURNS | DESCRIPTION                                            |
| ------- | ------------------------------------------------------ |
| `int`   | Character length of the document text. **TYPE:** `int` |

### `__post_init__()`

Post-initialization setup to process textual or FHIR data.

- If input data is a FHIR Bundle, stores it and extracts OperationOutcome and Provenance resources.
- If input data is a list of FHIR resources, wraps them in a Bundle.
- For text input, sets .text field accordingly.

### `update_problem_list(entities, patient_ref, coding_system='http://snomed.info/sct', code_attribute='cui')`

Populate or update the problem list from a list of linked entities.

Expects entities as plain dicts with a medical code under `code_attribute` (e.g. from entity linking). Entities missing the code are skipped. Existing problem list Conditions are preserved.

| PARAMETER        | DESCRIPTION                                                                                                                                                            |
| ---------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `entities`       | Entities to convert, each a dict with at least "text" and the code under code_attribute (e.g. {"text": "fever", "cui": "386661006"}). **TYPE:** `List[Dict[str, Any]]` |
| `patient_ref`    | FHIR reference to the patient (e.g. "Patient/abc"). **TYPE:** `str`                                                                                                    |
| `coding_system`  | Coding system URI for the conditions (default: SNOMED CT). **TYPE:** `str` **DEFAULT:** `'http://snomed.info/sct'`                                                     |
| `code_attribute` | Dict key containing the medical code (default: "cui"). **TYPE:** `str` **DEFAULT:** `'cui'`                                                                            |

Example

> > > doc.update_problem_list( ... [{"text": ent.text, "cui": ent.\_.cui} for ent in spacy_doc.ents], ... patient_ref="Patient/abc", ... )

## `base`

### `BaseDocument`

Base container for document data flowing through a pipeline.

Holds the original input in `data` and a text view in `text`. Serialization helpers skip private (`_`-prefixed) attributes so pipeline-internal state (e.g. the spaCy doc) is never emitted.

| ATTRIBUTE | DESCRIPTION                                                                             |
| --------- | --------------------------------------------------------------------------------------- |
| `data`    | The original input supplied (raw text, FHIR Bundle, resource, or list). **TYPE:** `Any` |
| `text`    | Text view of the document, derived from data. **TYPE:** `str`                           |

## `document`

### `CdsAnnotations`

Container for Clinical Decision Support (CDS) results.

This class stores and manages outputs from clinical decision support systems, including CDS Hooks cards and suggested clinical actions. The cards contain recommendations, warnings, and other decision support content that can be displayed to clinicians. Actions represent specific clinical tasks or interventions that are suggested based on the analysis.

| ATTRIBUTE  | DESCRIPTION                                                                                                                        |
| ---------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| `_cards`   | CDS Hooks cards containing clinical recommendations, warnings, or other decision support content. **TYPE:** `Optional[List[Card]]` |
| `_actions` | Suggested clinical actions that could be taken based on the CDS analysis. **TYPE:** `Optional[List[Action]]`                       |

Example

> > > cds = CdsAnnotations() cds.cards = [Card(summary="Consider aspirin")] cds.actions = [Action(type="create", description="Order aspirin")]

#### `actions`

Get the current list of suggested clinical actions.

#### `cards`

Get the current list of CDS Hooks cards.

### `Document`

Bases: `BaseDocument`

Main document container for processing textual and clinical data in HealthChain.

The Document class is the primary structure used throughout annotation and analytics pipelines, accumulating transformations, extractions, and results from each stage. It seamlessly integrates raw text, FHIR resources, clinical decision support (CDS) results, and ML model outputs in one object.

Features

- Accepts text, FHIR Bundles/resources, or lists of FHIR resources as input.
- Stores and manipulates clinical FHIR data via the .fhir property (access to bundles, problem lists, meds, allergies, etc.).
- Encapsulates CDS Hooks-style decision support cards and suggested actions via the .cds property.

| ATTRIBUTE | DESCRIPTION                                                                                    |
| --------- | ---------------------------------------------------------------------------------------------- |
| `fhir`    | FHIR resources and context (problem list, medication, allergy, etc.) **TYPE:** `FhirData`      |
| `cds`     | Clinical decision support (cards and actions) **TYPE:** `CdsAnnotations`                       |
| `text`    | The text content of the document (if available). **TYPE:** `str`                               |
| `data`    | The original input supplied (raw text, Bundle, resource, or list of resources) **TYPE:** `Any` |

Usage example

> > > doc = Document(data="Patient has hypertension") doc.fhir.problem_list = [Condition(...)] doc.cds.cards = [Card(...)]

Inherits from

BaseDocument

#### `__len__()`

Return the length of the document's text.

| RETURNS | DESCRIPTION                                            |
| ------- | ------------------------------------------------------ |
| `int`   | Character length of the document text. **TYPE:** `int` |

#### `__post_init__()`

Post-initialization setup to process textual or FHIR data.

- If input data is a FHIR Bundle, stores it and extracts OperationOutcome and Provenance resources.
- If input data is a list of FHIR resources, wraps them in a Bundle.
- For text input, sets .text field accordingly.

#### `update_problem_list(entities, patient_ref, coding_system='http://snomed.info/sct', code_attribute='cui')`

Populate or update the problem list from a list of linked entities.

Expects entities as plain dicts with a medical code under `code_attribute` (e.g. from entity linking). Entities missing the code are skipped. Existing problem list Conditions are preserved.

| PARAMETER        | DESCRIPTION                                                                                                                                                            |
| ---------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `entities`       | Entities to convert, each a dict with at least "text" and the code under code_attribute (e.g. {"text": "fever", "cui": "386661006"}). **TYPE:** `List[Dict[str, Any]]` |
| `patient_ref`    | FHIR reference to the patient (e.g. "Patient/abc"). **TYPE:** `str`                                                                                                    |
| `coding_system`  | Coding system URI for the conditions (default: SNOMED CT). **TYPE:** `str` **DEFAULT:** `'http://snomed.info/sct'`                                                     |
| `code_attribute` | Dict key containing the medical code (default: "cui"). **TYPE:** `str` **DEFAULT:** `'cui'`                                                                            |

Example

> > > doc.update_problem_list( ... [{"text": ent.text, "cui": ent.\_.cui} for ent in spacy_doc.ents], ... patient_ref="Patient/abc", ... )

### `FhirData`

Container for FHIR resource data and its context.

Stores and manages clinical data in FHIR format. Access document references within resources easily through convenience functions.

Also allows you to set common continuity of care lists, such as a problem list, medication list, and allergy list. These collections are accessible as properties of the class instance.

TODO: make problem, meds, allergy lists configurable

Properties

bundle: The FHIR bundle containing resources prefetch_resources: Dictionary of CDS Hooks prefetch resources problem_list: List of Condition resources medication_list: List of MedicationStatement resources allergy_list: List of AllergyIntolerance resources

Example

> > > fhir = FhirData()
> > >
> > > #### Add prefetch resources from CDS request
> > >
> > > fhir.prefetch_resources = {"patient": patient_resource}
> > >
> > > #### Add document to bundle
> > >
> > > doc_id = fhir.add_document_reference(document)
> > >
> > > #### Get document with relationships
> > >
> > > doc_family = fhir.get_document_reference_family(doc_id)
> > >
> > > #### Access clinical lists
> > >
> > > conditions = fhir.problem_list

#### `allergy_list`

Get allergy list from the bundle.

#### `bundle`

Returns the FHIR Bundle if it exists.

#### `medication_list`

Get medication list from the bundle.

#### `operation_outcomes`

Get extracted OperationOutcome resources separated from the bundle.

#### `patient`

Get the first Patient resource from the bundle (convenience accessor).

Returns None if no Patient resources are present in the bundle. For bundles with multiple patients, use the patients property instead.

#### `patients`

Get all Patient resources from the bundle.

Most bundles contain a single patient, but some queries (e.g., family history, population queries) may return multiple patients. This property provides access to all Patient resources without removing them from the bundle.

#### `prefetch_resources`

Returns the prefetch FHIR resources.

#### `problem_list`

Get problem list from the bundle. Problem list items are stored as Condition resources in the bundle. See: https://www.hl7.org/fhir/condition.html

#### `provenances`

Get extracted Provenance resources separated from the bundle.

#### `add_document_reference(document, parent_id=None, relationship_type='transforms')`

Adds a DocumentReference resource to the FHIR bundle and establishes relationships between documents if a parent_id is provided. The relationship is tracked using the FHIR relatesTo element with a specified relationship type. See: https://build.fhir.org/documentreference-definitions.html#DocumentReference.relatesTo

| PARAMETER           | DESCRIPTION                                                                                                                                                                                                                                                     |
| ------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `document`          | The DocumentReference to add to the bundle **TYPE:** `DocumentReference`                                                                                                                                                                                        |
| `parent_id`         | Optional ID of the parent document. If provided, establishes a relationship between this document and its parent. **TYPE:** `Optional[str]` **DEFAULT:** `None`                                                                                                 |
| `relationship_type` | The type of relationship to establish with the parent document. Defaults to "transforms". This is used in the FHIR relatesTo element's code. See: http://hl7.org/fhir/valueset-document-relationship-type **TYPE:** `Optional[str]` **DEFAULT:** `'transforms'` |

| RETURNS | DESCRIPTION                                                                                                |
| ------- | ---------------------------------------------------------------------------------------------------------- |
| `str`   | The ID of the added document. If the document had no ID, a new UUID-based ID is generated. **TYPE:** `str` |

#### `add_resources(resources, resource_type, replace=False)`

Add resources to the working bundle.

#### `get_document_reference_family(document_id)`

Get a DocumentReference resource and all its related resources based on the relatesTo element in the FHIR standard. See: https://build.fhir.org/documentreference-definitions.html#DocumentReference.relatesTo

| PARAMETER     | DESCRIPTION                                                                    |
| ------------- | ------------------------------------------------------------------------------ |
| `document_id` | ID of the DocumentReference resource to find relationships for **TYPE:** `str` |

| RETURNS          | DESCRIPTION                                                                                                                                                                                                                                               |
| ---------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `Dict[str, Any]` | Dict containing: 'document': The requested DocumentReference resource 'parents': List of parent DocumentReference resources 'children': List of child DocumentReference resources 'siblings': List of DocumentReference resources sharing the same parent |

#### `get_document_references_readable(include_data=True, include_relationships=True)`

Get DocumentReferences resources with their content and optional relationship data in a human-readable dictionary format.

| PARAMETER               | DESCRIPTION                                                                                        |
| ----------------------- | -------------------------------------------------------------------------------------------------- |
| `include_data`          | If True, decode and include the document data (default: True) **TYPE:** `bool` **DEFAULT:** `True` |
| `include_relationships` | If True, include related document information (default: True) **TYPE:** `bool` **DEFAULT:** `True` |

| RETURNS                | DESCRIPTION                                                                    |
| ---------------------- | ------------------------------------------------------------------------------ |
| `List[Dict[str, Any]]` | List of documents with metadata and optionally their content and relationships |

#### `get_prefetch_resources(key)`

Get resources of a specific type from the prefetch bundle.

#### `get_resources(resource_type)`

Get resources of a specific type from the working bundle.
