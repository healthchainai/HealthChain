# FHIR Helpers

FHIR utilities for HealthChain.

## `CodedEntry`

Bases: `BaseModel`

Flattened coded identity of a clinical resource.

JSON-serializable via `model_dump()` so it can be returned directly from agent tools. `code`/`display`/`system` come from the first coding; `codings` carries all of them.

## `EntryCoding`

Bases: `BaseModel`

A single coding (code/display/system) from a CodeableConcept.

## `FHIRValidationError`

Bases: `Exception`

Raised when FHIR validation fails. Carries the full ValidationReport.

## `FHIRVersion`

Bases: `str`, `Enum`

Supported FHIR versions.

R5 is the default version in fhir.resources library. R4B and STU3 are available via subpackages (e.g., fhir.resources.R4B).

## `ValidationIssue`

Bases: `BaseModel`

A single validation issue, mirroring FHIR OperationOutcome.issue fields.

https://www.hl7.org/fhir/operationoutcome.html

## `ValidationReport`

Bases: `BaseModel`

Result of validating a FHIR resource.

JSON-serializable via `model_dump()` so it can be returned directly from agent tools. Convert to a FHIR OperationOutcome resource with `to_operation_outcome()`.

### `to_operation_outcome()`

Convert the report to a FHIR OperationOutcome resource.

| RETURNS    | DESCRIPTION                                                        |
| ---------- | ------------------------------------------------------------------ |
| `Resource` | An OperationOutcome of the report's FHIR version, with one issue   |
| `Resource` | per validation issue (or a single 'informational' issue if valid). |

## `add_coding_to_codeable_concept(codeable_concept, code, system, display=None)`

Add a coding to an existing CodeableConcept.

Useful for adding standardized codes (e.g., SNOMED CT) to resources that already have codes from other systems (e.g., ICD-10).

| PARAMETER          | DESCRIPTION                                                                      |
| ------------------ | -------------------------------------------------------------------------------- |
| `codeable_concept` | The CodeableConcept to add coding to **TYPE:** `CodeableConcept`                 |
| `code`             | The code value from the code system **TYPE:** `str`                              |
| `system`           | The code system URI **TYPE:** `str`                                              |
| `display`          | Optional display text for the code **TYPE:** `Optional[str]` **DEFAULT:** `None` |

| RETURNS           | DESCRIPTION                                                                       |
| ----------------- | --------------------------------------------------------------------------------- |
| `CodeableConcept` | The updated CodeableConcept with the new coding added **TYPE:** `CodeableConcept` |

Example

> > > ### Add SNOMED CT code to a condition that has ICD-10
> > >
> > > condition_code = condition.code condition_code = add_coding_to_codeable_concept( ... condition_code, ... code="44054006", ... system="http://snomed.info/sct", ... display="Type 2 diabetes mellitus" ... )

## `add_provenance_metadata(resource, source, tag_code=None, tag_display=None)`

Add provenance metadata to a FHIR resource.

Adds source system identifier, timestamp, and optional processing tags to track data lineage and transformations for audit trails.

| PARAMETER     | DESCRIPTION                                                                                                                    |
| ------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| `resource`    | The FHIR resource to annotate **TYPE:** `Any`                                                                                  |
| `source`      | Name of the source system (e.g., "epic", "cerner") **TYPE:** `str`                                                             |
| `tag_code`    | Optional tag code for processing operations (e.g., "aggregated", "deduplicated") **TYPE:** `Optional[str]` **DEFAULT:** `None` |
| `tag_display` | Optional display text for the tag **TYPE:** `Optional[str]` **DEFAULT:** `None`                                                |

| RETURNS    | DESCRIPTION                                                 |
| ---------- | ----------------------------------------------------------- |
| `Resource` | The resource with added provenance metadata **TYPE:** `Any` |

Example

> > > condition = create_condition(subject="Patient/123", code="E11.9") condition = add_provenance_metadata(condition, "epic", "aggregated", "Aggregated from source")

## `add_resource(bundle, resource, full_url=None)`

Add a resource to a bundle.

| PARAMETER  | DESCRIPTION                                                                                       |
| ---------- | ------------------------------------------------------------------------------------------------- |
| `bundle`   | The bundle to add to **TYPE:** `Bundle`                                                           |
| `resource` | The resource to add, e.g. Condition, MedicationStatement, AllergyIntolerance **TYPE:** `Resource` |
| `full_url` | Optional full URL for the resource **TYPE:** `Optional[str]` **DEFAULT:** `None`                  |

## `calculate_age_from_birthdate(birth_date)`

Calculate age in years from a birth date string.

| PARAMETER    | DESCRIPTION                                                                |
| ------------ | -------------------------------------------------------------------------- |
| `birth_date` | Birth date in ISO format (YYYY-MM-DD or full ISO datetime) **TYPE:** `str` |

| RETURNS         | DESCRIPTION                                    |
| --------------- | ---------------------------------------------- |
| `Optional[int]` | Age in years, or None if birth date is invalid |

## `calculate_age_from_event_date(birth_date, event_date)`

Calculate age in years from birth date and event date (MIMIC-IV style).

Uses the formula: age = year(eventDate) - year(birthDate) This matches MIMIC-IV on FHIR de-identified age calculation.

| PARAMETER    | DESCRIPTION                                                                |
| ------------ | -------------------------------------------------------------------------- |
| `birth_date` | Birth date in ISO format (YYYY-MM-DD or full ISO datetime) **TYPE:** `str` |
| `event_date` | Event date in ISO format (YYYY-MM-DD or full ISO datetime) **TYPE:** `str` |

| RETURNS         | DESCRIPTION                                                         |
| --------------- | ------------------------------------------------------------------- |
| `Optional[int]` | Age in years based on year difference, or None if dates are invalid |

Example

> > > calculate_age_from_event_date("1990-06-15", "2020-03-10") 30

## `convert_prefetch_to_fhir_objects(prefetch_dict)`

Convert a dictionary of FHIR resource dicts to FHIR Resource objects.

Takes a prefetch dictionary where values may be either dict representations of FHIR resources or already instantiated FHIR Resource objects, and ensures all values are FHIR Resource objects.

| PARAMETER       | DESCRIPTION                                                                          |
| --------------- | ------------------------------------------------------------------------------------ |
| `prefetch_dict` | Dictionary mapping keys to FHIR resource dicts or objects **TYPE:** `Dict[str, Any]` |

| RETURNS               | DESCRIPTION                                                                              |
| --------------------- | ---------------------------------------------------------------------------------------- |
| `Dict[str, Resource]` | Dict\[str, Resource\]: Dictionary with same keys but all values as FHIR Resource objects |

Example

> > > prefetch = { ... "patient": {"resourceType": "Patient", "id": "123"}, ... "condition": Condition(id="456", ...) ... } fhir_objects = convert_prefetch_to_fhir_objects(prefetch) isinstance(fhir_objects["patient"], Patient) # True isinstance(fhir_objects["condition"], Condition) # True

## `convert_resource(resource, target_version)`

Convert a FHIR resource to a different version.

Converts by serializing the resource to a dictionary and deserializing with the target version's resource class. This approach works for resources with compatible field structures.

Note

Field mappings between FHIR versions may not be 1:1. Some fields may be added, removed, or renamed between versions. This function performs a best-effort conversion and may raise validation errors if the resource data is incompatible with the target version.

| PARAMETER        | DESCRIPTION                                                 |
| ---------------- | ----------------------------------------------------------- |
| `resource`       | The FHIR resource to convert **TYPE:** `Any`                |
| `target_version` | The target FHIR version **TYPE:** `Union[FHIRVersion, str]` |

| RETURNS | DESCRIPTION                                   |
| ------- | --------------------------------------------- |
| `Any`   | A new resource instance of the target version |

| RAISES            | DESCRIPTION                                              |
| ----------------- | -------------------------------------------------------- |
| `ValueError`      | If the resource type cannot be determined or imported    |
| `ValidationError` | If the resource data is incompatible with target version |

Example

> > > from fhir.resources.patient import Patient patient_r5 = Patient(id="123", gender="male") patient_r4b = convert_resource(patient_r5, "R4B") print(patient_r4b.**class**.**module**) fhir.resources.R4B.patient

## `count_resources(bundle)`

Count resources by type in a bundle.

| PARAMETER | DESCRIPTION                                   |
| --------- | --------------------------------------------- |
| `bundle`  | The FHIR Bundle to analyze **TYPE:** `Bundle` |

| RETURNS          | DESCRIPTION                                                                         |
| ---------------- | ----------------------------------------------------------------------------------- |
| `dict[str, int]` | Dictionary mapping resource type names to their counts.                             |
| `Example`        | {"Condition": 2, "MedicationStatement": 1, "Patient": 1} **TYPE:** `dict[str, int]` |

Example

> > > bundle = create_bundle() add_resource(bundle, create_condition(...)) add_resource(bundle, create_condition(...)) add_resource(bundle, create_medication_statement(...)) counts = count_resources(bundle) print(counts)

## `create_allergy_intolerance(patient, code=None, display=None, system='http://snomed.info/sct', *, generate_id=True, warn=True)`

Create a minimal active FHIR AllergyIntolerance. If you need to create a more complex allergy intolerance, use the FHIR AllergyIntolerance resource directly. https://build.fhir.org/allergyintolerance.html

| PARAMETER     | DESCRIPTION                                                                                                                               |
| ------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| `patient`     | REQUIRED. Reference to the patient (e.g. "Patient/123") **TYPE:** `str`                                                                   |
| `code`        | The allergen code **TYPE:** `Optional[str]` **DEFAULT:** `None`                                                                           |
| `display`     | The display name for the allergen **TYPE:** `Optional[str]` **DEFAULT:** `None`                                                           |
| `system`      | The code system (default: SNOMED CT) **TYPE:** `Optional[str]` **DEFAULT:** `'http://snomed.info/sct'`                                    |
| `generate_id` | Stamp an auto-generated 'hc-' id. Pass False for deterministic output (snapshot tests, evals) **TYPE:** `bool` **DEFAULT:** `True`        |
| `warn`        | Log a warning for spec-invalid codes. Pass False if you validate explicitly with validate_resource() **TYPE:** `bool` **DEFAULT:** `True` |

| RETURNS              | DESCRIPTION                                                                                                     |
| -------------------- | --------------------------------------------------------------------------------------------------------------- |
| `AllergyIntolerance` | A FHIR AllergyIntolerance resource with an auto-generated ID prefixed with 'hc-' **TYPE:** `AllergyIntolerance` |

## `create_bundle(bundle_type='collection')`

Create an empty FHIR Bundle. https://www.hl7.org/fhir/bundle.html

| PARAMETER     | DESCRIPTION                                                                                                                                                                                                   |
| ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `bundle_type` | The type of bundle (default: collection) Valid types: document, message, transaction, transaction-response, batch, batch-response, history, searchset, collection **TYPE:** `str` **DEFAULT:** `'collection'` |

## `create_condition(subject, clinical_status='active', code=None, display=None, system='http://snomed.info/sct', onset=None, *, generate_id=True, warn=True)`

Create a minimal active FHIR Condition. If you need to create a more complex condition, use the FHIR Condition resource directly. https://build.fhir.org/condition.html

| PARAMETER         | DESCRIPTION                                                                                                                                                                     |
| ----------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `subject`         | REQUIRED. Reference to the patient (e.g. "Patient/123") **TYPE:** `str`                                                                                                         |
| `clinical_status` | REQUIRED. Clinical status (default: active) **TYPE:** `str` **DEFAULT:** `'active'`                                                                                             |
| `code`            | The condition code **TYPE:** `Optional[str]` **DEFAULT:** `None`                                                                                                                |
| `display`         | The display name for the condition **TYPE:** `Optional[str]` **DEFAULT:** `None`                                                                                                |
| `system`          | The code system (default: SNOMED CT) **TYPE:** `Optional[str]` **DEFAULT:** `'http://snomed.info/sct'`                                                                          |
| `onset`           | When the condition began, as an ISO 8601 date/datetime string, set as onsetDateTime (e.g. "2024-01-15" or "2024-01-15T09:00:00Z") **TYPE:** `Optional[str]` **DEFAULT:** `None` |
| `generate_id`     | Stamp an auto-generated 'hc-' id. Pass False for deterministic output (snapshot tests, evals) **TYPE:** `bool` **DEFAULT:** `True`                                              |
| `warn`            | Log a warning for spec-invalid codes. Pass False if you validate explicitly with validate_resource() **TYPE:** `bool` **DEFAULT:** `True`                                       |

| RETURNS     | DESCRIPTION                                                                                   |
| ----------- | --------------------------------------------------------------------------------------------- |
| `Condition` | A FHIR Condition resource with an auto-generated ID prefixed with 'hc-' **TYPE:** `Condition` |

