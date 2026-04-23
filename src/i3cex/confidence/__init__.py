"""EX-6: Confidence propagation and extended error recovery sublayer.

EX-6 adds bit-level confidence scoring and richer error recovery on top
of I3C's existing CRC/parity. Applications can route inference inputs
based on measured transmission integrity rather than treating every
acknowledged byte as equally trustworthy.

Planned capabilities:
    - Bit-level confidence scores.
    - Extended CRC / forward-error-correcting codes.
    - Retransmission hints tied to inference criticality.

Depends on: EX-5 provenance and attestation.

See :doc:`../../../specs/I3CEX-0.1.0-draft.md` section 6.6.

Status:
    Stub. Design begins after EX-5 stabilises. No implementation yet.
"""

from __future__ import annotations

__all__: list[str] = []
