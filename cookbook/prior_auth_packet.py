#!/usr/bin/env python3
"""
Prior Authorization: from a FHIR chart pull to a coded request packet

A treating office asks for an MRI. The request lands in the EHR as free text —
"MRI lumbar spine without contrast", diagnosis "lumbar radiculopathy, right L5
distribution" — and the payer will not read free text. Somebody has to pull the
chart, code the diagnosis and the requested service, check the request against
the utilization-review criteria, and send back a packet that cites both. Today
that somebody is usually a person with a browser and a code book.

This example does the whole loop against FHIR: pull the chart from a live FHIR
server, resolve the free text to codes through HealthChain's terminology seam,
apply the criteria, and emit the decision as FHIR the payer can ingest — a coded
ServiceRequest, a Task carrying the authorization request, and a
DocumentReference holding the justification letter.

Bring your own chart. This script ships a pre-baked chart pull so it runs offline
with zero setup — no server, no credentials. Point it at a real FHIR server and
the rest is unchanged.

Requirements:
- pip install healthchain

Run:
    python cookbook/prior_auth_packet.py
    # Codes the request, applies the criteria, prints the packet.
    # Set MEDPLUM_* env vars to pull the chart from a live FHIR server and
    # write the packet back to it.
"""

import json
import os
import re
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv

from healthchain.fhir import (
    add_resource,
    create_bundle,
    create_document_reference,
    get_resources,
    load_bundle,
    validate_resource,
)
from healthchain.fhir.r4b import Condition, DocumentReference, ServiceRequest, Task
from healthchain.terminology import ICD10CM, Coding, LocalCodeLookup, TerminologyLookup

load_dotenv()

DATA = Path(__file__).parent / "data"
IMAGING_CATALOG = "http://example.org/fhir/CodeSystem/imaging-order-catalog"

# The chart as it comes off a FHIR server: Condition and ServiceRequest carry a
# `code.text` and no coding at all, which is what a text-entered order looks like
# every time. `healthchain seed medplum` prints the ID Medplum assigns; export
# it as PATIENT_ID to run against your server.
PATIENT_ID = os.getenv("PATIENT_ID", "wc-claimant-001")


# --- Step 1: pull the chart --------------------------------------------------
def pull_chart():
    """Fetch the patient's chart: the diagnosis, the request, and the note.

    With MEDPLUM_* configured this is three live searches against a FHIR server.
    Without it, the same Bundle is loaded from disk so the example still runs.
    """
    if not os.getenv("MEDPLUM_CLIENT_ID"):
        return load_bundle(DATA / "prior_auth_chart.json")

    from healthchain.gateway import FHIRGateway
    from healthchain.gateway.clients import FHIRAuthConfig

    gateway = FHIRGateway()
    gateway.add_source(
        "medplum", FHIRAuthConfig.from_env("MEDPLUM").to_connection_string()
    )

    # One bundle holding everything the reviewer needs to make a decision.
    chart = create_bundle()
    for resource_type in (Condition, ServiceRequest, DocumentReference):
        results = gateway.search(
            resource_type, {"patient": PATIENT_ID}, source="medplum"
        )
        for resource in get_resources(results, resource_type):
            add_resource(chart, resource)

    return chart


# --- Step 2: code the free text ----------------------------------------------
# Clinical shorthand and catalog vocabulary rarely share a token. A code book
# says "Radiculopathy, lumbar region"; a physician types "lumbar radiculopathy,
# right L5 distribution". These two tables are the whole bridge, and they are the
# part you will tune for your own catalog.
SYNONYMS = {
    "mri": "mr",
    "magnetic": "mr",
    "resonance": "mr",
    "ct": "ct",
    "xray": "xr",
    "x-ray": "xr",
    "lumbosacral": "lumbar",
    "ivd": "disc",
    "herniation": "displacement",
    "hnp": "displacement",
}

