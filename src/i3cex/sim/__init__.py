"""Pure-Python behavioural simulator for I3C and I3C-EX.

This simulator models I3C SDR-mode bus behaviour at a level sufficient
for protocol logic development and integration testing. It is **not**
cycle-accurate; for cycle-accurate validation, use the cocotb
cosimulation harness (``tests/cosim/``) against the
chipsalliance/i3c-core RTL.

Design goals:
    - Fast enough for inner-loop TDD (milliseconds per test).
    - Deterministic and reproducible (no wall-clock dependencies).
    - Faithful to I3C SDR semantics: DAA, CCCs, IBI, arbitration.
    - Extensible to simulate failure modes (bit flips, bus stalls,
      malicious targets) for Byzantine fusion testing.

This simulator is intentionally distinct from the cosimulation layer.
Pure-Python lets us iterate on protocol logic without the overhead of
RTL compilation and Verilator execution. Cycle-accurate claims in
publications will come from the cosim harness.

See :doc:`../../../GOVERNANCE.md` "Simulation strategy" decision log.

Status:
    Stub. Initial simulator implementation begins alongside EX-1.
"""

from __future__ import annotations

__all__: list[str] = []
