#!/usr/bin/env python3
"""
Discharge Note Summarizer (Transformer) — a summarization pipeline served
as a CDS Hooks service, using a HuggingFace transformer model directly.

Requirements:
    pip install "healthchain[examples,sandbox]" torch
    # Note: downloads ~1GB on first run (sshleifer/distilbart-cnn-12-6)

Run:
    python cookbook/cds_discharge_summarizer_hf_trf.py
    # Fires test requests from discharge_notes.csv and exits.
    # To keep the service running for manual exploration, replace
    # `with app.sandbox(...)` with `app.run()` in the __main__ block.
"""

from pathlib import Path

from transformers import pipeline as hf_pipeline

from healthchain.gateway import HealthChainAPI, CDSHooksService
from healthchain.io import CdsFhirAdapter, Document
from healthchain.models import Card, CDSRequest, CDSResponse, Source
from healthchain.pipeline import Pipeline

_DATA_DIR = Path(__file__).parent / "data"


def create_pipeline() -> Pipeline:
    """One node: run the summarizer and build the CDS card inline."""
    summarizer = hf_pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")
    pipeline = Pipeline()

    @pipeline.add_node
    def summarize_to_card(doc: Document) -> Document:
        if not doc.text:
            return doc

        summary = summarizer(doc.text)[0]["summary_text"]

        doc.cds.cards = [
            Card(
                summary=summary[:140],
                indicator="info",
                source=Source(label="Discharge Note Summarizer"),
                detail=summary,
            )
        ]
        return doc

    return pipeline


def create_app() -> HealthChainAPI:
    pipeline = create_pipeline()
    adapter = CdsFhirAdapter()
    cds = CDSHooksService()

    @cds.hook("encounter-discharge", id="discharge-summarizer")
    def discharge_summarizer(request: CDSRequest) -> CDSResponse:
        doc = adapter.parse(request)
        doc = pipeline(doc)
        return adapter.format(doc)

    app = HealthChainAPI(
        title="Discharge Note Summarizer",
        description="AI-powered discharge note summarization service",
        service_type="cds-hooks",
    )
    app.register_service(cds, path="/cds")
    return app


app = create_app()


if __name__ == "__main__":
    with app.sandbox("discharge-summarizer") as client:
        client.load_free_text(
            csv_path=str(_DATA_DIR / "discharge_notes.csv"),
            column_name="text",
        )
        responses = client.send_requests()
        client.save_results("./output/")
