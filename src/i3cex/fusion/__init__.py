"""EX-3: Byzantine fusion signalling sublayer.

EX-3 introduces wire-level primitives for Byzantine-resilient sensor
fusion. Redundant sensors can signal disagreement, controllers can
propagate voting tokens, and quorum state is visible at the protocol
layer rather than reconstructed at the application layer.

Planned capabilities:
    - Voting tokens for redundant sensor clusters.
    - Disagreement flags.
    - Quorum-state propagation.

Depends on: EX-2 QoS negotiation.

See :doc:`../../../specs/I3CEX-0.1.0-draft.md` section 6.3.

Status:
    Stub. Design begins after EX-2 stabilises. No implementation yet.
"""

from __future__ import annotations

__all__: list[str] = []