## `create_document_reference(data=None, url=None, content_type=None, status='current', description='DocumentReference created by HealthChain', attachment_title='Attachment created by HealthChain', *, generate_id=True, warn=True)`

Create a minimal FHIR DocumentReference. If you need to create a more complex document reference, use the FHIR DocumentReference resource directly. https://build.fhir.org/documentreference.html

| PARAMETER          | DESCRIPTION                                                                                                                               |
| ------------------ | ----------------------------------------------------------------------------------------------------------------------------------------- |
| `data`             | The data content of the document attachment **TYPE:** `Optional[Any]` **DEFAULT:** `None`                                                 |
| `url`              | URL where the document can be accessed **TYPE:** `Optional[str]` **DEFAULT:** `None`                                                      |
| `content_type`     | MIME type of the document (e.g. "application/pdf", "text/xml", "image/png") **TYPE:** `Optional[str]` **DEFAULT:** `None`                 |
| `status`           | REQUIRED. Status of the document reference (default: current) **TYPE:** `str` **DEFAULT:** `'current'`                                    |
| `description`      | Description of the document reference **TYPE:** `Optional[str]` **DEFAULT:** `'DocumentReference created by HealthChain'`                 |
| `attachment_title` | Title for the document attachment **TYPE:** `Optional[str]` **DEFAULT:** `'Attachment created by HealthChain'`                            |
| `generate_id`      | Stamp an auto-generated 'hc-' id. Pass False for deterministic output (snapshot tests, evals) **TYPE:** `bool` **DEFAULT:** `True`        |
| `warn`             | Log a warning for spec-invalid codes. Pass False if you validate explicitly with validate_resource() **TYPE:** `bool` **DEFAULT:** `True` |

| RETURNS             | DESCRIPTION                                                                                                   |
| ------------------- | ------------------------------------------------------------------------------------------------------------- |
| `DocumentReference` | A FHIR DocumentReference resource with an auto-generated ID prefixed with 'hc-' **TYPE:** `DocumentReference` |

## `create_document_reference_content(attachment_data=None, url=None, content_type='text/plain', language='en-US', title=None, **kwargs)`

Create a FHIR DocumentReferenceContent object.

Creates a DocumentReferenceContent structure that can be added to a DocumentReference. Either attachment_data or url must be provided. If attachment_data is provided, it will be base64 encoded automatically.

| PARAMETER         | DESCRIPTION                                                                                                                      |
| ----------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| `attachment_data` | The content data (text that will be base64 encoded) **TYPE:** `Optional[str]` **DEFAULT:** `None`                                |
| `url`             | URL where the content can be accessed **TYPE:** `Optional[str]` **DEFAULT:** `None`                                              |
| `content_type`    | MIME type (e.g., 'text/plain', 'text/html', 'application/pdf') (default: text/plain) **TYPE:** `str` **DEFAULT:** `'text/plain'` |
| `language`        | Language code (default: en-US) **TYPE:** `Optional[str]` **DEFAULT:** `'en-US'`                                                  |
| `title`           | Optional title for the content (default: "Attachment created by HealthChain") **TYPE:** `Optional[str]` **DEFAULT:** `None`      |
| `**kwargs`        | Additional DocumentReferenceContent fields (e.g., format, profile) **DEFAULT:** `{}`                                             |

| RETURNS          | DESCRIPTION                                                                                        |
| ---------------- | -------------------------------------------------------------------------------------------------- |
| `Dict[str, Any]` | Dict\[str, Any\]: A FHIR DocumentReferenceContent dictionary with attachment and optional language |

Example

> > > ### Create content with inline data
> > >
> > > content = create_document_reference_content( ... attachment_data="Patient presents with fever...", ... content_type="text/plain", ... title="Clinical Note" ... )
> > >
> > > ### Create content with URL reference
> > >
> > > content = create_document_reference_content( ... url="https://example.com/document.pdf", ... content_type="application/pdf", ... title="Lab Report" ... )
> > >
> > > ### Add content to a DocumentReference
> > >
> > > doc_ref = DocumentReference( ... id="doc-1", ... status="current", ... content=[content] ... )

## `create_dosage(text=None, route_code=None, route_display=None, route_system='http://snomed.info/sct', dose_value=None, dose_unit=None, frequency=None, period=None, period_unit=None, as_needed=None)`

Create a minimal FHIR Dosage element.

Builds a minimum viable Dosage suitable for attaching to a MedicationStatement or MedicationRequest. Only the fields you provide are populated. For anything more complex, construct the FHIR Dosage directly. https://build.fhir.org/dosage.html

| PARAMETER       | DESCRIPTION                                                                                                          |
| --------------- | -------------------------------------------------------------------------------------------------------------------- |
| `text`          | Free-text dosage instructions (e.g. "1 tablet twice daily") **TYPE:** `Optional[str]` **DEFAULT:** `None`            |
| `route_code`    | The route of administration code (e.g. SNOMED CT code for "oral") **TYPE:** `Optional[str]` **DEFAULT:** `None`      |
| `route_display` | The display name for the route code **TYPE:** `Optional[str]` **DEFAULT:** `None`                                    |
| `route_system`  | The code system for the route (default: SNOMED CT) **TYPE:** `Optional[str]` **DEFAULT:** `'http://snomed.info/sct'` |
| `dose_value`    | The numeric dose amount, set as doseAndRate.doseQuantity.value **TYPE:** `Optional[float]` **DEFAULT:** `None`       |
| `dose_unit`     | The unit for the dose amount (e.g. "mg", "tablet") **TYPE:** `Optional[str]` **DEFAULT:** `None`                     |
| `frequency`     | How many times per period the dose is taken (Timing.repeat.frequency) **TYPE:** `Optional[int]` **DEFAULT:** `None`  |
| `period`        | The length of the period (Timing.repeat.period) **TYPE:** `Optional[float]` **DEFAULT:** `None`                      |
| `period_unit`   | The unit of the period (e.g. "d" for day, "h" for hour) **TYPE:** `Optional[str]` **DEFAULT:** `None`                |
| `as_needed`     | Whether the medication is taken as needed (asNeededBoolean) **TYPE:** `Optional[bool]` **DEFAULT:** `None`           |

| RETURNS  | DESCRIPTION                                                                 |
| -------- | --------------------------------------------------------------------------- |
| `Dosage` | A FHIR Dosage element populated with the provided fields **TYPE:** `Dosage` |

## `create_medication_statement(subject, status='unknown', code=None, display=None, system='http://snomed.info/sct', dosage=None, *, generate_id=True, warn=True)`

Create a minimal FHIR MedicationStatement. If you need to create a more complex medication statement, use the FHIR MedicationStatement resource directly. https://build.fhir.org/medicationstatement.html

| PARAMETER     | DESCRIPTION                                                                                                                                                                                                                                                             |
| ------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `subject`     | REQUIRED. Reference to the patient (e.g. "Patient/123") **TYPE:** `str`                                                                                                                                                                                                 |
| `status`      | REQUIRED. Status of the medication. Default "unknown" (an R4B-valid code that makes no clinical assertion). Allowed R4B values: active, completed, entered-in-error, intended, stopped, on-hold, unknown, not-taken **TYPE:** `Optional[str]` **DEFAULT:** `'unknown'`  |
| `code`        | The medication code **TYPE:** `Optional[str]` **DEFAULT:** `None`                                                                                                                                                                                                       |
| `display`     | The display name for the medication **TYPE:** `Optional[str]` **DEFAULT:** `None`                                                                                                                                                                                       |
| `system`      | The code system (default: SNOMED CT) **TYPE:** `Optional[str]` **DEFAULT:** `'http://snomed.info/sct'`                                                                                                                                                                  |
| `dosage`      | Dosage instructions. A plain string is wrapped as a single free-text Dosage; a single Dosage is wrapped in a one-element list; a list of Dosage elements is used as-is. See create_dosage(). **TYPE:** `Optional[Union[str, Dosage, List[Dosage]]]` **DEFAULT:** `None` |
| `generate_id` | Stamp an auto-generated 'hc-' id. Pass False for deterministic output (snapshot tests, evals) **TYPE:** `bool` **DEFAULT:** `True`                                                                                                                                      |
| `warn`        | Log a warning for spec-invalid codes. Pass False if you validate explicitly with validate_resource() **TYPE:** `bool` **DEFAULT:** `True`                                                                                                                               |

| RETURNS               | DESCRIPTION                                                                                                       |
| --------------------- | ----------------------------------------------------------------------------------------------------------------- |
| `MedicationStatement` | A FHIR MedicationStatement resource with an auto-generated ID prefixed with 'hc-' **TYPE:** `MedicationStatement` |

## `create_patient(gender=None, birth_date=None, identifier=None, identifier_system='http://hospital.example.org', *, generate_id=True, warn=True)`

Create a minimal FHIR Patient resource with basic gender and birthdate If you need to create a more complex patient, use the FHIR Patient resource directly https://hl7.org/fhir/patient.html (No required fields).

| PARAMETER           | DESCRIPTION                                                                                                                                   |
| ------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| `gender`            | Administrative gender (male, female, other, unknown) **TYPE:** `Optional[str]` **DEFAULT:** `None`                                            |
| `birth_date`        | Birth date in YYYY-MM-DD format **TYPE:** `Optional[str]` **DEFAULT:** `None`                                                                 |
| `identifier`        | Optional identifier value for the patient (e.g., MRN) **TYPE:** `Optional[str]` **DEFAULT:** `None`                                           |
| `identifier_system` | The system for the identifier (default: "http://hospital.example.org") **TYPE:** `Optional[str]` **DEFAULT:** `'http://hospital.example.org'` |
| `generate_id`       | Stamp an auto-generated 'hc-' id. Pass False for deterministic output (snapshot tests, evals) **TYPE:** `bool` **DEFAULT:** `True`            |
| `warn`              | Log a warning for spec-invalid codes. Pass False if you validate explicitly with validate_resource() **TYPE:** `bool` **DEFAULT:** `True`     |

| RETURNS   | DESCRIPTION                                                                               |
| --------- | ----------------------------------------------------------------------------------------- |
| `Patient` | A FHIR Patient resource with an auto-generated ID prefixed with 'hc-' **TYPE:** `Patient` |

## `create_resource_from_dict(resource_dict, resource_type, raise_on_error=False)`

Create a FHIR resource instance from a dictionary

| PARAMETER        | DESCRIPTION                                                                                                                                |
| ---------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| `resource_dict`  | Dictionary representation of the resource **TYPE:** `Dict`                                                                                 |
| `resource_type`  | Type of FHIR resource to create **TYPE:** `str`                                                                                            |
| `raise_on_error` | If True, raise FHIRValidationError with a full ValidationReport instead of returning None on failure **TYPE:** `bool` **DEFAULT:** `False` |

| RETURNS              | DESCRIPTION                                                             |
| -------------------- | ----------------------------------------------------------------------- |
| `Optional[Resource]` | Optional\[Resource\]: FHIR resource instance or None if creation failed |

| RAISES                | DESCRIPTION                                    |
| --------------------- | ---------------------------------------------- |
| `FHIRValidationError` | If raise_on_error is True and validation fails |

## `create_risk_assessment_from_prediction(subject, prediction, status='final', method=None, basis=None, comment=None, occurrence_datetime=None, *, generate_id=True, warn=True)`

Create a FHIR RiskAssessment from ML model prediction output. If you need to create a more complex risk assessment, use the FHIR RiskAssessment resource directly. https://hl7.org/fhir/riskassessment.html

| PARAMETER             | DESCRIPTION                                                                                                                                                                                                                                                                                                                            |
| --------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `subject`             | REQUIRED. Reference to the patient (e.g. "Patient/123") **TYPE:** `str`                                                                                                                                                                                                                                                                |
| `prediction`          | Dictionary containing prediction details with keys: - outcome: CodeableConcept or dict with code, display, system for the predicted outcome - probability: float between 0 and 1 representing the risk probability - qualitative_risk: Optional str indicating risk level (e.g., "high", "moderate", "low") **TYPE:** `Dict[str, Any]` |
| `status`              | REQUIRED. The status of the assessment (default: "final") **TYPE:** `str` **DEFAULT:** `'final'`                                                                                                                                                                                                                                       |
| `method`              | Optional CodeableConcept describing the assessment method/model used **TYPE:** `Optional[CodeableConcept]` **DEFAULT:** `None`                                                                                                                                                                                                         |
| `basis`               | Optional list of References to observations or other resources used as input **TYPE:** `Optional[List[Reference]]` **DEFAULT:** `None`                                                                                                                                                                                                 |
| `comment`             | Optional text comment about the assessment **TYPE:** `Optional[str]` **DEFAULT:** `None`                                                                                                                                                                                                                                               |
| `occurrence_datetime` | When the assessment was made (ISO format). Omitted when not provided — the helper never invents a timestamp **TYPE:** `Optional[str]` **DEFAULT:** `None`                                                                                                                                                                              |
| `generate_id`         | Stamp an auto-generated 'hc-' id. Pass False for deterministic output (snapshot tests, evals) **TYPE:** `bool` **DEFAULT:** `True`                                                                                                                                                                                                     |
| `warn`                | Log a warning for spec-invalid codes. Pass False if you validate explicitly with validate_resource() **TYPE:** `bool` **DEFAULT:** `True`                                                                                                                                                                                              |

