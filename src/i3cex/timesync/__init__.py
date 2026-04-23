"""EX-4: Distributed timestamping sublayer.

EX-4 provides cross-bus temporal correlation using I3C's in-band
interrupt mechanism as a clock beacon substrate. Controllers federate
consensus on skew and drift, and all timestamps across a multi-bus
deployment become cross-comparable.

Planned capabilities:
    - Clock beacon frames via In-Band Interrupt (IBI).
    - Skew estimation across controllers.
    - Cross-bus timestamp federation.

Depends on: EX-3 Byzantine fusion signalling.

See :doc:`../../../specs/I3CEX-0.1.0-draft.md` section 6.4.

Status:
    Stub. Design begins after EX-3 stabilises. No implementation yet.
"""

from __future__ import annotations

__all__: list[str] = []
