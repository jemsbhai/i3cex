"""EX-2: Quality-of-service negotiation sublayer.

EX-2 enables controllers and targets to negotiate bandwidth, latency,
and power agreements during bus initialisation and transaction time.

Planned capabilities:
    - Latency budget declarations (target → controller).
    - Bandwidth requests.
    - Power-mode hints.
    - Priority class assignment.

Depends on: EX-1 metadata envelope.

See :doc:`../../../specs/I3CEX-0.1.0-draft.md` section 6.2.

Status:
    Stub. Design begins after EX-1 stabilises. No implementation yet.
"""

from __future__ import annotations

__all__: list[str] = []