| RETURNS          | DESCRIPTION                                                                                             |
| ---------------- | ------------------------------------------------------------------------------------------------------- |
| `RiskAssessment` | A FHIR RiskAssessment resource with an auto-generated ID prefixed with 'hc-' **TYPE:** `RiskAssessment` |

Example

> > > prediction = { ... "outcome": {"code": "A41.9", "display": "Sepsis", "system": "http://hl7.org/fhir/sid/icd-10"}, ... "probability": 0.85, ... "qualitative_risk": "high" ... } risk = create_risk_assessment("Patient/123", prediction)

## `create_single_attachment(content_type=None, data=None, url=None, title='Attachment created by HealthChain')`

Create a minimal FHIR Attachment.

Creates a FHIR Attachment resource with basic fields. Either data or url should be provided. If data is provided, it will be base64 encoded.

| PARAMETER      | DESCRIPTION                                                                                                                                            |
| -------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `content_type` | The MIME type of the content **TYPE:** `Optional[str]` **DEFAULT:** `None`                                                                             |
| `data`         | The actual data content to be base64 encoded **TYPE:** `Optional[str]` **DEFAULT:** `None`                                                             |
| `url`          | The URL where the data can be found **TYPE:** `Optional[str]` **DEFAULT:** `None`                                                                      |
| `title`        | A title for the attachment (default: "Attachment created by HealthChain") **TYPE:** `Optional[str]` **DEFAULT:** `'Attachment created by HealthChain'` |

| RETURNS      | DESCRIPTION                                                                |
| ------------ | -------------------------------------------------------------------------- |
| `Attachment` | A FHIR Attachment resource with basic metadata and content **TYPE:** `Any` |

## `create_single_codeable_concept(code, display=None, system='http://snomed.info/sct')`

Create a minimal FHIR CodeableConcept with a single coding.

| PARAMETER | DESCRIPTION                                                                                            |
| --------- | ------------------------------------------------------------------------------------------------------ |
| `code`    | REQUIRED. The code value from the code system **TYPE:** `str`                                          |
| `display` | The display name for the code **TYPE:** `Optional[str]` **DEFAULT:** `None`                            |
| `system`  | The code system (default: SNOMED CT) **TYPE:** `Optional[str]` **DEFAULT:** `'http://snomed.info/sct'` |

| RETURNS           | DESCRIPTION                                                          |
| ----------------- | -------------------------------------------------------------------- |
| `CodeableConcept` | A FHIR CodeableConcept resource with a single coding **TYPE:** `Any` |

## `create_single_reaction(code, display=None, system='http://snomed.info/sct', severity=None)`

Create a minimal FHIR Reaction with a single coding.

Creates a FHIR Reaction object with a single manifestation coding. The manifestation describes the clinical reaction that was observed. The severity indicates how severe the reaction was.

| PARAMETER  | DESCRIPTION                                                                                                                       |
| ---------- | --------------------------------------------------------------------------------------------------------------------------------- |
| `code`     | REQUIRED. The code value from the code system representing the reaction manifestation **TYPE:** `str`                             |
| `display`  | The display name for the manifestation code **TYPE:** `Optional[str]` **DEFAULT:** `None`                                         |
| `system`   | The code system for the manifestation code (default: SNOMED CT) **TYPE:** `Optional[str]` **DEFAULT:** `'http://snomed.info/sct'` |
| `severity` | The severity of the reaction (mild, moderate, severe) **TYPE:** `Optional[str]` **DEFAULT:** `None`                               |

| RETURNS                | DESCRIPTION                                                                                |
| ---------------------- | ------------------------------------------------------------------------------------------ |
| `List[Dict[str, Any]]` | A list containing a single FHIR Reaction dictionary with manifestation and severity fields |

## `create_value_quantity_observation(code, value, unit, status='final', subject=None, system='http://loinc.org', display=None, effective_datetime=None, *, generate_id=True, warn=True)`

Create a minimal FHIR Observation for vital signs or laboratory values. If you need to create a more complex observation, use the FHIR Observation resource directly. https://hl7.org/fhir/observation.html

| PARAMETER            | DESCRIPTION                                                                                                                                                                                                      |
| -------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `status`             | REQUIRED. The status of the observation (default: "final") **TYPE:** `str` **DEFAULT:** `'final'`                                                                                                                |
| `code`               | REQUIRED. The observation code (e.g., LOINC code for the measurement) **TYPE:** `str`                                                                                                                            |
| `value`              | The numeric value of the observation **TYPE:** `float`                                                                                                                                                           |
| `unit`               | The unit of measure (e.g., "beats/min", "mg/dL") **TYPE:** `str`                                                                                                                                                 |
| `system`             | The code system for the observation code (default: LOINC) **TYPE:** `str` **DEFAULT:** `'http://loinc.org'`                                                                                                      |
| `display`            | The display name for the observation code **TYPE:** `Optional[str]` **DEFAULT:** `None`                                                                                                                          |
| `effective_datetime` | When the observation was made (ISO format). Omitted when not provided — the helper never invents a timestamp, so only record a time the caller can actually assert **TYPE:** `Optional[str]` **DEFAULT:** `None` |
| `subject`            | Reference to the patient (e.g. "Patient/123") **TYPE:** `Optional[str]` **DEFAULT:** `None`                                                                                                                      |
| `generate_id`        | Stamp an auto-generated 'hc-' id. Pass False for deterministic output (snapshot tests, evals) **TYPE:** `bool` **DEFAULT:** `True`                                                                               |
| `warn`               | Log a warning for spec-invalid codes. Pass False if you validate explicitly with validate_resource() **TYPE:** `bool` **DEFAULT:** `True`                                                                        |

| RETURNS       | DESCRIPTION                                                                                       |
| ------------- | ------------------------------------------------------------------------------------------------- |
| `Observation` | A FHIR Observation resource with an auto-generated ID prefixed with 'hc-' **TYPE:** `Observation` |

## `encode_gender(gender)`

Encode gender as integer for ML models.

Standard encoding: Male=1, Female=0, Other/Unknown=None

| PARAMETER | DESCRIPTION                                      |
| --------- | ------------------------------------------------ |
| `gender`  | Gender string (case-insensitive) **TYPE:** `str` |

| RETURNS         | DESCRIPTION                                                       |
| --------------- | ----------------------------------------------------------------- |
| `Optional[int]` | Encoded gender (1 for male, 0 for female, None for other/unknown) |

## `extract_resources(bundle, resource_type)`

Remove resources of a given type from a bundle and return them.

Useful for extracting and separating specific resource types (e.g., OperationOutcome) from a FHIR Bundle, modifying the bundle in place.

| PARAMETER       | DESCRIPTION                                                                                                                             |
| --------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| `bundle`        | The FHIR Bundle to process (modified in place) **TYPE:** `Bundle`                                                                       |
| `resource_type` | The FHIR resource class or string name to extract (e.g., OperationOutcome or "OperationOutcome") **TYPE:** `Union[str, Type[Resource]]` |

| RETURNS          | DESCRIPTION                                                                   |
| ---------------- | ----------------------------------------------------------------------------- |
| `List[Resource]` | List\[Resource\]: All resources of the specified type that were in the bundle |

## `fhir_version_context(version)`

Context manager for temporarily changing the default FHIR version.

| PARAMETER | DESCRIPTION                                                                    |
| --------- | ------------------------------------------------------------------------------ |
| `version` | The FHIR version to use within the context **TYPE:** `Union[FHIRVersion, str]` |

| YIELDS        | DESCRIPTION                         |
| ------------- | ----------------------------------- |
| `FHIRVersion` | The resolved FHIRVersion being used |

Example

> > > with fhir_version_context("R4B") as v: ... patient = get_fhir_resource("Patient") # R4B Patient ... print(f"Using {v}")
> > >
> > > ### After context, default is restored

## `get_coded_entries(bundle, resource_type, status=None)`

Read the flattened coded identity of resources in a bundle.

The read-side counterpart to the `create_*` helpers: instead of walking nested CodeableConcepts by hand, get code/display/system/status and entry metadata as flat records. Medication resources are handled specially: `medicationCodeableConcept` is read directly, and `medicationReference` is resolved to its target (bundled or contained) Medication.

Resources with no coded identity at all (no codings and no concept text) are skipped.

| PARAMETER       | DESCRIPTION                                                                                                                                                   |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `bundle`        | The bundle to read **TYPE:** `Bundle`                                                                                                                         |
| `resource_type` | A resource type name or list of names (e.g. "Condition" or ["MedicationStatement", "MedicationRequest"]) **TYPE:** `Union[str, List[str]]`                    |
| `status`        | Only return entries with this status. For Condition and AllergyIntolerance this matches the clinicalStatus code **TYPE:** `Optional[str]` **DEFAULT:** `None` |

| RETURNS            | DESCRIPTION                                                    |
| ------------------ | -------------------------------------------------------------- |
| `List[CodedEntry]` | List of CodedEntry records, in bundle order per requested type |

Example

> > > bundle = load_bundle("synthea_patient.json") for entry in get_coded_entries(bundle, "Condition", status="active"): ... print(entry.code, entry.display, entry.authored_on) meds = get_coded_entries(bundle, ["MedicationStatement", "MedicationRequest"])

## `get_default_version()`

Get the current default FHIR version.

| RETURNS       | DESCRIPTION                                                 |
| ------------- | ----------------------------------------------------------- |
| `FHIRVersion` | The current default FHIRVersion (R4B if not explicitly set) |

## `get_fhir_resource(resource_name, version=None)`

Dynamically import a FHIR resource class based on version.

| PARAMETER       | DESCRIPTION                                                                                                                   |
| --------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| `resource_name` | Name of the FHIR resource (e.g., "Patient", "Condition") **TYPE:** `str`                                                      |
| `version`       | FHIR version (None for default, or FHIRVersion enum/string) **TYPE:** `Optional[Union[FHIRVersion, str]]` **DEFAULT:** `None` |

| RETURNS     | DESCRIPTION                                       |
| ----------- | ------------------------------------------------- |
| `Type[Any]` | The FHIR resource class for the specified version |

| RAISES       | DESCRIPTION                                          |
| ------------ | ---------------------------------------------------- |
| `ValueError` | If version is invalid or resource cannot be imported |

Example

> > > Patient_R5 = get_fhir_resource("Patient") Patient_R4B = get_fhir_resource("Patient", "R4B") Patient_STU3 = get_fhir_resource("Patient", FHIRVersion.STU3)

## `get_medications(bundle, status=None)`

Read all medications in a bundle as flat coded entries.

Sugar over `get_coded_entries` spanning MedicationStatement and MedicationRequest, with `medicationReference` resolved within the bundle.

| PARAMETER | DESCRIPTION                                                                                            |
| --------- | ------------------------------------------------------------------------------------------------------ |
| `bundle`  | The bundle to read **TYPE:** `Bundle`                                                                  |
| `status`  | Only return medications with this status (e.g. "active") **TYPE:** `Optional[str]` **DEFAULT:** `None` |

| RETURNS            | DESCRIPTION                                          |
| ------------------ | ---------------------------------------------------- |
| `List[CodedEntry]` | List of CodedEntry records for all medications found |

Example

> > > for med in get_medications(bundle, status="active"): ... print(med.code, med.display, med.system)

## `get_resource_type(resource_type)`

Get the resource type class from string or type.

| PARAMETER       | DESCRIPTION                                                                                                   |
| --------------- | ------------------------------------------------------------------------------------------------------------- |
| `resource_type` | String name of the resource type (e.g. "Condition") or the type itself **TYPE:** `Union[str, Type[Resource]]` |

| RETURNS          | DESCRIPTION                 |
| ---------------- | --------------------------- |
| `Type[Resource]` | The R4B resource type class |

| RAISES       | DESCRIPTION                                                 |
| ------------ | ----------------------------------------------------------- |
| `ValueError` | If the resource type is not supported or cannot be imported |

## `get_resource_version(resource)`

Detect the FHIR version of a resource based on its module path.