# Words that carry clinical meaning but never appear in a catalog display:
# spinal levels, dermatome talk, laterality that ICD-10-CM does not encode for
# this family of codes. Dropping them is what lets retrieval find anything at all.
NOISE = {
    "a",
    "an",
    "and",
    "at",
    "distribution",
    "dermatome",
    "for",
    "in",
    "of",
    "or",
    "the",
    "to",
    "unspecified",
}
LEVEL = re.compile(r"^[clts]\d{1,2}(-[clts]?\d{1,2})?$")


def normalize(text: str) -> List[str]:
    """Free text to the tokens worth searching on."""
    words = re.findall(r"[a-z0-9-]+", text.lower())
    tokens = []
    for word in words:
        word = SYNONYMS.get(word, word)
        if word in NOISE or LEVEL.match(word) or len(word) == 1:
            continue
        if word not in tokens:
            tokens.append(word)
    return tokens


class RerankingCodeLookup:
    """Retrieve-then-rerank in front of any other ``TerminologyLookup``.

    Exact lookup answers "is this string in the catalog"; coding asks "which
    code does this text mean", which is a ranking problem. This wraps a strict
    lookup in the two stages that make it usable on real text: back off the query
    until candidates come back, then rank the candidates by how well they cover
    the query and how little they add to it.

    It implements ``TerminologyLookup``, so anything that takes a lookup takes
    this — and a hosted retrieval service or a trained reranker drops into the
    same seam without the caller changing.

    Args:
        base: The lookup to retrieve candidates from
        top_k: Maximum candidates to return
    """

    def __init__(self, base: TerminologyLookup, top_k: int = 5) -> None:
        self.base = base
        self.top_k = top_k

    def search(self, text: str, system: Optional[str] = None) -> List[Coding]:
        tokens = normalize(text)
        if not tokens:
            return []
        candidates = self._retrieve(tokens, system)
        return self._rerank(tokens, candidates)[: self.top_k]

    def _retrieve(self, tokens: List[str], system: Optional[str]) -> List[Coding]:
        """Query with every token, then progressively fewer, until hits appear.

        A strict AND-match over five tokens usually returns nothing. Dropping one
        token at a time turns a miss into a candidate set instead of a dead end.
        """
        seen, candidates = set(), []
        for width in range(len(tokens), 0, -1):
            for start in range(len(tokens) - width + 1):
                query = " ".join(tokens[start : start + width])
                for coding in self.base.search(query, system=system):
                    if coding.code not in seen:
                        seen.add(coding.code)
                        candidates.append(coding)
            if candidates:
                break
        return candidates

    def _rerank(self, tokens: List[str], candidates: List[Coding]) -> List[Coding]:
        """Rank by F1 between query tokens and display tokens.

        Recall alone promotes long displays that happen to contain the query;
        precision alone promotes stubs. The harmonic mean picks the code that
        says what the text says and nothing more — which is the specificity a
        payer is checking for.
        """

        def score(coding: Coding) -> float:
            display = set(normalize(coding.display))
            if not display:
                return 0.0
            overlap = len(set(tokens) & display)
            if not overlap:
                return 0.0
            recall = overlap / len(tokens)
            precision = overlap / len(display)
            return 2 * recall * precision / (recall + precision)

        scored = [(score(c), c) for c in candidates]
        return [c for value, c in sorted(scored, key=lambda p: -p[0]) if value > 0]


def code_resource(resource, lookup: TerminologyLookup, system: str):
    """Attach the top-ranked coding to a text-only ``code`` element.

    The candidates are returned, not hidden: coding is a suggestion until a human
    or a policy accepts it, and the runners-up are what a reviewer actually wants
    to see.
    """
    candidates = lookup.search(resource.code.text, system=system)
    if not candidates:
        return resource, []

    best = candidates[0]
    resource.code.coding = [
        {"system": best.system, "code": best.code, "display": best.display}
    ]
    return resource, candidates


# --- Step 3: apply the criteria ----------------------------------------------
RED_FLAGS = [
    "saddle anesthesia",
    "bowel or bladder dysfunction",
    "fever",
    "history of malignancy",
    "progressive motor deficit",
]
MIN_CONSERVATIVE_WEEKS = 6


