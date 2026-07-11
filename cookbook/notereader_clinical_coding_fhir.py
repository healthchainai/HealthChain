#!/usr/bin/env python3
"""
A complete medical coding pipeline: process clinical notes from Epic NoteReader
and write extracted conditions as validated FHIR.
Demonstrates bring-your-own-NLP pipelines, legacy CDA integration, and FHIR write-back.

Requirements:
    pip install "healthchain[cda,examples]" "spacy>=3.7,<3.8" \
        https://s3-us-west-2.amazonaws.com/ai2-s2-scispacy/releases/v0.5.4/en_core_sci_sm-0.5.4.tar.gz
    # The en_core_sci_sm 0.5.4 model needs spaCy <3.8 to load; install in one
    # command so pip resolves a compatible set.

Run:
    python cookbook/notereader_clinical_coding_fhir.py
    # Fires a test CDA document and exits.
    # To keep the service running for manual exploration, replace
    # `with app.sandbox(...)` with `app.run()` in the __main__ block.
"""

import logging
from pathlib import Path

import spacy

from healthchain.fhir import add_provenance_metadata
from healthchain.gateway.api import HealthChainAPI
from healthchain.gateway.fhir import FHIRGateway
from healthchain.gateway.clients import FHIRAuthConfig
from healthchain.gateway.soap import NoteReaderService
from healthchain.io import CdaAdapter, Document
from healthchain.models import CdaRequest
from healthchain.pipeline import Pipeline


# Suppress Spyne warnings
logging.getLogger("spyne.model.complex").setLevel(logging.ERROR)

_DATA_DIR = Path(__file__).parent / "data"

# The patient the extracted Conditions are written against. In production,
# resolve this from the incoming document's patient context.
PATIENT_REF = "Patient/123"

# Load configuration from environment variables
config = FHIRAuthConfig.from_env("MEDPLUM")
MEDPLUM_URL = config.to_connection_string()


def create_pipeline():
    """Build the medical coding pipeline: clinical NER + entity linking + FHIR problem list."""
    nlp = spacy.load("en_core_sci_sm")
    pipeline = Pipeline()

    # Simple dummy linker for demo purposes — swap for a real entity linker
    # (e.g. scispacy's UmlsEntityLinker) in production
    dummy_linker = {
        "pneumonia": "233604007",
        "type 2 diabetes mellitus": "44054006",
        "congestive heart failure": "42343007",
        "chronic kidney disease": "431855005",
        "hypertension": "38341003",
        "community acquired pneumonia": "385093006",
        "ventilator associated pneumonia": "233717007",
        "anaphylaxis": "39579001",
        "delirium": "2776000",
        "depression": "35489007",
        "asthma": "195967001",
        "copd": "13645005",
    }

    @pipeline.add_node
    def extract_problems(doc: Document) -> Document:
        """Run NER, link entities to SNOMED CT codes, and update the FHIR problem list."""
        spacy_doc = nlp(doc.text)

        doc.update_problem_list(
            [
                {"text": ent.text, "cui": dummy_linker.get(ent.text.lower())}
                for ent in spacy_doc.ents
            ],
            patient_ref=PATIENT_REF,
        )

        return doc

    return pipeline


def create_app():
    pipeline = create_pipeline()
    cda_adapter = CdaAdapter()

    # Modern FHIR sources
    fhir_gateway = FHIRGateway()
    fhir_gateway.add_source("medplum", MEDPLUM_URL)

    # Legacy CDA processing
    note_service = NoteReaderService()

    @note_service.method("ProcessDocument")
    def ai_coding_workflow(request: CdaRequest):
        doc = cda_adapter.parse(request)
        doc = pipeline(doc)

        for condition in doc.fhir.problem_list:
            # Add basic provenance tracking
            condition = add_provenance_metadata(
                condition, source="epic-notereader", tag_code="cdi"
            )
            fhir_gateway.create(condition, source="medplum")

        cda_response = cda_adapter.format(doc)

        return cda_response

    # Register services
    app = HealthChainAPI(
        title="Epic CDI Service",
        description="Clinical document intelligence with FHIR and NoteReader integration",
        service_type="fhir-gateway",
    )
    app.register_gateway(fhir_gateway, path="/fhir")
    app.register_service(note_service, path="/notereader")

    return app


# Create the app
app = create_app()


if __name__ == "__main__":
    with app.sandbox(workflow="sign-note-inpatient", protocol="soap") as client:
        client.load_from_path(_DATA_DIR / "notereader_cda.xml")
        responses = client.send_requests()
        client.save_results("./output/")