| PARAMETER  | DESCRIPTION                              |
| ---------- | ---------------------------------------- |
| `resource` | A FHIR resource instance **TYPE:** `Any` |

| RETURNS                 | DESCRIPTION                                   |
| ----------------------- | --------------------------------------------- |
| `Optional[FHIRVersion]` | The FHIRVersion if detectable, None otherwise |

Example

> > > from fhir.resources.R4B.patient import Patient patient = Patient(id="123") version = get_resource_version(patient) print(version) FHIRVersion.R4B

## `get_resources(bundle, resource_type)`

Get all resources of a specific type from a bundle.

| PARAMETER       | DESCRIPTION                                                                                                   |
| --------------- | ------------------------------------------------------------------------------------------------------------- |
| `bundle`        | The bundle to search **TYPE:** `Bundle`                                                                       |
| `resource_type` | String name of the resource type (e.g. "Condition") or the type itself **TYPE:** `Union[str, Type[Resource]]` |

| RETURNS          | DESCRIPTION                             |
| ---------------- | --------------------------------------- |
| `List[Resource]` | List of resources of the specified type |

Example

> > > bundle = create_bundle()
> > >
> > > ### Using string identifier
> > >
> > > conditions = get_resources(bundle, "Condition") medications = get_resources(bundle, "MedicationStatement") allergies = get_resources(bundle, "AllergyIntolerance")
> > >
> > > ### Or using type directly
> > >
> > > from fhir.resources.condition import Condition conditions = get_resources(bundle, Condition)

## `load_bundle(source, version=None)`

Load and validate a FHIR Bundle, raising on any validation error.

Validates the bundle structure and every entry resource, aggregating all issues into a single report rather than failing on the first error. Issue expressions locate the offending entry, e.g. `Bundle.entry[2].resource.subject`. See the module docstring for exactly what is and is not checked.

| PARAMETER | DESCRIPTION                                                                                                                   |
| --------- | ----------------------------------------------------------------------------------------------------------------------------- |
| `source`  | A file path, a JSON string, or a dict representation of a Bundle **TYPE:** `Union[str, Path, Dict[str, Any]]`                 |
| `version` | FHIR version to validate against (default: session default) **TYPE:** `Optional[Union[FHIRVersion, str]]` **DEFAULT:** `None` |

| RETURNS  | DESCRIPTION                                        |
| -------- | -------------------------------------------------- |
| `Bundle` | The validated Bundle instance **TYPE:** `Resource` |

| RAISES                | DESCRIPTION                                                                  |
| --------------------- | ---------------------------------------------------------------------------- |
| `FHIRValidationError` | If parsing or validation fails; carries the full ValidationReport in .report |
| `FileNotFoundError`   | If a file path is given but does not exist                                   |

Example

> > > bundle = load_bundle("synthea_patient.json") try: ... bundle = load_bundle({"resourceType": "Bundle", "entry": [...]}) ... except FHIRValidationError as e: ... print(e.report.model_dump())

## `merge_bundles(bundles, bundle_type='collection', deduplicate=False, dedupe_key='id')`

Merge multiple FHIR bundles into a single bundle.

Combines entries from multiple bundles while preserving resource metadata. Useful for aggregating search results from multiple FHIR sources.

| PARAMETER     | DESCRIPTION                                                                                     |
| ------------- | ----------------------------------------------------------------------------------------------- |
| `bundles`     | List of bundles to merge **TYPE:** `List[Bundle]`                                               |
| `bundle_type` | Type for the merged bundle (default: "collection") **TYPE:** `str` **DEFAULT:** `'collection'`  |
| `deduplicate` | If True, remove duplicate resources based on dedupe_key **TYPE:** `bool` **DEFAULT:** `False`   |
| `dedupe_key`  | Resource attribute to use for deduplication (default: "id") **TYPE:** `str` **DEFAULT:** `'id'` |

| RETURNS  | DESCRIPTION                                            |
| -------- | ------------------------------------------------------ |
| `Bundle` | A new bundle containing all entries from input bundles |

Example

> > > ### Merge search results from multiple sources
> > >
> > > epic_bundle = gateway.search(Condition, {"patient": "123"}, "epic") cerner_bundle = gateway.search(Condition, {"patient": "123"}, "cerner") merged = merge_bundles([epic_bundle, cerner_bundle], deduplicate=True)
> > >
> > > ### Use in Document workflow
> > >
> > > doc = Document(data=merged) doc.fhir.bundle # Contains all conditions from both sources

## `prefetch_to_bundle(prefetch)`

Flatten CDS Hooks prefetch into a collection Bundle dict.

Converts the keyed prefetch format (used in CDS Hooks) into a flat collection bundle for downstream processing.

| PARAMETER  | DESCRIPTION                                                                                                               |
| ---------- | ------------------------------------------------------------------------------------------------------------------------- |
| `prefetch` | CDS Hooks prefetch dict with format: {"patient": {...}, "observations": {"entry": [...]}, ...} **TYPE:** `Dict[str, Any]` |

| RETURNS          | DESCRIPTION                                              |
| ---------------- | -------------------------------------------------------- |
| `Dict[str, Any]` | Bundle dict with type "collection" and flattened entries |

Example

> > > prefetch = request.prefetch bundle = prefetch_to_bundle(prefetch)

## `read_content_attachment(document_reference, include_data=True)`

Read the attachments in a human readable format from a FHIR DocumentReference content field.

| PARAMETER            | DESCRIPTION                                                                                                                                    |
| -------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| `document_reference` | The FHIR DocumentReference resource **TYPE:** `DocumentReference`                                                                              |
| `include_data`       | Whether to include the data of the attachments. If true, the data will be also be decoded (default: True) **TYPE:** `bool` **DEFAULT:** `True` |

| RETURNS                          | DESCRIPTION                                                                                                                                                                              |
| -------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `Optional[List[Dict[str, Any]]]` | Optional\[List\[Dict[str, Any]\]\]: List of dictionaries containing attachment data and metadata, or None if no attachments are found: \[ { "data": str, "metadata": Dict[str, Any] } \] |

## `resolve_reference(bundle, reference, parent=None)`

Resolve a FHIR Reference to its target resource within a bundle.

Read-side counterpart to `add_resource`: given a reference string or an R4B `Reference` element, find the resource it points to. Resolution is attempted in this order:

1. Contained: references starting with `#` are resolved against `parent.contained` by resource `id`.
1. Exact `fullUrl` match against `entry.fullUrl` (covers absolute URLs and `urn:uuid:...` references).
1. `Type/id` relative references: match an entry whose resource type name and `id` match, or an absolute `fullUrl` ending in `/Type/id`.
1. `urn:uuid:{id}` fallback: when no `fullUrl` matched, match a resource whose `id` equals the uuid part.

Never raises on unresolvable or malformed references; returns None instead. The lookup is built lazily per call (no caching or state).

| PARAMETER   | DESCRIPTION                                                                                                                                                               |
| ----------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `bundle`    | The bundle to search **TYPE:** `Bundle`                                                                                                                                   |
| `reference` | A reference string (e.g. "Patient/123", "urn:uuid:...", "#contained-id") or an R4B Reference element **TYPE:** `Union[str, Reference]`                                    |
| `parent`    | The resource that owns the reference, required only to resolve contained ("#id") references against its contained list **TYPE:** `Optional[Resource]` **DEFAULT:** `None` |

| RETURNS              | DESCRIPTION                                                              |
| -------------------- | ------------------------------------------------------------------------ |
| `Optional[Resource]` | The first matching resource, or None if the reference cannot be resolved |

Example

> > > bundle = load_bundle("synthea_patient.json") med_request = get_resources(bundle, "MedicationRequest")[0] medication = resolve_reference(bundle, med_request.medicationReference) patient = resolve_reference(bundle, "Patient/patient-1")

## `set_condition_category(condition, category)`

Set the category of a FHIR Condition to either 'problem-list-item' or 'encounter-diagnosis'.

| PARAMETER   | DESCRIPTION                                                                                |
| ----------- | ------------------------------------------------------------------------------------------ |
| `condition` | The FHIR Condition resource to modify **TYPE:** `Condition`                                |
| `category`  | The category to set. Must be 'problem-list-item' or 'encounter-diagnosis'. **TYPE:** `str` |

| RETURNS     | DESCRIPTION                                                                                |
| ----------- | ------------------------------------------------------------------------------------------ |
| `Condition` | The modified FHIR Condition resource with the specified category set **TYPE:** `Condition` |

| RAISES       | DESCRIPTION                                       |
| ------------ | ------------------------------------------------- |
| `ValueError` | If the category is not one of the allowed values. |

## `set_resources(bundle, resources, resource_type, replace=True)`

Set resources of a specific type in the bundle.

| PARAMETER       | DESCRIPTION                                                                                                                                                                     |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `bundle`        | The bundle to modify **TYPE:** `Bundle`                                                                                                                                         |
| `resources`     | The new resources to add **TYPE:** `List[Resource]`                                                                                                                             |
| `resource_type` | String name of the resource type (e.g. "Condition") or the type itself **TYPE:** `Union[str, Type[Resource]]`                                                                   |
| `replace`       | If True, remove existing resources of this type before adding new ones. If False, append new resources to existing ones. Defaults to True. **TYPE:** `bool` **DEFAULT:** `True` |

Example

> > > bundle = create_bundle()
> > >
> > > ### Append to existing resources (default behavior)
> > >
> > > set_resources(bundle, [condition1, condition2], "Condition") set_resources(bundle, [medication1], "MedicationStatement")
> > >
> > > ### Replace existing resources
> > >
> > > set_resources(bundle, [condition3], "Condition", replace=True)
> > >
> > > ### Or using type directly
> > >
> > > from fhir.resources.condition import Condition set_resources(bundle, [condition1, condition2], Condition)

## `validate_resource(resource, resource_type=None, version=None)`

Validate a FHIR resource and return a report. Never raises.

Runs structural validation (types, required fields, unknown fields) and checks primitive code fields against their required bindings. Binding issues are only reported once structural validation passes. See the module docstring for exactly what is and is not checked.

| PARAMETER       | DESCRIPTION                                                                                                                                                                                      |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `resource`      | A dict representation or an instantiated FHIR resource **TYPE:** `Union[Dict[str, Any], Resource]`                                                                                               |
| `resource_type` | Resource type name (e.g. "Condition"). Optional if the dict has a "resourceType" key or the input is already a resource **TYPE:** `Optional[str]` **DEFAULT:** `None`                            |
| `version`       | FHIR version to validate against (default: session default). Ignored for instantiated resources, which carry their own version **TYPE:** `Optional[Union[FHIRVersion, str]]` **DEFAULT:** `None` |

| RETURNS            | DESCRIPTION                                                                 |
| ------------------ | --------------------------------------------------------------------------- |
| `ValidationReport` | valid is True when no error/fatal issues exist **TYPE:** `ValidationReport` |

Example

> > > report = validate_resource({"resourceType": "Condition"}) report.valid False report.issues[0].expression 'Condition.subject'

## `bundlehelpers`

Helper functions for working with FHIR Bundles. Patterns:

- create\_\*(): create a new FHIR bundle
- add\_\*(): add a resource to a bundle
- get\_\*(): get resources from a bundle
- set\_\*(): set resources in a bundle
- merge\_\*(): merge multiple bundles into a single bundle
- extract\_\*(): extract resources from a bundle

### `add_resource(bundle, resource, full_url=None)`

Add a resource to a bundle.

| PARAMETER  | DESCRIPTION                                                                                       |
| ---------- | ------------------------------------------------------------------------------------------------- |
| `bundle`   | The bundle to add to **TYPE:** `Bundle`                                                           |
| `resource` | The resource to add, e.g. Condition, MedicationStatement, AllergyIntolerance **TYPE:** `Resource` |
| `full_url` | Optional full URL for the resource **TYPE:** `Optional[str]` **DEFAULT:** `None`                  |

### `count_resources(bundle)`

Count resources by type in a bundle.

| PARAMETER | DESCRIPTION                                   |
| --------- | --------------------------------------------- |
| `bundle`  | The FHIR Bundle to analyze **TYPE:** `Bundle` |

| RETURNS          | DESCRIPTION                                                                         |
| ---------------- | ----------------------------------------------------------------------------------- |
| `dict[str, int]` | Dictionary mapping resource type names to their counts.                             |
| `Example`        | {"Condition": 2, "MedicationStatement": 1, "Patient": 1} **TYPE:** `dict[str, int]` |

Example

> > > bundle = create_bundle() add_resource(bundle, create_condition(...)) add_resource(bundle, create_condition(...)) add_resource(bundle, create_medication_statement(...)) counts = count_resources(bundle) print(counts)

