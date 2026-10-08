# Gateway

The HealthChain Gateway module provides a secure integration layer for connecting your models and agents with multiple healthcare systems.

It provides a unified interface for connecting to FHIR servers, CDS Hooks, and SOAP/CDA services and is designed to be used in conjunction with the [HealthChainAPI](https://healthchainai.github.io/HealthChain/reference/gateway/api/index.md) to create a complete healthcare integration platform.

## Features 🚀

The Gateway handles the complex parts of healthcare integration:

- **Multiple Protocols**: Works with [FHIR RESTful APIs](https://hl7.org/fhir/http.html), [CDS Hooks](https://cds-hooks.hl7.org/), and [Epic NoteReader CDI](https://discovery.hgdata.com/product/epic-notereader-cdi) (SOAP/CDA service) out of the box
- **Multi-Source**: Context managers to work with data from multiple EHR systems and FHIR servers safely
- **Smart Connections**: Handles [OAuth2.0 authentication](https://oauth.net/2/), connection pooling, and automatic token refresh
- **Event-Driven**: Native [asyncio](https://docs.python.org/3/library/asyncio.html) support for real-time events, audit trails, and workflow automation
- **Transform & Aggregate**: FastAPI-style declarative patterns to create endpoints for enhancing and combining data
- **Developer-Friendly**: Modern Python typing and validation support via [fhir.resources](https://github.com/nazrulworld/fhir.resources) (powered by [Pydantic](https://docs.pydantic.dev/)), protocol-based interfaces, and informative error messages

## Key Components

| Component                                                                                                | Description                                                           | Use Case                                                                                                     |
| -------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| [**HealthChainAPI**](https://healthchainai.github.io/HealthChain/reference/gateway/api/index.md)         | FastAPI app with gateway and service registration                     | Main app that coordinates everything                                                                         |
| [**FHIRGateway**](https://healthchainai.github.io/HealthChain/reference/gateway/fhir_gateway/index.md)   | Sync and async FHIR client with connection pooling and authentication | Reading/writing patient data from EHRs (Epic, Cerner, etc.) or application FHIR servers (Medplum, Hapi etc.) |
| [**CDSHooksService**](https://healthchainai.github.io/HealthChain/reference/gateway/cdshooks/index.md)   | Clinical Decision Support hooks service                               | Real-time alerts and recommendations                                                                         |
| [**NoteReaderService**](https://healthchainai.github.io/HealthChain/reference/gateway/soap_cda/index.md) | SOAP/CDA document processing service                                  | Processing clinical documents and notes                                                                      |
| [**Event System**](https://healthchainai.github.io/HealthChain/reference/gateway/events/index.md)        | Event-driven integration                                              | Audit trails, workflow automation                                                                            |

## Basic Usage

```python
from healthchain.gateway import HealthChainAPI, FHIRGateway
from healthchain.fhir.r4b import Patient

# Create the application
app = HealthChainAPI()

# Synchronous FHIR gateway
fhir = FHIRGateway()
fhir.add_source("epic", "fhir://epic.org/api/FHIR/R4?client_id=...")

@fhir.transform(Patient)
def enhance_patient(id: str, source: str = None) -> Patient:
    patient = fhir.read(Patient, id, source)
    patient.active = True  # Your custom logic here
    fhir.update(patient, source)
    return patient

app.register_gateway(fhir)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app)
    # Default: http://127.0.0.1:8000/
```

```python
from healthchain.gateway import HealthChainAPI, AsyncFHIRGateway
from healthchain.fhir.r4b import Patient

# Create the application
app = HealthChainAPI()

# Asynchronous FHIR gateway
async_fhir = AsyncFHIRGateway()
async_fhir.add_source("medplum", "fhir://api.medplum.com/fhir/R4/?client_id=...")

@async_fhir.transform(Patient)
async def enhance_patient_async(id: str, source: str = None) -> Patient:
    # modify is a context manager that allows you to modify the patient resource
    async with async_fhir.modify(Patient, id, source) as patient:
        patient.active = True  # Your custom logic here
        return patient

app.register_gateway(async_fhir)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app)
```

You can also register multiple services of different protocols:

```python
from healthchain.gateway import (
    HealthChainAPI, FHIRGateway,
    CDSHooksService, NoteReaderService
)

app = HealthChainAPI()

# FHIR for patient data
fhir = FHIRGateway()
fhir.add_source("epic", "fhir://fhir.epic.com/r4?...")

# CDS Hooks for real-time alerts
cds = CDSHooksService()

@cds.hook("patient-view", id="allergy-alerts")
def check_allergies(request):
    # Your logic here
    return {"cards": [...]}

# SOAP for clinical documents
notes = NoteReaderService()

@notes.method("ProcessDocument")
def process_note(request):
    # Your NLP pipeline here
    return processed_document

# Register everything
app.register_gateway(fhir)
app.register_service(cds)
app.register_service(notes)
```

## Protocol Support

| Protocol      | Implementation                   | Features                                                                                                                                                                                                                                                                                                                                                                               |
| ------------- | -------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **FHIR API**  | `FHIRGateway` `AsyncFHIRGateway` | FHIR-instance level CRUD operations - [read](https://hl7.org/fhir/http.html#read), [create](https://hl7.org/fhir/http.html#create), [update](https://hl7.org/fhir/http.html#update), [delete](https://hl7.org/fhir/http.html#delete), [search](https://hl7.org/fhir/http.html#search), register `transform` and `aggregate` handlers, connection pooling and authentication management |
| **CDS Hooks** | `CDSHooksService`                | Hook Registration, Service Discovery                                                                                                                                                                                                                                                                                                                                                   |
| **SOAP/CDA**  | `NoteReaderService`              | Method Registration (`ProcessDocument`), SOAP Service Discovery (WSDL)                                                                                                                                                                                                                                                                                                                 |
