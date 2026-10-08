# Prior Authorization: From FHIR Chart Pull to a Coded Request Packet

**Level:** Intermediate

A treating office asks for an MRI. The request lands in the EHR as free text — `"MRI lumbar spine without contrast"`, diagnosis `"lumbar radiculopathy, right L5 distribution"` — and the payer will not read free text. Somebody has to pull the chart, code the diagnosis and the requested service, check the request against the utilization-review criteria, and send back a packet that cites both. Today that somebody is usually a person with a browser and a code book.

This cookbook does the whole loop against FHIR: pull the chart from a live FHIR server, resolve the free text to codes through HealthChain's terminology seam, apply the criteria, and emit the decision as FHIR the payer can ingest.

Full working example: [cookbook/prior_auth_packet.py](https://github.com/healthchainai/HealthChain/tree/main/cookbook/prior_auth_packet.py)

---

## Clinical context

Prior authorization is where a lot of care stalls. The request itself is usually uncontroversial — an MRI after eight weeks of failed physical therapy is textbook — but it gets denied or delayed because the packet is incomplete: an unspecified diagnosis code, no documented conservative-care duration, no objective findings cited. The clinical decision was fine; the paperwork lost.

Two failure modes dominate, and both are engineering problems:

- **Under-specified codes.** `M54.50 Low back pain, unspecified` and `M54.16 Radiculopathy, lumbar region` describe the same patient to a clinician and different patients to a payer. Only one of them supports advanced imaging.
- **Findings that are in the note but not in the packet.** The straight leg raise result exists. Nobody carried it across.

Both are fixed by coding the free text properly and by citing the sentence each criterion was decided on — which is what this pipeline does.

---

## Quick Start

```bash
pip install healthchain
python cookbook/prior_auth_packet.py
```

Expected output:

```
Pulled from FHIR — free text, no codes:

  Condition.code.text      'lumbar radiculopathy, right L5 distribution'
  ServiceRequest.code.text 'MRI lumbar spine without contrast'

=== Coding ===

  Diagnosis candidates (ranked):
    1. M54.16         Radiculopathy, lumbar region <- selected
    2. M47.816        Spondylosis without myelopathy or radiculopathy, lumbar region
    3. M51.16         Intervertebral disc disorders with radiculopathy, lumbar region
    4. M54.15         Radiculopathy, thoracolumbar region

  Service candidates (ranked):
    1. IMG-MR-LSP-WO  MR lumbar spine without contrast <- selected
    2. IMG-MR-LSP-WWO MR lumbar spine with and without contrast

=== Criteria review ===

  [    MET] Conservative care >= 6 weeks: 8 weeks documented
  [    MET] Objective neurologic findings: positive straight leg raise, motor deficit, or dermatomal numbness
  [    MET] No unaddressed red flags: red flags documented as absent

=== Packet (4 validated resources) ===

MEDICAL NECESSITY JUSTIFICATION

Requested service: MR lumbar spine without contrast (IMG-MR-LSP-WO)
Diagnosis: Radiculopathy, lumbar region (M54.16, ICD-10-CM)

Criteria review:
  [MET] Conservative care >= 6 weeks - 8 weeks documented
  [MET] Objective neurologic findings - positive straight leg raise, motor deficit, or dermatomal numbness
  [MET] No unaddressed red flags - red flags documented as absent

Determination: request meets criteria for authorization.
```

The script ships a pre-baked chart pull, so it runs offline with no server and no credentials.

---

## How It Works

### Step 1: Pull the chart

The chart is three resources: the diagnosis, the requested service, and the note that justifies it. `FHIRGateway` fetches them from whichever EHR you point it at, and everything downstream works on typed resources rather than JSON.

```python
gateway = FHIRGateway()
gateway.add_source("medplum", FHIRAuthConfig.from_env("MEDPLUM").to_connection_string())

chart = create_bundle()
for resource_type in (Condition, ServiceRequest, DocumentReference):
    results = gateway.search(resource_type, {"patient": PATIENT_ID}, source="medplum")
    for resource in get_resources(results, resource_type):
        add_resource(chart, resource)
```

What comes back is what a text-entered order always looks like: a `code.text` and no `code.coding` at all.

```python
condition.code.text        # 'lumbar radiculopathy, right L5 distribution'
condition.code.coding      # None
```

### Step 2: Code the free text

HealthChain's terminology seam is one method — `search(text, system) -> list[Coding]`. `LocalCodeLookup` implements it over an in-memory catalog, and this cookbook loads a site catalog of ICD-10-CM diagnoses plus local imaging order codes.

Strict lookup is not enough on real text, though. The code book says `Radiculopathy, lumbar region`; the physician typed `lumbar radiculopathy, right L5 distribution`. An AND-match over those five tokens returns nothing. Coding is a ranking problem, so the cookbook wraps the strict lookup in the two stages that make it work — and, because `TerminologyLookup` is a protocol, the wrapper *is* a lookup:

```python
class RerankingCodeLookup:
    def search(self, text: str, system: str | None = None) -> list[Coding]:
        tokens = normalize(text)
        candidates = self._retrieve(tokens, system)   # back off until hits appear
        return self._rerank(tokens, candidates)[: self.top_k]

lookup = RerankingCodeLookup(LocalCodeLookup(catalog=catalog))
assert isinstance(lookup, TerminologyLookup)   # drops in anywhere a lookup goes
```

**Retrieve** queries with every token, then progressively fewer, until candidates come back — a miss becomes a candidate set instead of a dead end. **Rerank** scores each candidate by the F1 between query tokens and display tokens. Recall alone promotes long displays that happen to contain the query; precision alone promotes stubs. The harmonic mean picks the code that says what the text says and nothing more, which is exactly the specificity the payer is checking for.

The candidates are returned, not hidden. Coding is a suggestion until a human or a policy accepts it, and the runners-up are what a reviewer wants to see.

??? details "Swapping in a real terminology service"

    The demo catalog is a few dozen codes. Production needs the full ICD-10-CM release, and probably an embedding retriever with a trained cross-encoder reranker in place of token F1. Both live behind the same one-method protocol:

    ```python
    class HostedCodeLookup:
        def search(self, text: str, system: str | None = None) -> list[Coding]:
            hits = self.index.query(self.embed(text), filter={"system": system}, k=50)
            return [Coding(**h) for h in self.reranker.rank(text, hits)][:5]

    lookup = HostedCodeLookup()   # code_resource() does not change
    ```

    A FHIR `$lookup`/`$expand` endpoint or a hosted MCP terminology server fits the same seam.

!!! warning "CPT is licensed; this catalog is not"

    The procedure codes here are a site-local imaging catalog (`IMG-MR-LSP-WO`) because CPT is AMA-copyrighted and cannot ship in an open-source example. This is a real constraint on real prior-auth systems, not a shortcut — swap in your organization's licensed CPT or LOINC catalog and nothing else changes.

### Step 3: Apply the criteria

The criteria are a readable stand-in for the guideline your payer publishes (ACOEM, MTUS, InterQual). The shape is the point: every criterion carries the sentence it was decided on, so the packet cites the chart instead of asserting a conclusion.

One detail matters more than it looks. Notes document red flags precisely by ruling them out:

> No saddle anesthesia, no bowel or bladder dysfunction, no fever, no history of malignancy.

A substring match reads that as four red flags and denies a request that should sail through. Negation detection is not optional in clinical text:

```python
def is_negated(note: str, phrase: str) -> bool:
    for match in re.finditer(re.escape(phrase), note, flags=re.IGNORECASE):
        clause = note[max(0, match.start() - 40) : match.start()].rsplit(".", 1)[-1]
        if not re.search(r"\b(no|not|denies|without|negative for)\b", clause, re.IGNORECASE):
            return False
    return True
```

For anything beyond a demo, use a real negation model — [medspaCy](https://github.com/medspacy/medspacy)'s ConText implementation, or an LLM step behind the same interface.

### Step 4: Emit the packet as FHIR

Three resources, each doing one job: the coded `ServiceRequest` is what is being asked for, the `Task` is the authorization request itself, and the `DocumentReference` carries the justification letter. Nothing leaves without validating — a rejected packet costs a week of appeals.

```python
for resource in (service_request, condition, task, justification):
    report = validate_resource(resource)
    if not report.valid:
        raise SystemExit("refusing to send an invalid packet")
    add_resource(bundle, resource)
```

The `Task` carries the *coded* diagnosis, not the text the office typed:

```json
{
  "resourceType": "Task",
  "status": "requested",
  "intent": "order",
  "code": { "text": "Prior authorization request" },
  "focus": { "reference": "ServiceRequest/sr-mri-lumbar" },
  "for": { "reference": "Patient/wc-claimant-001" },
  "reasonCode": {
    "coding": [{
      "system": "http://hl7.org/fhir/sid/icd-10-cm",
      "code": "M54.16",
      "display": "Radiculopathy, lumbar region"
    }],
    "text": "lumbar radiculopathy, right L5 distribution"
  },
  "reasonReference": { "reference": "Condition/cond-lumbar-radic" }
}
```

??? details "Running it against a live FHIR server"

    Set `MEDPLUM_*` in a `.env` file and the same script pulls the chart from the server and writes the packet back:

    ```bash
    MEDPLUM_CLIENT_ID=...
    MEDPLUM_CLIENT_SECRET=...
    MEDPLUM_BASE_URL=https://api.medplum.com/fhir/R4/
    MEDPLUM_TOKEN_URL=https://api.medplum.com/oauth2/token
    ```

    Seed the chart, then export the patient ID Medplum prints:

    ```bash
    healthchain seed medplum cookbook/data/prior_auth_chart.json
    export PATIENT_ID=<the ID it printed>
    ```

    The write-back updates the Condition and ServiceRequest in place, and creates the justification and the Task that links to it. See [Working with FHIR Sandboxes](setup_fhir_sandboxes.md) for setup.

---

## What You've Built

| Stage | In | Out |
|---|---|---|
| Chart pull | Patient ID | `Condition`, `ServiceRequest`, `DocumentReference` |
| Coding | `code.text` free text | Ranked `Coding` candidates, top one attached |
| Criteria review | Progress note | Per-criterion verdict + the evidence for it |
| Packet | The above | Validated `ServiceRequest` + `Task` + `DocumentReference` |

A production version swaps three parts and keeps the shape: a full terminology service behind `TerminologyLookup`, a real negation model, and the payer's published criteria instead of the three here. The FHIR in and FHIR out stays as it is.

!!! tip "Next Steps"

    - Point it at your own catalog — `LocalCodeLookup(catalog=...)` takes any list of codings, so a site formulary or an order catalog works unchanged
    - Emit a Da Vinci PAS `Claim` alongside the `Task` if your payer accepts the profile
    - Return the determination as a CDS Hooks card so the request is checked while the order is still being written — see the [CDS Hooks gateway](../reference/gateway/cdshooks.md)
    - Go to production: scaffold with `healthchain new` and run with `healthchain serve`
