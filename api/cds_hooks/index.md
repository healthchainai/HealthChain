# CDS Hooks

## `EncounterDischargeContext`

Bases: `BaseHookContext`

Workflow: This hook is triggered during the discharge process for typically inpatient encounters. It can be invoked at any point from the start to the end of the discharge process. The purpose is to allow hook services to intervene in various aspects of the discharge decision. This includes verifying discharge medications, ensuring continuity of care planning, and verifying necessary documentation for discharge processing.

| ATTRIBUTE     | DESCRIPTION                                                                                                                               |
| ------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| `userId`      | REQUIRED. The ID of the current user, expected to be a Practitioner or PractitionerRole. For example, 'Practitioner/123'. **TYPE:** `str` |
| `patientId`   | REQUIRED. The FHIR Patient.id of the patient being discharged. **TYPE:** `str`                                                            |
| `encounterId` | REQUIRED. The FHIR Encounter.id of the encounter being ended. **TYPE:** `str`                                                             |

Documentation: https://cds-hooks.org/hooks/encounter-discharge/

## `OrderSelectContext`

Bases: `BaseHookContext`

Workflow: The order-select hook occurs after the clinician selects the order and before signing. This hook occurs when a clinician initially selects one or more new orders from a list of potential orders for a specific patient (including orders for medications, procedures, labs and other orders). The newly selected order defines that medication, procedure, lab, etc, but may or may not define the additional details necessary to finalize the order.

| ATTRIBUTE     | DESCRIPTION                                                                                                                                                                                                              |
| ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `userId`      | REQUIRED. An identifier of the current user, in the format [ResourceType]/[id], where ResourceType is either 'Practitioner' or 'PractitionerRole'. Examples: 'PractitionerRole/123', 'Practitioner/abc'. **TYPE:** `str` |
| `patientId`   | REQUIRED. The FHIR Patient.id representing the current patient in context. **TYPE:** `str`                                                                                                                               |
| `encounterId` | OPTIONAL. The FHIR Encounter.id representing the current encounter in context, if applicable. **TYPE:** `Optional[str]`                                                                                                  |
| `selections`  | REQUIRED. A list of the FHIR id(s) of the newly selected orders, referencing resources in the draftOrders Bundle. Example: 'MedicationRequest/103'. **TYPE:** `[str]`                                                    |
| `draftOrders` | REQUIRED. A Bundle of FHIR request resources with a draft status, representing all unsigned orders from the current session, including newly selected orders. **TYPE:** `object`                                         |

Documentation: https://cds-hooks.org/hooks/order-select/

## `OrderSignContext`

Bases: `BaseHookContext`

Workflow: The order-sign hook is triggered when a clinician is ready to sign one or more orders for a patient. This includes orders for medications, procedures, labs, and other orders. It is one of the last workflow events before an order is promoted from a draft status. The context includes all order details such as dose, quantity, route, etc., even though the order is still in a draft status. This hook is also applicable for re-signing revised orders, which may have a status other than 'draft'. The hook replaces the medication-prescribe and order-review hooks.

| ATTRIBUTE     | DESCRIPTION                                                                                                                                                                       |
| ------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `userId`      | REQUIRED. The ID of the current user, expected to be of type 'Practitioner' or 'PractitionerRole'. Examples include 'PractitionerRole/123' or 'Practitioner/abc'. **TYPE:** `str` |
| `patientId`   | REQUIRED. The FHIR Patient.id representing the current patient in context. **TYPE:** `str`                                                                                        |
| `encounterId` | OPTIONAL. The FHIR Encounter.id of the current encounter in context. **TYPE:** `Optional[str]`                                                                                    |
| `draftOrders` | REQUIRED. A Bundle of FHIR request resources with a draft status, representing orders that aren't yet signed from the current ordering session. **TYPE:** `dict`                  |

Documentation: https://cds-hooks.org/hooks/order-sign/

## `PatientViewContext`

Bases: `BaseHookContext`

Workflow: The user has just opened a patient's record; typically called only once at the beginning of a user's interaction with a specific patient's record.

| ATTRIBUTE     | DESCRIPTION                                                                                                                                                                                                                        |
| ------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `userId`      | An identifier of the current user, in the format [ResourceType]/[id], where ResourceType is one of 'Practitioner', 'PractitionerRole', 'Patient', or 'RelatedPerson'. Examples: 'Practitioner/abc', 'Patient/123'. **TYPE:** `str` |
| `patientId`   | The FHIR Patient.id representing the current patient in context. **TYPE:** `str`                                                                                                                                                   |
| `encounterId` | The FHIR Encounter.id representing the current encounter in context, if applicable. This field is optional. **TYPE:** `Optional[str]`                                                                                              |

Documentation: https://cds-hooks.org/hooks/patient-view/

https://cds-hooks.org/specification/current/#discovery

## `CDSService`

Bases: `BaseModel`

A model representing a CDS service configuration.

| ATTRIBUTE           | DESCRIPTION                                                                                                                                                                                                                   |
| ------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `hook`              | The hook this service should be invoked on. This should correspond to one of the predefined hooks. **TYPE:** `str`                                                                                                            |
| `title`             | The human-friendly name of this service. It is recommended to provide this for better usability. **TYPE:** `Optional[str]`                                                                                                    |
| `description`       | A detailed description of what this service does and its purpose within the CDS framework. **TYPE:** `str`                                                                                                                    |
| `id`                | The unique identifier of this service. It forms part of the URL as {baseUrl}/cds-services/{id}. **TYPE:** `str`                                                                                                               |
| `prefetch`          | Optional FHIR queries that the service requests the CDS Client to perform and provide on each service call. Keys describe the type of data and values are the actual FHIR query strings. **TYPE:** `Optional[Dict[str, str]]` |
| `usageRequirements` | Human-friendly description of any preconditions for the use of this CDS service. **TYPE:** `Optional[str]`                                                                                                                    |

Documentation: https://cds-hooks.org/specification/current/#response

## `CDSServiceInformation`

Bases: `BaseModel`

A CDS Service is discoverable via a stable endpoint by CDS Clients. The Discovery endpoint includes information such as a description of the CDS Service, when it should be invoked, and any data that is requested to be prefetched.

This is not compulsary

https://cds-hooks.org/specification/current/#feedback

## `CDSFeedback`

Bases: `BaseModel`

A feedback endpoint enables suggestion tracking & analytics. A CDS Service MAY support a feedback endpoint; a CDS Client SHOULD be capable of sending feedback.

| ATTRIBUTE             | DESCRIPTION                                                                                                   |
| --------------------- | ------------------------------------------------------------------------------------------------------------- |
| `card`                | The card.uuid from the CDS Hooks response. Uniquely identifies the card. **TYPE:** `str`                      |
| `outcome`             | The outcome of the action, either 'accepted' or 'overridden'. **TYPE:** `str`                                 |
| `acceptedSuggestions` | An array of accepted suggestions, required if the outcome is 'accepted'. **TYPE:** `List[AcceptedSuggestion]` |
| `overrideReason`      | The reason for overriding, including any coding and comments. **TYPE:** `Optional[OverrideReason]`            |
| `outcomeTimestamp`    | The ISO8601 timestamp of when the action was taken on the card. **TYPE:** `datetime`                          |

Documentation: https://cds-hooks.org/specification/current/#feedback
