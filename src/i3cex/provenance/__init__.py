"""EX-5: Provenance and attestation sublayer.

EX-5 carries hash-chained source attribution, transform history, and
device attestation tokens alongside sensor data. Downstream inference
pipelines can verify which sensor produced a value, which processing
steps touched it, and whether the producing device was itself
attested.

Planned capabilities:
    - Hash-chain record per value.
    - Source attribution identifiers.
    - Transform history encoding.
    - Integration hooks for ETSI SSP attestation via I3C Interface for SSP.

Depends on: EX-4 distributed timestamping.

See :doc:`../../../specs/I3CEX-0.1.0-draft.md` section 6.5.

Status:
    Stub. Design begins after EX-4 stabilises. No implementation yet.
"""

from __future__ import annotations

__all__: list[str] = []