### `create_bundle(bundle_type='collection')`

Create an empty FHIR Bundle. https://www.hl7.org/fhir/bundle.html

| PARAMETER     | DESCRIPTION                                                                                                                                                                                                   |
| ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `bundle_type` | The type of bundle (default: collection) Valid types: document, message, transaction, transaction-response, batch, batch-response, history, searchset, collection **TYPE:** `str` **DEFAULT:** `'collection'` |

### `extract_resources(bundle, resource_type)`

Remove resources of a given type from a bundle and return them.

Useful for extracting and separating specific resource types (e.g., OperationOutcome) from a FHIR Bundle, modifying the bundle in place.

| PARAMETER       | DESCRIPTION                                                                                                                             |
| --------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| `bundle`        | The FHIR Bundle to process (modified in place) **TYPE:** `Bundle`                                                                       |
| `resource_type` | The FHIR resource class or string name to extract (e.g., OperationOutcome or "OperationOutcome") **TYPE:** `Union[str, Type[Resource]]` |

| RETURNS          | DESCRIPTION                                                                   |
| ---------------- | ----------------------------------------------------------------------------- |
| `List[Resource]` | List\[Resource\]: All resources of the specified type that were in the bundle |

### `get_resource_type(resource_type)`

Get the resource type class from string or type.

| PARAMETER       | DESCRIPTION                                                                                                   |
| --------------- | ------------------------------------------------------------------------------------------------------------- |
| `resource_type` | String name of the resource type (e.g. "Condition") or the type itself **TYPE:** `Union[str, Type[Resource]]` |

| RETURNS          | DESCRIPTION                 |
| ---------------- | --------------------------- |
| `Type[Resource]` | The R4B resource type class |

| RAISES       | DESCRIPTION                                                 |
| ------------ | ----------------------------------------------------------- |
| `ValueError` | If the resource type is not supported or cannot be imported |

### `get_resources(bundle, resource_type)`

Get all resources of a specific type from a bundle.

| PARAMETER       | DESCRIPTION                                                                                                   |
| --------------- | ------------------------------------------------------------------------------------------------------------- |
| `bundle`        | The bundle to search **TYPE:** `Bundle`                                                                       |
| `resource_type` | String name of the resource type (e.g. "Condition") or the type itself **TYPE:** `Union[str, Type[Resource]]` |

| RETURNS          | DESCRIPTION                             |
| ---------------- | --------------------------------------- |
| `List[Resource]` | List of resources of the specified type |

Example

> > > bundle = create_bundle()
> > >
> > > #### Using string identifier
> > >
> > > conditions = get_resources(bundle, "Condition") medications = get_resources(bundle, "MedicationStatement") allergies = get_resources(bundle, "AllergyIntolerance")
> > >
> > > #### Or using type directly
> > >
> > > from fhir.resources.condition import Condition conditions = get_resources(bundle, Condition)

### `merge_bundles(bundles, bundle_type='collection', deduplicate=False, dedupe_key='id')`

Merge multiple FHIR bundles into a single bundle.

Combines entries from multiple bundles while preserving resource metadata. Useful for aggregating search results from multiple FHIR sources.

| PARAMETER     | DESCRIPTION                                                                                     |
| ------------- | ----------------------------------------------------------------------------------------------- |
| `bundles`     | List of bundles to merge **TYPE:** `List[Bundle]`                                               |
| `bundle_type` | Type for the merged bundle (default: "collection") **TYPE:** `str` **DEFAULT:** `'collection'`  |
| `deduplicate` | If True, remove duplicate resources based on dedupe_key **TYPE:** `bool` **DEFAULT:** `False`   |
| `dedupe_key`  | Resource attribute to use for deduplication (default: "id") **TYPE:** `str` **DEFAULT:** `'id'` |

| RETURNS  | DESCRIPTION                                            |
| -------- | ------------------------------------------------------ |
| `Bundle` | A new bundle containing all entries from input bundles |

Example

> > > #### Merge search results from multiple sources
> > >
> > > epic_bundle = gateway.search(Condition, {"patient": "123"}, "epic") cerner_bundle = gateway.search(Condition, {"patient": "123"}, "cerner") merged = merge_bundles([epic_bundle, cerner_bundle], deduplicate=True)
> > >
> > > #### Use in Document workflow
> > >
> > > doc = Document(data=merged) doc.fhir.bundle # Contains all conditions from both sources

### `resolve_reference(bundle, reference, parent=None)`

Resolve a FHIR Reference to its target resource within a bundle.

Read-side counterpart to `add_resource`: given a reference string or an R4B `Reference` element, find the resource it points to. Resolution is attempted in this order:

1. Contained: references starting with `#` are resolved against `parent.contained` by resource `id`.
1. Exact `fullUrl` match against `entry.fullUrl` (covers absolute URLs and `urn:uuid:...` references).
1. `Type/id` relative references: match an entry whose resource type name and `id` match, or an absolute `fullUrl` ending in `/Type/id`.
1. `urn:uuid:{id}` fallback: when no `fullUrl` matched, match a resource whose `id` equals the uuid part.

Never raises on unresolvable or malformed references; returns None instead. The lookup is built lazily per call (no caching or state).

| PARAMETER   | DESCRIPTION                                                                                                                                                               |
| ----------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `bundle`    | The bundle to search **TYPE:** `Bundle`                                                                                                                                   |
| `reference` | A reference string (e.g. "Patient/123", "urn:uuid:...", "#contained-id") or an R4B Reference element **TYPE:** `Union[str, Reference]`                                    |
| `parent`    | The resource that owns the reference, required only to resolve contained ("#id") references against its contained list **TYPE:** `Optional[Resource]` **DEFAULT:** `None` |

| RETURNS              | DESCRIPTION                                                              |
| -------------------- | ------------------------------------------------------------------------ |
| `Optional[Resource]` | The first matching resource, or None if the reference cannot be resolved |

Example

> > > bundle = load_bundle("synthea_patient.json") med_request = get_resources(bundle, "MedicationRequest")[0] medication = resolve_reference(bundle, med_request.medicationReference) patient = resolve_reference(bundle, "Patient/patient-1")

### `set_resources(bundle, resources, resource_type, replace=True)`

Set resources of a specific type in the bundle.

| PARAMETER       | DESCRIPTION                                                                                                                                                                     |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `bundle`        | The bundle to modify **TYPE:** `Bundle`                                                                                                                                         |
| `resources`     | The new resources to add **TYPE:** `List[Resource]`                                                                                                                             |
| `resource_type` | String name of the resource type (e.g. "Condition") or the type itself **TYPE:** `Union[str, Type[Resource]]`                                                                   |
| `replace`       | If True, remove existing resources of this type before adding new ones. If False, append new resources to existing ones. Defaults to True. **TYPE:** `bool` **DEFAULT:** `True` |

Example

> > > bundle = create_bundle()
> > >
> > > #### Append to existing resources (default behavior)
> > >
> > > set_resources(bundle, [condition1, condition2], "Condition") set_resources(bundle, [medication1], "MedicationStatement")
> > >
> > > #### Replace existing resources
> > >
> > > set_resources(bundle, [condition3], "Condition", replace=True)
> > >
> > > #### Or using type directly
> > >
> > > from fhir.resources.condition import Condition set_resources(bundle, [condition1, condition2], Condition)

## `elementhelpers`

FHIR element creation functions.

This module provides convenience functions for creating FHIR elements that are used as building blocks within FHIR resources (e.g., CodeableConcept, Attachment, Coding).

### `create_dosage(text=None, route_code=None, route_display=None, route_system='http://snomed.info/sct', dose_value=None, dose_unit=None, frequency=None, period=None, period_unit=None, as_needed=None)`

Create a minimal FHIR Dosage element.

Builds a minimum viable Dosage suitable for attaching to a MedicationStatement or MedicationRequest. Only the fields you provide are populated. For anything more complex, construct the FHIR Dosage directly. https://build.fhir.org/dosage.html

| PARAMETER       | DESCRIPTION                                                                                                          |
| --------------- | -------------------------------------------------------------------------------------------------------------------- |
| `text`          | Free-text dosage instructions (e.g. "1 tablet twice daily") **TYPE:** `Optional[str]` **DEFAULT:** `None`            |
| `route_code`    | The route of administration code (e.g. SNOMED CT code for "oral") **TYPE:** `Optional[str]` **DEFAULT:** `None`      |
| `route_display` | The display name for the route code **TYPE:** `Optional[str]` **DEFAULT:** `None`                                    |
| `route_system`  | The code system for the route (default: SNOMED CT) **TYPE:** `Optional[str]` **DEFAULT:** `'http://snomed.info/sct'` |
| `dose_value`    | The numeric dose amount, set as doseAndRate.doseQuantity.value **TYPE:** `Optional[float]` **DEFAULT:** `None`       |
| `dose_unit`     | The unit for the dose amount (e.g. "mg", "tablet") **TYPE:** `Optional[str]` **DEFAULT:** `None`                     |
| `frequency`     | How many times per period the dose is taken (Timing.repeat.frequency) **TYPE:** `Optional[int]` **DEFAULT:** `None`  |
| `period`        | The length of the period (Timing.repeat.period) **TYPE:** `Optional[float]` **DEFAULT:** `None`                      |
| `period_unit`   | The unit of the period (e.g. "d" for day, "h" for hour) **TYPE:** `Optional[str]` **DEFAULT:** `None`                |
| `as_needed`     | Whether the medication is taken as needed (asNeededBoolean) **TYPE:** `Optional[bool]` **DEFAULT:** `None`           |

| RETURNS  | DESCRIPTION                                                                 |
| -------- | --------------------------------------------------------------------------- |
| `Dosage` | A FHIR Dosage element populated with the provided fields **TYPE:** `Dosage` |

### `create_single_attachment(content_type=None, data=None, url=None, title='Attachment created by HealthChain')`

Create a minimal FHIR Attachment.

Creates a FHIR Attachment resource with basic fields. Either data or url should be provided. If data is provided, it will be base64 encoded.

| PARAMETER      | DESCRIPTION                                                                                                                                            |
| -------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `content_type` | The MIME type of the content **TYPE:** `Optional[str]` **DEFAULT:** `None`                                                                             |
| `data`         | The actual data content to be base64 encoded **TYPE:** `Optional[str]` **DEFAULT:** `None`                                                             |
| `url`          | The URL where the data can be found **TYPE:** `Optional[str]` **DEFAULT:** `None`                                                                      |
| `title`        | A title for the attachment (default: "Attachment created by HealthChain") **TYPE:** `Optional[str]` **DEFAULT:** `'Attachment created by HealthChain'` |

| RETURNS      | DESCRIPTION                                                                |
| ------------ | -------------------------------------------------------------------------- |
| `Attachment` | A FHIR Attachment resource with basic metadata and content **TYPE:** `Any` |

### `create_single_codeable_concept(code, display=None, system='http://snomed.info/sct')`

Create a minimal FHIR CodeableConcept with a single coding.

| PARAMETER | DESCRIPTION                                                                                            |
| --------- | ------------------------------------------------------------------------------------------------------ |
| `code`    | REQUIRED. The code value from the code system **TYPE:** `str`                                          |
| `display` | The display name for the code **TYPE:** `Optional[str]` **DEFAULT:** `None`                            |
| `system`  | The code system (default: SNOMED CT) **TYPE:** `Optional[str]` **DEFAULT:** `'http://snomed.info/sct'` |

| RETURNS           | DESCRIPTION                                                          |
| ----------------- | -------------------------------------------------------------------- |
| `CodeableConcept` | A FHIR CodeableConcept resource with a single coding **TYPE:** `Any` |

### `create_single_reaction(code, display=None, system='http://snomed.info/sct', severity=None)`

Create a minimal FHIR Reaction with a single coding.

Creates a FHIR Reaction object with a single manifestation coding. The manifestation describes the clinical reaction that was observed. The severity indicates how severe the reaction was.

| PARAMETER  | DESCRIPTION                                                                                                                       |
| ---------- | --------------------------------------------------------------------------------------------------------------------------------- |
| `code`     | REQUIRED. The code value from the code system representing the reaction manifestation **TYPE:** `str`                             |
| `display`  | The display name for the manifestation code **TYPE:** `Optional[str]` **DEFAULT:** `None`                                         |
| `system`   | The code system for the manifestation code (default: SNOMED CT) **TYPE:** `Optional[str]` **DEFAULT:** `'http://snomed.info/sct'` |
| `severity` | The severity of the reaction (mild, moderate, severe) **TYPE:** `Optional[str]` **DEFAULT:** `None`                               |

| RETURNS                | DESCRIPTION                                                                                |
| ---------------------- | ------------------------------------------------------------------------------------------ |
| `List[Dict[str, Any]]` | A list containing a single FHIR Reaction dictionary with manifestation and severity fields |