def is_negated(note: str, phrase: str) -> bool:
    """Is this phrase preceded by a negation in the same clause?

    Notes document red flags precisely by ruling them out — "no saddle
    anesthesia, no bowel or bladder dysfunction". A substring match reads that as
    five red flags and denies a request that should sail through, which is why
    every real clinical NLP stack carries negation detection.
    """
    for match in re.finditer(re.escape(phrase), note, flags=re.I):
        clause = note[max(0, match.start() - 40) : match.start()]
        clause = clause.rsplit(".", 1)[-1]
        if not re.search(r"\b(no|not|denies|without|negative for)\b", clause, re.I):
            return False
    return True


def review(note: str) -> dict:
    """Check the request against the utilization-review criteria.

    The criteria here are a readable stand-in for the guideline your payer
    actually publishes (ACOEM, MTUS, InterQual). The shape is the point: every
    criterion carries the sentence it was decided on, so the packet can cite the
    chart rather than assert a conclusion.
    """
    weeks = 0
    duration = re.search(r"conservative care[^.]*?(\d+)\s*weeks", note, re.I | re.S)
    if duration:
        weeks = int(duration.group(1))

    flags = [
        flag
        for flag in RED_FLAGS
        if flag in note.lower() and not is_negated(note, flag)
    ]
    deficit = bool(
        re.search(r"straight leg raise positive|motor \d/5|numbness", note, re.I)
    )

    criteria = [
        {
            "name": f"Conservative care >= {MIN_CONSERVATIVE_WEEKS} weeks",
            "met": weeks >= MIN_CONSERVATIVE_WEEKS,
            "evidence": f"{weeks} weeks documented",
        },
        {
            "name": "Objective neurologic findings",
            "met": deficit,
            "evidence": "positive straight leg raise, motor deficit, or dermatomal numbness"
            if deficit
            else "none documented",
        },
        {
            "name": "No unaddressed red flags",
            "met": not flags,
            "evidence": "; ".join(flags) if flags else "red flags documented as absent",
        },
    ]
    return {"criteria": criteria, "meets_criteria": all(c["met"] for c in criteria)}


# --- Step 4: emit the packet as FHIR -----------------------------------------
def build_packet(condition, service_request, decision) -> "Bundle":  # noqa: F821
    """Assemble the authorization request the payer receives.

    Three resources, each doing one job: the coded ServiceRequest is what is being
    asked for, the Task is the authorization request itself, and the
    DocumentReference carries the justification. Everything is validated before it
    leaves — a rejected packet costs a week of appeals.
    """
    letter = render_letter(condition, service_request, decision)

    task = Task(
        status="requested",
        intent="order",
        priority="routine",
        code={"text": "Prior authorization request"},
        focus={"reference": f"ServiceRequest/{service_request.id}"},
        for_fhir={"reference": f"Patient/{PATIENT_ID}"},
        # The coded diagnosis, not the text the office typed — this is what the
        # payer adjudicates against.
        reasonCode=condition.code,
        reasonReference={"reference": f"Condition/{condition.id}"},
        authoredOn="2026-08-19T14:05:00Z",
    )
    justification = create_document_reference(
        data=letter,
        content_type="text/plain",
        description="Prior authorization justification",
        attachment_title="Medical necessity justification",
    )
    justification.subject = {"reference": f"Patient/{PATIENT_ID}"}
    task.input = [
        {
            "type": {"text": "Medical necessity justification"},
            "valueReference": {"reference": f"DocumentReference/{justification.id}"},
        }
    ]

    bundle = create_bundle()
    for resource in (service_request, condition, task, justification):
        report = validate_resource(resource)
        if not report.valid:
            for issue in report.issues:
                print(f"  INVALID {resource.__resource_type__}: {issue.diagnostics}")
            raise SystemExit("refusing to send an invalid packet")
        add_resource(bundle, resource)

    return bundle, letter


