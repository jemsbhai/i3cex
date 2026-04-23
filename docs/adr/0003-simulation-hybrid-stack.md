# ADR-0003: Hybrid simulation stack

- **Status**: Accepted
- **Date**: 2026-04-23
- **Deciders**: Muntaser Syed
- **Consulted**: Claude (Anthropic)
- **Informed**: Future collaborators, reviewers

## Context and Problem Statement

The project needs a simulation strategy that supports both fast
iteration on protocol logic and publication-credible cycle-accurate
validation. Top-tier conferences (NSDI, SenSys, SIGCOMM, EuroSys,
ASPLOS) demand cycle-accurate baselines, realistic workloads, and
reproducible artefacts. A pure-Python behavioural simulator satisfies
the first requirement but not the second; a pure-RTL cosimulation
satisfies the second but is too slow for inner-loop TDD.

## Decision Drivers

- TDD requires millisecond-scale test feedback.
- Reviewers demand cycle-accurate numbers.
- Reproducibility requires open-source, permissively licensed tools.
- Windows development must be supported for the pure-Python layer.
- Linux/WSL2 is acceptable for the cosimulation layer.

## Considered Options

- Option A: Pure Python behavioural simulator only.
- Option B: cocotb + Verilator + chipsalliance/i3c-core RTL only.
- Option C: Hybrid — Python for iteration, RTL cosim for validation.

## Decision Outcome

Chosen option: **Option C — hybrid stack**, because it is the only
option that satisfies both fast TDD feedback and publication-credible
cycle accuracy.

The three layers:

1. **Pure Python behavioural simulator** (`i3cex.sim`) for fast TDD.
2. **cocotb + Verilator against chipsalliance/i3c-core** for
   cycle-accurate validation. Apache-2.0, actively maintained, CHIPS
   Alliance-backed.
3. **FPGA deployment** (Paper 2 era) on Digilent Cora Z7 or Terasic
   DE10-Nano, per the MDPI open-source I3C controller precedent.

### Consequences

**Good:**

- Inner-loop TDD runs on Windows natively; no WSL2 required for most
  development.
- Cycle-accurate numbers for publication come from actual Apache-2.0
  industry-reference RTL, not a toy simulator.
- FPGA deployment path exists for Paper 2 without redesign.

**Bad:**

- Two simulation layers must be maintained in lockstep.
- Cosimulation dependencies (Verilator 5.012+, Verible, Icarus 12.0+)
  are a heavy install.
- cocotb introduces Python-simulator boundary overhead that slows
  mass Monte Carlo fuzzing.

## Pros and Cons of the Options

### Option A: Pure Python only

- Good: Simple, fast, cross-platform.
- Good: Zero external tooling dependencies.
- Bad: Not cycle-accurate; reviewers will discount latency and jitter
  numbers.
- Bad: Any claim about timing behaviour must be independently
  validated anyway, so this option just defers the cosim problem.

### Option B: Cosim only

- Good: Publication-credible from day one.
- Good: Directly validates against industry-reference RTL.
- Bad: Simulation runs are seconds to minutes, not milliseconds;
  inner-loop TDD is impractical.
- Bad: Linux/WSL2 only; Windows development is blocked.
- Bad: Dependency install is heavy; onboarding friction is high.

### Option C: Hybrid

- Good: Best of both — Python for speed, RTL for credibility.
- Good: Clean separation of concerns: behavioural semantics in
  Python, timing semantics in RTL.
- Bad: Two layers to maintain.
- Bad: Requires discipline to keep the two in semantic sync.

## References

- `../../../GOVERNANCE.md` — simulation strategy decision log entry.
- [chipsalliance/i3c-core](https://github.com/chipsalliance/i3c-core) —
  Apache-2.0 reference RTL.
- Open-Source FPGA Implementation of an I3C Controller, MDPI 2025.
- [cocotb documentation](https://www.cocotb.org/)
- [Verilator project](https://www.veripool.org/verilator/)