## `r4b`

Version-aware re-exports for FHIR R4B resources.

Import FHIR R4B resource classes from here instead of fhir.resources directly:

```text
from healthchain.fhir.r4b import Condition, Patient, Appointment
```

This ensures version consistency with HealthChain's FHIR version management.

## `readers`

FHIR conversion and reading functions.

This module provides functions for converting between different FHIR representations and reading data from FHIR resources.

### `CodedEntry`

Bases: `BaseModel`

Flattened coded identity of a clinical resource.

JSON-serializable via `model_dump()` so it can be returned directly from agent tools. `code`/`display`/`system` come from the first coding; `codings` carries all of them.

### `EntryCoding`

Bases: `BaseModel`

A single coding (code/display/system) from a CodeableConcept.

### `convert_prefetch_to_fhir_objects(prefetch_dict)`

Convert a dictionary of FHIR resource dicts to FHIR Resource objects.

Takes a prefetch dictionary where values may be either dict representations of FHIR resources or already instantiated FHIR Resource objects, and ensures all values are FHIR Resource objects.

| PARAMETER       | DESCRIPTION                                                                          |
| --------------- | ------------------------------------------------------------------------------------ |
| `prefetch_dict` | Dictionary mapping keys to FHIR resource dicts or objects **TYPE:** `Dict[str, Any]` |

| RETURNS               | DESCRIPTION                                                                              |
| --------------------- | ---------------------------------------------------------------------------------------- |
| `Dict[str, Resource]` | Dict\[str, Resource\]: Dictionary with same keys but all values as FHIR Resource objects |

Example

> > > prefetch = { ... "patient": {"resourceType": "Patient", "id": "123"}, ... "condition": Condition(id="456", ...) ... } fhir_objects = convert_prefetch_to_fhir_objects(prefetch) isinstance(fhir_objects["patient"], Patient) # True isinstance(fhir_objects["condition"], Condition) # True

### `create_resource_from_dict(resource_dict, resource_type, raise_on_error=False)`

Create a FHIR resource instance from a dictionary

| PARAMETER        | DESCRIPTION                                                                                                                                |
| ---------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| `resource_dict`  | Dictionary representation of the resource **TYPE:** `Dict`                                                                                 |
| `resource_type`  | Type of FHIR resource to create **TYPE:** `str`                                                                                            |
| `raise_on_error` | If True, raise FHIRValidationError with a full ValidationReport instead of returning None on failure **TYPE:** `bool` **DEFAULT:** `False` |

| RETURNS              | DESCRIPTION                                                             |
| -------------------- | ----------------------------------------------------------------------- |
| `Optional[Resource]` | Optional\[Resource\]: FHIR resource instance or None if creation failed |

| RAISES                | DESCRIPTION                                    |
| --------------------- | ---------------------------------------------- |
| `FHIRValidationError` | If raise_on_error is True and validation fails |

### `get_coded_entries(bundle, resource_type, status=None)`

Read the flattened coded identity of resources in a bundle.

The read-side counterpart to the `create_*` helpers: instead of walking nested CodeableConcepts by hand, get code/display/system/status and entry metadata as flat records. Medication resources are handled specially: `medicationCodeableConcept` is read directly, and `medicationReference` is resolved to its target (bundled or contained) Medication.

Resources with no coded identity at all (no codings and no concept text) are skipped.

| PARAMETER       | DESCRIPTION                                                                                                                                                   |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `bundle`        | The bundle to read **TYPE:** `Bundle`                                                                                                                         |
| `resource_type` | A resource type name or list of names (e.g. "Condition" or ["MedicationStatement", "MedicationRequest"]) **TYPE:** `Union[str, List[str]]`                    |
| `status`        | Only return entries with this status. For Condition and AllergyIntolerance this matches the clinicalStatus code **TYPE:** `Optional[str]` **DEFAULT:** `None` |

| RETURNS            | DESCRIPTION                                                    |
| ------------------ | -------------------------------------------------------------- |
| `List[CodedEntry]` | List of CodedEntry records, in bundle order per requested type |

Example

> > > bundle = load_bundle("synthea_patient.json") for entry in get_coded_entries(bundle, "Condition", status="active"): ... print(entry.code, entry.display, entry.authored_on) meds = get_coded_entries(bundle, ["MedicationStatement", "MedicationRequest"])

### `get_medications(bundle, status=None)`

Read all medications in a bundle as flat coded entries.

Sugar over `get_coded_entries` spanning MedicationStatement and MedicationRequest, with `medicationReference` resolved within the bundle.

| PARAMETER | DESCRIPTION                                                                                            |
| --------- | ------------------------------------------------------------------------------------------------------ |
| `bundle`  | The bundle to read **TYPE:** `Bundle`                                                                  |
| `status`  | Only return medications with this status (e.g. "active") **TYPE:** `Optional[str]` **DEFAULT:** `None` |

| RETURNS            | DESCRIPTION                                          |
| ------------------ | ---------------------------------------------------- |
| `List[CodedEntry]` | List of CodedEntry records for all medications found |

Example

> > > for med in get_medications(bundle, status="active"): ... print(med.code, med.display, med.system)

### `prefetch_to_bundle(prefetch)`

Flatten CDS Hooks prefetch into a collection Bundle dict.

Converts the keyed prefetch format (used in CDS Hooks) into a flat collection bundle for downstream processing.

| PARAMETER  | DESCRIPTION                                                                                                               |
| ---------- | ------------------------------------------------------------------------------------------------------------------------- |
| `prefetch` | CDS Hooks prefetch dict with format: {"patient": {...}, "observations": {"entry": [...]}, ...} **TYPE:** `Dict[str, Any]` |

| RETURNS          | DESCRIPTION                                              |
| ---------------- | -------------------------------------------------------- |
| `Dict[str, Any]` | Bundle dict with type "collection" and flattened entries |

Example

> > > prefetch = request.prefetch bundle = prefetch_to_bundle(prefetch)

### `read_content_attachment(document_reference, include_data=True)`

Read the attachments in a human readable format from a FHIR DocumentReference content field.

| PARAMETER            | DESCRIPTION                                                                                                                                    |
| -------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| `document_reference` | The FHIR DocumentReference resource **TYPE:** `DocumentReference`                                                                              |
| `include_data`       | Whether to include the data of the attachments. If true, the data will be also be decoded (default: True) **TYPE:** `bool` **DEFAULT:** `True` |

| RETURNS                          | DESCRIPTION                                                                                                                                                                              |
| -------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `Optional[List[Dict[str, Any]]]` | Optional\[List\[Dict[str, Any]\]\]: List of dictionaries containing attachment data and metadata, or None if no attachments are found: \[ { "data": str, "metadata": Dict[str, Any] } \] |

## `resourcehelpers`

FHIR resource creation and modification functions.

This module provides convenience functions for creating and modifying FHIR resources.

Patterns:

- create\_\*(): create a new FHIR resource with sensible defaults
- set\_\*(): set specific fields of resources with soft validation
- add\_\*(): add data to resources safely

Parameters marked REQUIRED are required by FHIR specification.

### `add_coding_to_codeable_concept(codeable_concept, code, system, display=None)`

Add a coding to an existing CodeableConcept.

Useful for adding standardized codes (e.g., SNOMED CT) to resources that already have codes from other systems (e.g., ICD-10).

| PARAMETER          | DESCRIPTION                                                                      |
| ------------------ | -------------------------------------------------------------------------------- |
| `codeable_concept` | The CodeableConcept to add coding to **TYPE:** `CodeableConcept`                 |
| `code`             | The code value from the code system **TYPE:** `str`                              |
| `system`           | The code system URI **TYPE:** `str`                                              |
| `display`          | Optional display text for the code **TYPE:** `Optional[str]` **DEFAULT:** `None` |

| RETURNS           | DESCRIPTION                                                                       |
| ----------------- | --------------------------------------------------------------------------------- |
| `CodeableConcept` | The updated CodeableConcept with the new coding added **TYPE:** `CodeableConcept` |

Example

> > > #### Add SNOMED CT code to a condition that has ICD-10
> > >
> > > condition_code = condition.code condition_code = add_coding_to_codeable_concept( ... condition_code, ... code="44054006", ... system="http://snomed.info/sct", ... display="Type 2 diabetes mellitus" ... )

### `add_provenance_metadata(resource, source, tag_code=None, tag_display=None)`

Add provenance metadata to a FHIR resource.

Adds source system identifier, timestamp, and optional processing tags to track data lineage and transformations for audit trails.

| PARAMETER     | DESCRIPTION                                                                                                                    |
| ------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| `resource`    | The FHIR resource to annotate **TYPE:** `Any`                                                                                  |
| `source`      | Name of the source system (e.g., "epic", "cerner") **TYPE:** `str`                                                             |
| `tag_code`    | Optional tag code for processing operations (e.g., "aggregated", "deduplicated") **TYPE:** `Optional[str]` **DEFAULT:** `None` |
| `tag_display` | Optional display text for the tag **TYPE:** `Optional[str]` **DEFAULT:** `None`                                                |

| RETURNS    | DESCRIPTION                                                 |
| ---------- | ----------------------------------------------------------- |
| `Resource` | The resource with added provenance metadata **TYPE:** `Any` |

Example

> > > condition = create_condition(subject="Patient/123", code="E11.9") condition = add_provenance_metadata(condition, "epic", "aggregated", "Aggregated from source")

### `create_allergy_intolerance(patient, code=None, display=None, system='http://snomed.info/sct', *, generate_id=True, warn=True)`

Create a minimal active FHIR AllergyIntolerance. If you need to create a more complex allergy intolerance, use the FHIR AllergyIntolerance resource directly. https://build.fhir.org/allergyintolerance.html

| PARAMETER     | DESCRIPTION                                                                                                                               |
| ------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| `patient`     | REQUIRED. Reference to the patient (e.g. "Patient/123") **TYPE:** `str`                                                                   |
| `code`        | The allergen code **TYPE:** `Optional[str]` **DEFAULT:** `None`                                                                           |
| `display`     | The display name for the allergen **TYPE:** `Optional[str]` **DEFAULT:** `None`                                                           |
| `system`      | The code system (default: SNOMED CT) **TYPE:** `Optional[str]` **DEFAULT:** `'http://snomed.info/sct'`                                    |
| `generate_id` | Stamp an auto-generated 'hc-' id. Pass False for deterministic output (snapshot tests, evals) **TYPE:** `bool` **DEFAULT:** `True`        |
| `warn`        | Log a warning for spec-invalid codes. Pass False if you validate explicitly with validate_resource() **TYPE:** `bool` **DEFAULT:** `True` |

| RETURNS              | DESCRIPTION                                                                                                     |
| -------------------- | --------------------------------------------------------------------------------------------------------------- |
| `AllergyIntolerance` | A FHIR AllergyIntolerance resource with an auto-generated ID prefixed with 'hc-' **TYPE:** `AllergyIntolerance` |

### `create_condition(subject, clinical_status='active', code=None, display=None, system='http://snomed.info/sct', onset=None, *, generate_id=True, warn=True)`

Create a minimal active FHIR Condition. If you need to create a more complex condition, use the FHIR Condition resource directly. https://build.fhir.org/condition.html

| PARAMETER         | DESCRIPTION                                                                                                                                                                     |
| ----------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `subject`         | REQUIRED. Reference to the patient (e.g. "Patient/123") **TYPE:** `str`                                                                                                         |
| `clinical_status` | REQUIRED. Clinical status (default: active) **TYPE:** `str` **DEFAULT:** `'active'`                                                                                             |
| `code`            | The condition code **TYPE:** `Optional[str]` **DEFAULT:** `None`                                                                                                                |
| `display`         | The display name for the condition **TYPE:** `Optional[str]` **DEFAULT:** `None`                                                                                                |
| `system`          | The code system (default: SNOMED CT) **TYPE:** `Optional[str]` **DEFAULT:** `'http://snomed.info/sct'`                                                                          |
| `onset`           | When the condition began, as an ISO 8601 date/datetime string, set as onsetDateTime (e.g. "2024-01-15" or "2024-01-15T09:00:00Z") **TYPE:** `Optional[str]` **DEFAULT:** `None` |
| `generate_id`     | Stamp an auto-generated 'hc-' id. Pass False for deterministic output (snapshot tests, evals) **TYPE:** `bool` **DEFAULT:** `True`                                              |
| `warn`            | Log a warning for spec-invalid codes. Pass False if you validate explicitly with validate_resource() **TYPE:** `bool` **DEFAULT:** `True`                                       |

