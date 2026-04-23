"""Candidate B: Type-Length-Value (TLV) framing for I3C-EX.

This module implements one of two candidate framing strategies under
comparative evaluation per :doc:`../../../specs/I3CEX-0.1.0-draft.md`
section 5.2.

Strategy overview
-----------------
Extension data is encoded as a sequence of TLV records appended to or
embedded within the I3C payload. The tentative record layout is:

- Byte 0:     Type (sublayer identifier + record subtype).
- Byte 1:     Length (bytes of Value that follow).
- Bytes 2..:  Value (sublayer-specific payload).

TLV records may appear in sequence. Nested TLVs (a record whose Value
contains further TLVs) are supported subject to per-record maximum
length constraints.

Trade-offs vs preamble (Candidate A)
------------------------------------
TLV framing:
    + Unlimited extensibility; new sublayers and subtypes do not
      consume reserved bits.
    + Self-delimiting records allow skipping unknown types.
    - Higher per-frame overhead (minimum 2 bytes per record).
    - More complex decoder state machine.
    - Potentially variable decode latency depending on record count.

See :doc:`../../../GOVERNANCE.md` decision log: "Framing strategy —
comparative prototyping."

Status
------
Skeleton. The actual encoder, decoder, and invariants land via TDD.
Every function below raises ``NotImplementedError`` until the
corresponding test is written.
"""

from __future__ import annotations

__all__: list[str] = []
