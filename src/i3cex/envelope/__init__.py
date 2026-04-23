"""EX-1: Metadata envelope sublayer.

The metadata envelope is the foundational I3C-EX sublayer. It carries a
minimal, always-useful set of auxiliary data alongside each I3C
transaction:

- Sequence number (monotonic per controller/target pair)
- Timestamp (local-clock at send time)
- Sublayer presence flags (which higher sublayers ride on this frame)
- Checksum

Every higher sublayer (QoS, fusion, timestamping, provenance,
confidence) rides on top of the envelope. A device supporting any
EX-N level MUST also support EX-1.

See :doc:`../../../specs/I3CEX-0.1.0-draft.md` section 6.1.

Status:
    Skeleton. Detailed bit-level layout is pending the framing strategy
    decision (preamble vs TLV). No implementation yet.
"""

from __future__ import annotations

__all__: list[str] = []