| RETURNS     | DESCRIPTION                                                                                   |
| ----------- | --------------------------------------------------------------------------------------------- |
| `Condition` | A FHIR Condition resource with an auto-generated ID prefixed with 'hc-' **TYPE:** `Condition` |

### `create_document_reference(data=None, url=None, content_type=None, status='current', description='DocumentReference created by HealthChain', attachment_title='Attachment created by HealthChain', *, generate_id=True, warn=True)`

Create a minimal FHIR DocumentReference. If you need to create a more complex document reference, use the FHIR DocumentReference resource directly. https://build.fhir.org/documentreference.html

| PARAMETER          | DESCRIPTION                                                                                                                               |
| ------------------ | ----------------------------------------------------------------------------------------------------------------------------------------- |
| `data`             | The data content of the document attachment **TYPE:** `Optional[Any]` **DEFAULT:** `None`                                                 |
| `url`              | URL where the document can be accessed **TYPE:** `Optional[str]` **DEFAULT:** `None`                                                      |
| `content_type`     | MIME type of the document (e.g. "application/pdf", "text/xml", "image/png") **TYPE:** `Optional[str]` **DEFAULT:** `None`                 |
| `status`           | REQUIRED. Status of the document reference (default: current) **TYPE:** `str` **DEFAULT:** `'current'`                                    |
| `description`      | Description of the document reference **TYPE:** `Optional[str]` **DEFAULT:** `'DocumentReference created by HealthChain'`                 |
| `attachment_title` | Title for the document attachment **TYPE:** `Optional[str]` **DEFAULT:** `'Attachment created by HealthChain'`                            |
| `generate_id`      | Stamp an auto-generated 'hc-' id. Pass False for deterministic output (snapshot tests, evals) **TYPE:** `bool` **DEFAULT:** `True`        |
| `warn`             | Log a warning for spec-invalid codes. Pass False if you validate explicitly with validate_resource() **TYPE:** `bool` **DEFAULT:** `True` |

| RETURNS             | DESCRIPTION                                                                                                   |
| ------------------- | ------------------------------------------------------------------------------------------------------------- |
| `DocumentReference` | A FHIR DocumentReference resource with an auto-generated ID prefixed with 'hc-' **TYPE:** `DocumentReference` |

### `create_document_reference_content(attachment_data=None, url=None, content_type='text/plain', language='en-US', title=None, **kwargs)`

Create a FHIR DocumentReferenceContent object.

Creates a DocumentReferenceContent structure that can be added to a DocumentReference. Either attachment_data or url must be provided. If attachment_data is provided, it will be base64 encoded automatically.

| PARAMETER         | DESCRIPTION                                                                                                                      |
| ----------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| `attachment_data` | The content data (text that will be base64 encoded) **TYPE:** `Optional[str]` **DEFAULT:** `None`                                |
| `url`             | URL where the content can be accessed **TYPE:** `Optional[str]` **DEFAULT:** `None`                                              |
| `content_type`    | MIME type (e.g., 'text/plain', 'text/html', 'application/pdf') (default: text/plain) **TYPE:** `str` **DEFAULT:** `'text/plain'` |
| `language`        | Language code (default: en-US) **TYPE:** `Optional[str]` **DEFAULT:** `'en-US'`                                                  |
| `title`           | Optional title for the content (default: "Attachment created by HealthChain") **TYPE:** `Optional[str]` **DEFAULT:** `None`      |
| `**kwargs`        | Additional DocumentReferenceContent fields (e.g., format, profile) **DEFAULT:** `{}`                                             |

| RETURNS          | DESCRIPTION                                                                                        |
| ---------------- | -------------------------------------------------------------------------------------------------- |
| `Dict[str, Any]` | Dict\[str, Any\]: A FHIR DocumentReferenceContent dictionary with attachment and optional language |

Example

> > > #### Create content with inline data
> > >
> > > content = create_document_reference_content( ... attachment_data="Patient presents with fever...", ... content_type="text/plain", ... title="Clinical Note" ... )
> > >
> > > #### Create content with URL reference
> > >
> > > content = create_document_reference_content( ... url="https://example.com/document.pdf", ... content_type="application/pdf", ... title="Lab Report" ... )
> > >
> > > #### Add content to a DocumentReference
> > >
> > > doc_ref = DocumentReference( ... id="doc-1", ... status="current", ... content=[content] ... )

### `create_medication_statement(subject, status='unknown', code=None, display=None, system='http://snomed.info/sct', dosage=None, *, generate_id=True, warn=True)`

Create a minimal FHIR MedicationStatement. If you need to create a more complex medication statement, use the FHIR MedicationStatement resource directly. https://build.fhir.org/medicationstatement.html

| PARAMETER     | DESCRIPTION                                                                                                                                                                                                                                                             |
| ------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `subject`     | REQUIRED. Reference to the patient (e.g. "Patient/123") **TYPE:** `str`                                                                                                                                                                                                 |
| `status`      | REQUIRED. Status of the medication. Default "unknown" (an R4B-valid code that makes no clinical assertion). Allowed R4B values: active, completed, entered-in-error, intended, stopped, on-hold, unknown, not-taken **TYPE:** `Optional[str]` **DEFAULT:** `'unknown'`  |
| `code`        | The medication code **TYPE:** `Optional[str]` **DEFAULT:** `None`                                                                                                                                                                                                       |
| `display`     | The display name for the medication **TYPE:** `Optional[str]` **DEFAULT:** `None`                                                                                                                                                                                       |
| `system`      | The code system (default: SNOMED CT) **TYPE:** `Optional[str]` **DEFAULT:** `'http://snomed.info/sct'`                                                                                                                                                                  |
| `dosage`      | Dosage instructions. A plain string is wrapped as a single free-text Dosage; a single Dosage is wrapped in a one-element list; a list of Dosage elements is used as-is. See create_dosage(). **TYPE:** `Optional[Union[str, Dosage, List[Dosage]]]` **DEFAULT:** `None` |
| `generate_id` | Stamp an auto-generated 'hc-' id. Pass False for deterministic output (snapshot tests, evals) **TYPE:** `bool` **DEFAULT:** `True`                                                                                                                                      |
| `warn`        | Log a warning for spec-invalid codes. Pass False if you validate explicitly with validate_resource() **TYPE:** `bool` **DEFAULT:** `True`                                                                                                                               |

| RETURNS               | DESCRIPTION                                                                                                       |
| --------------------- | ----------------------------------------------------------------------------------------------------------------- |
| `MedicationStatement` | A FHIR MedicationStatement resource with an auto-generated ID prefixed with 'hc-' **TYPE:** `MedicationStatement` |

### `create_patient(gender=None, birth_date=None, identifier=None, identifier_system='http://hospital.example.org', *, generate_id=True, warn=True)`

Create a minimal FHIR Patient resource with basic gender and birthdate If you need to create a more complex patient, use the FHIR Patient resource directly https://hl7.org/fhir/patient.html (No required fields).

| PARAMETER           | DESCRIPTION                                                                                                                                   |
| ------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| `gender`            | Administrative gender (male, female, other, unknown) **TYPE:** `Optional[str]` **DEFAULT:** `None`                                            |
| `birth_date`        | Birth date in YYYY-MM-DD format **TYPE:** `Optional[str]` **DEFAULT:** `None`                                                                 |
| `identifier`        | Optional identifier value for the patient (e.g., MRN) **TYPE:** `Optional[str]` **DEFAULT:** `None`                                           |
| `identifier_system` | The system for the identifier (default: "http://hospital.example.org") **TYPE:** `Optional[str]` **DEFAULT:** `'http://hospital.example.org'` |
| `generate_id`       | Stamp an auto-generated 'hc-' id. Pass False for deterministic output (snapshot tests, evals) **TYPE:** `bool` **DEFAULT:** `True`            |
| `warn`              | Log a warning for spec-invalid codes. Pass False if you validate explicitly with validate_resource() **TYPE:** `bool` **DEFAULT:** `True`     |

| RETURNS   | DESCRIPTION                                                                               |
| --------- | ----------------------------------------------------------------------------------------- |
| `Patient` | A FHIR Patient resource with an auto-generated ID prefixed with 'hc-' **TYPE:** `Patient` |

### `create_risk_assessment_from_prediction(subject, prediction, status='final', method=None, basis=None, comment=None, occurrence_datetime=None, *, generate_id=True, warn=True)`

Create a FHIR RiskAssessment from ML model prediction output. If you need to create a more complex risk assessment, use the FHIR RiskAssessment resource directly. https://hl7.org/fhir/riskassessment.html

| PARAMETER             | DESCRIPTION                                                                                                                                                                                                                                                                                                                            |
| --------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `subject`             | REQUIRED. Reference to the patient (e.g. "Patient/123") **TYPE:** `str`                                                                                                                                                                                                                                                                |
| `prediction`          | Dictionary containing prediction details with keys: - outcome: CodeableConcept or dict with code, display, system for the predicted outcome - probability: float between 0 and 1 representing the risk probability - qualitative_risk: Optional str indicating risk level (e.g., "high", "moderate", "low") **TYPE:** `Dict[str, Any]` |
| `status`              | REQUIRED. The status of the assessment (default: "final") **TYPE:** `str` **DEFAULT:** `'final'`                                                                                                                                                                                                                                       |
| `method`              | Optional CodeableConcept describing the assessment method/model used **TYPE:** `Optional[CodeableConcept]` **DEFAULT:** `None`                                                                                                                                                                                                         |
| `basis`               | Optional list of References to observations or other resources used as input **TYPE:** `Optional[List[Reference]]` **DEFAULT:** `None`                                                                                                                                                                                                 |
| `comment`             | Optional text comment about the assessment **TYPE:** `Optional[str]` **DEFAULT:** `None`                                                                                                                                                                                                                                               |
| `occurrence_datetime` | When the assessment was made (ISO format). Omitted when not provided — the helper never invents a timestamp **TYPE:** `Optional[str]` **DEFAULT:** `None`                                                                                                                                                                              |
| `generate_id`         | Stamp an auto-generated 'hc-' id. Pass False for deterministic output (snapshot tests, evals) **TYPE:** `bool` **DEFAULT:** `True`                                                                                                                                                                                                     |
| `warn`                | Log a warning for spec-invalid codes. Pass False if you validate explicitly with validate_resource() **TYPE:** `bool` **DEFAULT:** `True`                                                                                                                                                                                              |

| RETURNS          | DESCRIPTION                                                                                             |
| ---------------- | ------------------------------------------------------------------------------------------------------- |
| `RiskAssessment` | A FHIR RiskAssessment resource with an auto-generated ID prefixed with 'hc-' **TYPE:** `RiskAssessment` |

Example

> > > prediction = { ... "outcome": {"code": "A41.9", "display": "Sepsis", "system": "http://hl7.org/fhir/sid/icd-10"}, ... "probability": 0.85, ... "qualitative_risk": "high" ... } risk = create_risk_assessment("Patient/123", prediction)

### `create_value_quantity_observation(code, value, unit, status='final', subject=None, system='http://loinc.org', display=None, effective_datetime=None, *, generate_id=True, warn=True)`

Create a minimal FHIR Observation for vital signs or laboratory values. If you need to create a more complex observation, use the FHIR Observation resource directly. https://hl7.org/fhir/observation.html

| PARAMETER            | DESCRIPTION                                                                                                                                                                                                      |
| -------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `status`             | REQUIRED. The status of the observation (default: "final") **TYPE:** `str` **DEFAULT:** `'final'`                                                                                                                |
| `code`               | REQUIRED. The observation code (e.g., LOINC code for the measurement) **TYPE:** `str`                                                                                                                            |
| `value`              | The numeric value of the observation **TYPE:** `float`                                                                                                                                                           |
| `unit`               | The unit of measure (e.g., "beats/min", "mg/dL") **TYPE:** `str`                                                                                                                                                 |
| `system`             | The code system for the observation code (default: LOINC) **TYPE:** `str` **DEFAULT:** `'http://loinc.org'`                                                                                                      |
| `display`            | The display name for the observation code **TYPE:** `Optional[str]` **DEFAULT:** `None`                                                                                                                          |
| `effective_datetime` | When the observation was made (ISO format). Omitted when not provided — the helper never invents a timestamp, so only record a time the caller can actually assert **TYPE:** `Optional[str]` **DEFAULT:** `None` |
| `subject`            | Reference to the patient (e.g. "Patient/123") **TYPE:** `Optional[str]` **DEFAULT:** `None`                                                                                                                      |
| `generate_id`        | Stamp an auto-generated 'hc-' id. Pass False for deterministic output (snapshot tests, evals) **TYPE:** `bool` **DEFAULT:** `True`                                                                               |
| `warn`               | Log a warning for spec-invalid codes. Pass False if you validate explicitly with validate_resource() **TYPE:** `bool` **DEFAULT:** `True`                                                                        |