def render_letter(condition, service_request, decision) -> str:
    """Write the justification, citing the code and the criterion behind it."""
    dx = condition.code.coding[0]
    sv = service_request.code.coding[0]
    lines = [
        "MEDICAL NECESSITY JUSTIFICATION",
        "",
        f"Requested service: {sv.display} ({sv.code})",
        f"Diagnosis: {dx.display} ({dx.code}, ICD-10-CM)",
        "",
        "Criteria review:",
    ]
    for criterion in decision["criteria"]:
        mark = "MET" if criterion["met"] else "NOT MET"
        lines.append(f"  [{mark}] {criterion['name']} - {criterion['evidence']}")
    lines += [
        "",
        "Determination: request meets criteria for authorization."
        if decision["meets_criteria"]
        else "Determination: request does not meet criteria; additional documentation required.",
    ]
    return "\n".join(lines)


def write_back(bundle):
    """Persist the packet to the FHIR server the chart came from."""
    from healthchain.gateway import FHIRGateway
    from healthchain.gateway.clients import FHIRAuthConfig

    gateway = FHIRGateway()
    gateway.add_source(
        "medplum", FHIRAuthConfig.from_env("MEDPLUM").to_connection_string()
    )
    # The Condition and ServiceRequest came from this server: update them in place.
    for resource_type in ("Condition", "ServiceRequest"):
        for resource in get_resources(bundle, resource_type):
            gateway.update(resource, source="medplum")
            print(f"  updated {resource_type}/{resource.id}")

    # The justification and the Task are new. Create the justification first so
    # the Task can point at the ID the server gives it.
    justification = get_resources(bundle, "DocumentReference")[0]
    task = get_resources(bundle, "Task")[0]
    doc = gateway.create(justification, source="medplum")
    task.input[0].valueReference.reference = f"DocumentReference/{doc.id}"
    created = gateway.create(task, source="medplum")
    print(f"  created DocumentReference/{doc.id} and Task/{created.id}")


if __name__ == "__main__":
    chart = pull_chart()
    condition = get_resources(chart, "Condition")[0]
    service_request = get_resources(chart, "ServiceRequest")[0]
    note_attachment = get_resources(chart, "DocumentReference")[0]

    from healthchain.fhir import read_content_attachment

    note = read_content_attachment(note_attachment)[0]["data"]

    print("Pulled from FHIR — free text, no codes:\n")
    print(f"  Condition.code.text      {condition.code.text!r}")
    print(f"  ServiceRequest.code.text {service_request.code.text!r}")

    # The catalog is a site's own: ICD-10-CM for diagnoses, local order codes
    # for imaging. Same seam, whatever is behind it.
    catalog = json.loads((DATA / "prior_auth_catalog.json").read_text())
    lookup = RerankingCodeLookup(LocalCodeLookup(catalog=catalog))
    assert isinstance(lookup, TerminologyLookup)

    print("\n=== Coding ===\n")
    condition, dx_candidates = code_resource(condition, lookup, ICD10CM)
    service_request, sv_candidates = code_resource(
        service_request, lookup, IMAGING_CATALOG
    )
    for label, candidates in (("Diagnosis", dx_candidates), ("Service", sv_candidates)):
        print(f"  {label} candidates (ranked):")
        for rank, coding in enumerate(candidates, 1):
            mark = "<- selected" if rank == 1 else ""
            print(f"    {rank}. {coding.code:<14} {coding.display} {mark}")
        print()

    print("=== Criteria review ===\n")
    decision = review(note)
    for criterion in decision["criteria"]:
        mark = "MET" if criterion["met"] else "NOT MET"
        print(f"  [{mark:>7}] {criterion['name']}: {criterion['evidence']}")

    bundle, letter = build_packet(condition, service_request, decision)
    print(f"\n=== Packet ({len(bundle.entry)} validated resources) ===\n")
    print(letter)

    print("\nTask as FHIR:\n")
    task = get_resources(bundle, "Task")[0]
    print(task.model_dump_json(exclude_none=True, indent=2))

    if os.getenv("MEDPLUM_CLIENT_ID"):
        print("\n=== Writing the packet back to Medplum ===")
        write_back(bundle)
