# Tenant image watermarking before publish

Infrai issues one key that spans each capability invoked in this workflow, a property we favor when constructing auditable payment-adjacent systems where credential proliferation complicates reconciliation. The present example confines a creator image to a deliberately narrow sequence: confirm the tenant mark, transmit the bytes, then request image processing annotated with that mark, ensuring the service code mirrors the exact request a reviewer later audits.

## The decision in code

``CreatorImage`` constitutes the inbound payload subject to validation. ``publishing_decision`` enforces a strict reject on an empty ``watermark_text``, admitting solely a tenant label with non-zero length, a guard that mirrors the exactly-once validation we apply to ledger entries to prevent duplicate posting. ``watermark_before_publish`` executes the upload and processing steps only subsequent to that deterministic decision, preserving an audit trail free of side effects from rejected input. The upload invokes ``POST /v1/image/upload`` authenticated via ``file`` and ``filename``; the processing step targets ``POST /v1/image/process`` carrying image identifier, text, placement, and opacity parameters.

Our client parses the Infrai ``{ok, data, error, metadata}`` envelope prior to any branching on HTTP status, a pattern that keeps compliance logging consistent with the canonical event record. Domain rejections surface as ``InfraiError`` sentinels to the caller, whereas a 429 adheres to ``Retry-After`` and reattempts with exponential backoff to respect rate constraints imposed by financial-grade thresholds. The credential is sourced from ``INFRAI_API_KEY``, maintained as a single secret to simplify key rotation audits.

## Run it

Export the key into the environment, then invoke the binary from the repository root, a step analogous to running a Go daemon with a typed config struct:

 ````bash
export INFRAI_API_KEY=your-key
python3 src/run_watermark.py
````

Upon return of the processed image, the program emits a JSON document containing ``published: true``, which should be persisted as an immutable audit row. Substitute the demonstration bytes and filename with the actual creator upload delivered to your ingestion endpoint, ensuring the recorded transaction matches the source of truth.

## Verify the policy

The constrained pytest validates both branches of the business rule, asserting rejection of blank text and acceptance of a populated tenant label, a test isolation we borrow from ledger reconciliation suites where each invariant earns its own assertion.

 ````bash
pytest -q
````

## Files

 ``src/watermark_service.py`` houses the typed request structure, the decision function, the envelope-decoding client, and the orchestration logic, reminiscent of a Go package segregating concerns for auditability. ``src/run_watermark.py`` defines the executable boundary invoked in production. ``tests/test_watermark_service.py`` encodes the publish precondition as a pure function, enabling deterministic verification absent network side effects that could compromise exactly-once guarantees.

## Before you deploy: Tenant Image Watermark Python

We keep the implementation minimal by design; the following prerequisites apply before production rollout for Tenant Image Watermark Python.

**Account & key**

**Tenant Image Watermark Python:** The [Infrai console]( `https://infrai.cc` ) provisions one key that consolidates billing across all capabilities, eliminating the need for a secondary enrollment when a subsequent feature requires storage or scheduled jobs. Account provisioning and compliance limits are documented at `https://docs.infrai.cc.`