| RETURNS       | DESCRIPTION                                                                                       |
| ------------- | ------------------------------------------------------------------------------------------------- |
| `Observation` | A FHIR Observation resource with an auto-generated ID prefixed with 'hc-' **TYPE:** `Observation` |

### `set_condition_category(condition, category)`

Set the category of a FHIR Condition to either 'problem-list-item' or 'encounter-diagnosis'.

| PARAMETER   | DESCRIPTION                                                                                |
| ----------- | ------------------------------------------------------------------------------------------ |
| `condition` | The FHIR Condition resource to modify **TYPE:** `Condition`                                |
| `category`  | The category to set. Must be 'problem-list-item' or 'encounter-diagnosis'. **TYPE:** `str` |

| RETURNS     | DESCRIPTION                                                                                |
| ----------- | ------------------------------------------------------------------------------------------ |
| `Condition` | The modified FHIR Condition resource with the specified category set **TYPE:** `Condition` |

| RAISES       | DESCRIPTION                                       |
| ------------ | ------------------------------------------------- |
| `ValueError` | If the category is not one of the allowed values. |

## `utilities`

FHIR utility functions.

This module provides utility functions for common operations like ID generation, age calculation, and gender encoding.

### `calculate_age_from_birthdate(birth_date)`

Calculate age in years from a birth date string.

| PARAMETER    | DESCRIPTION                                                                |
| ------------ | -------------------------------------------------------------------------- |
| `birth_date` | Birth date in ISO format (YYYY-MM-DD or full ISO datetime) **TYPE:** `str` |

| RETURNS         | DESCRIPTION                                    |
| --------------- | ---------------------------------------------- |
| `Optional[int]` | Age in years, or None if birth date is invalid |

### `calculate_age_from_event_date(birth_date, event_date)`

Calculate age in years from birth date and event date (MIMIC-IV style).

Uses the formula: age = year(eventDate) - year(birthDate) This matches MIMIC-IV on FHIR de-identified age calculation.

| PARAMETER    | DESCRIPTION                                                                |
| ------------ | -------------------------------------------------------------------------- |
| `birth_date` | Birth date in ISO format (YYYY-MM-DD or full ISO datetime) **TYPE:** `str` |
| `event_date` | Event date in ISO format (YYYY-MM-DD or full ISO datetime) **TYPE:** `str` |

| RETURNS         | DESCRIPTION                                                         |
| --------------- | ------------------------------------------------------------------- |
| `Optional[int]` | Age in years based on year difference, or None if dates are invalid |

Example

> > > calculate_age_from_event_date("1990-06-15", "2020-03-10") 30

### `encode_gender(gender)`

Encode gender as integer for ML models.

Standard encoding: Male=1, Female=0, Other/Unknown=None

| PARAMETER | DESCRIPTION                                      |
| --------- | ------------------------------------------------ |
| `gender`  | Gender string (case-insensitive) **TYPE:** `str` |

| RETURNS         | DESCRIPTION                                                       |
| --------------- | ----------------------------------------------------------------- |
| `Optional[int]` | Encoded gender (1 for male, 0 for female, None for other/unknown) |

## `validation`

FHIR resource validation.

This module provides an explicit validation surface for FHIR resources: a report-returning `validate_resource` suitable for agent tool loops, a raising `load_bundle` for loading bundles from files or dicts, and the `ValidationReport`/`FHIRValidationError` types they share.

What IS checked:

- Structure: field types, required fields, and unknown fields, as enforced by the underlying `fhir.resources` Pydantic models.
- Required bindings on primitive `code` fields: values are checked against the value set shipped with the model metadata (e.g. `MedicationStatement.status`).

What is NOT checked:

- Bindings on CodeableConcept/Coding fields (no ValueSet expansion is bundled).
- FHIRPath invariants/constraints (e.g. "co-33: only one onset[x]").
- Profile conformance (e.g. US Core, UK Core).
- Reference integrity (whether referenced resources exist).

For full conformance validation, use a FHIR server's `$validate` operation against the relevant profiles.

### `FHIRValidationError`

Bases: `Exception`

Raised when FHIR validation fails. Carries the full ValidationReport.

### `ValidationIssue`

Bases: `BaseModel`

A single validation issue, mirroring FHIR OperationOutcome.issue fields.

https://www.hl7.org/fhir/operationoutcome.html

### `ValidationReport`

Bases: `BaseModel`

Result of validating a FHIR resource.

JSON-serializable via `model_dump()` so it can be returned directly from agent tools. Convert to a FHIR OperationOutcome resource with `to_operation_outcome()`.

#### `to_operation_outcome()`

Convert the report to a FHIR OperationOutcome resource.

| RETURNS    | DESCRIPTION                                                        |
| ---------- | ------------------------------------------------------------------ |
| `Resource` | An OperationOutcome of the report's FHIR version, with one issue   |
| `Resource` | per validation issue (or a single 'informational' issue if valid). |

### `load_bundle(source, version=None)`

Load and validate a FHIR Bundle, raising on any validation error.

Validates the bundle structure and every entry resource, aggregating all issues into a single report rather than failing on the first error. Issue expressions locate the offending entry, e.g. `Bundle.entry[2].resource.subject`. See the module docstring for exactly what is and is not checked.

| PARAMETER | DESCRIPTION                                                                                                                   |
| --------- | ----------------------------------------------------------------------------------------------------------------------------- |
| `source`  | A file path, a JSON string, or a dict representation of a Bundle **TYPE:** `Union[str, Path, Dict[str, Any]]`                 |
| `version` | FHIR version to validate against (default: session default) **TYPE:** `Optional[Union[FHIRVersion, str]]` **DEFAULT:** `None` |

| RETURNS  | DESCRIPTION                                        |
| -------- | -------------------------------------------------- |
| `Bundle` | The validated Bundle instance **TYPE:** `Resource` |

| RAISES                | DESCRIPTION                                                                  |
| --------------------- | ---------------------------------------------------------------------------- |
| `FHIRValidationError` | If parsing or validation fails; carries the full ValidationReport in .report |
| `FileNotFoundError`   | If a file path is given but does not exist                                   |

Example

> > > bundle = load_bundle("synthea_patient.json") try: ... bundle = load_bundle({"resourceType": "Bundle", "entry": [...]}) ... except FHIRValidationError as e: ... print(e.report.model_dump())

### `validate_resource(resource, resource_type=None, version=None)`

Validate a FHIR resource and return a report. Never raises.

Runs structural validation (types, required fields, unknown fields) and checks primitive code fields against their required bindings. Binding issues are only reported once structural validation passes. See the module docstring for exactly what is and is not checked.

| PARAMETER       | DESCRIPTION                                                                                                                                                                                      |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `resource`      | A dict representation or an instantiated FHIR resource **TYPE:** `Union[Dict[str, Any], Resource]`                                                                                               |
| `resource_type` | Resource type name (e.g. "Condition"). Optional if the dict has a "resourceType" key or the input is already a resource **TYPE:** `Optional[str]` **DEFAULT:** `None`                            |
| `version`       | FHIR version to validate against (default: session default). Ignored for instantiated resources, which carry their own version **TYPE:** `Optional[Union[FHIRVersion, str]]` **DEFAULT:** `None` |

| RETURNS            | DESCRIPTION                                                                 |
| ------------------ | --------------------------------------------------------------------------- |
| `ValidationReport` | valid is True when no error/fatal issues exist **TYPE:** `ValidationReport` |

Example

> > > report = validate_resource({"resourceType": "Condition"}) report.valid False report.issues[0].expression 'Condition.subject'

## `version`

FHIR version management for multi-version support.

This module provides utilities for working with different FHIR versions (STU3, R4B, R5). It enables dynamic resource loading, version context management, and basic resource conversion.

Usage

from healthchain.fhir.version import get_fhir_resource, FHIRVersion

### Get a resource class for a specific version

Patient_R4B = get_fhir_resource("Patient", "R4B") Patient_R5 = get_fhir_resource("Patient", FHIRVersion.R5)

### Set the default version for the session

set_default_version("R4B")

### Use context manager for temporary version changes

with fhir_version_context("STU3"): patient = get_fhir_resource("Patient") # Returns STU3 Patient

### Convert resources between versions

patient_r5 = Patient(id="123", gender="male") patient_r4b = convert_resource(patient_r5, "R4B")

### `FHIRVersion`

Bases: `str`, `Enum`

Supported FHIR versions.

R5 is the default version in fhir.resources library. R4B and STU3 are available via subpackages (e.g., fhir.resources.R4B).

### `convert_resource(resource, target_version)`

Convert a FHIR resource to a different version.

Converts by serializing the resource to a dictionary and deserializing with the target version's resource class. This approach works for resources with compatible field structures.

Note

Field mappings between FHIR versions may not be 1:1. Some fields may be added, removed, or renamed between versions. This function performs a best-effort conversion and may raise validation errors if the resource data is incompatible with the target version.

| PARAMETER        | DESCRIPTION                                                 |
| ---------------- | ----------------------------------------------------------- |
| `resource`       | The FHIR resource to convert **TYPE:** `Any`                |
| `target_version` | The target FHIR version **TYPE:** `Union[FHIRVersion, str]` |

| RETURNS | DESCRIPTION                                   |
| ------- | --------------------------------------------- |
| `Any`   | A new resource instance of the target version |

| RAISES            | DESCRIPTION                                              |
| ----------------- | -------------------------------------------------------- |
| `ValueError`      | If the resource type cannot be determined or imported    |
| `ValidationError` | If the resource data is incompatible with target version |

Example

> > > from fhir.resources.patient import Patient patient_r5 = Patient(id="123", gender="male") patient_r4b = convert_resource(patient_r5, "R4B") print(patient_r4b.**class**.**module**) fhir.resources.R4B.patient

### `fhir_version_context(version)`

Context manager for temporarily changing the default FHIR version.

| PARAMETER | DESCRIPTION                                                                    |
| --------- | ------------------------------------------------------------------------------ |
| `version` | The FHIR version to use within the context **TYPE:** `Union[FHIRVersion, str]` |

| YIELDS        | DESCRIPTION                         |
| ------------- | ----------------------------------- |
| `FHIRVersion` | The resolved FHIRVersion being used |

Example

> > > with fhir_version_context("R4B") as v: ... patient = get_fhir_resource("Patient") # R4B Patient ... print(f"Using {v}")
> > >
> > > #### After context, default is restored

### `get_default_version()`

Get the current default FHIR version.

| RETURNS       | DESCRIPTION                                                 |
| ------------- | ----------------------------------------------------------- |
| `FHIRVersion` | The current default FHIRVersion (R4B if not explicitly set) |

### `get_fhir_resource(resource_name, version=None)`

Dynamically import a FHIR resource class based on version.

| PARAMETER       | DESCRIPTION                                                                                                                   |
| --------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| `resource_name` | Name of the FHIR resource (e.g., "Patient", "Condition") **TYPE:** `str`                                                      |
| `version`       | FHIR version (None for default, or FHIRVersion enum/string) **TYPE:** `Optional[Union[FHIRVersion, str]]` **DEFAULT:** `None` |

| RETURNS     | DESCRIPTION                                       |
| ----------- | ------------------------------------------------- |
| `Type[Any]` | The FHIR resource class for the specified version |

| RAISES       | DESCRIPTION                                          |
| ------------ | ---------------------------------------------------- |
| `ValueError` | If version is invalid or resource cannot be imported |

Example

> > > Patient_R5 = get_fhir_resource("Patient") Patient_R4B = get_fhir_resource("Patient", "R4B") Patient_STU3 = get_fhir_resource("Patient", FHIRVersion.STU3)

### `get_resource_version(resource)`

Detect the FHIR version of a resource based on its module path.

| PARAMETER  | DESCRIPTION                              |
| ---------- | ---------------------------------------- |
| `resource` | A FHIR resource instance **TYPE:** `Any` |

| RETURNS                 | DESCRIPTION                                   |
| ----------------------- | --------------------------------------------- |
| `Optional[FHIRVersion]` | The FHIRVersion if detectable, None otherwise |

Example

> > > from fhir.resources.R4B.patient import Patient patient = Patient(id="123") version = get_resource_version(patient) print(version) FHIRVersion.R4B

### `reset_default_version()`

Reset the default FHIR version to R4B.

### `set_default_version(version)`

Set the global default FHIR version.

| PARAMETER | DESCRIPTION                                                            |
| --------- | ---------------------------------------------------------------------- |
| `version` | The FHIR version to use as default **TYPE:** `Union[FHIRVersion, str]` |

Example

> > > set_default_version("R4B") patient = get_fhir_resource("Patient") # Returns R4B Patient
