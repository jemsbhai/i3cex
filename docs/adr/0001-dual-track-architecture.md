# ADR-0001: Dual-track architecture (I3C-EX and I4C)

- **Status**: Accepted
- **Date**: 2026-04-23
- **Deciders**: Muntaser Syed
- **Consulted**: Claude (Anthropic)
- **Informed**: Future collaborators, reviewers

## Context and Problem Statement

I3C has demonstrable gaps for edge AI and edge ML workloads: no wire-level
metadata or provenance, no Byzantine-resilient fusion primitives, no
quality-of-service negotiation, brittle real-time behaviour from
clock-stretching removal, HDR mode fragmentation, skeletal error
detection, zero native security, loose timestamping semantics, and a
request-response model poorly suited to continuous inference streams.

We must choose how to address these gaps. The two natural approaches
are (a) a backward-compatible extension layer that rides on existing
I3C hardware, or (b) a clean-slate logical protocol redesign sharing
the I3C physical layer. Both have merit. Neither dominates.

## Decision Drivers

- Time to first publishable evidence.
- Adoption friction for industry practitioners.
- Research impact and narrative strength.
- Risk diversification against the possibility that one approach fails.
- Available development bandwidth.

## Considered Options

- Option A: I3C-EX only (extension layer).
- Option B: I4C only (clean redesign).
- Option C: Both, sequentially — I3C-EX first, then I4C.

## Decision Outcome

Chosen option: **Option C — Both, sequentially**, because the extension
layer produces publishable results faster and generates empirical
evidence that strengthens the redesign case, while the redesign
captures the research upside that the extension layer alone would
leave on the table.

### Consequences

**Good:**

- Paper 1 (I3C-EX) can ship in roughly one year; Paper 2 (I4C) can
  follow in the subsequent year, creating a coherent two-paper arc.
- Paper 1 findings (especially framing benchmarks and sublayer
  complexity data) directly inform Paper 2 design.
- Risk is diversified: if I4C fails to gain traction, I3C-EX still
  delivers value and a publication.
- Two distinct publication venues are addressable (embedded/IoT for
  Paper 1; networking/systems/protocols for Paper 2).

**Bad:**

- Double the scope: two specifications, two codebases, two test
  suites, two publication efforts.
- Risk of scope creep; the extension layer must be disciplined to not
  accrete features that belong in the redesign.
- Maintenance burden extends indefinitely for whichever artefacts
  gain uptake.

## Pros and Cons of the Options

### Option A: I3C-EX only

Build only the backward-compatible extension layer.

- Good: Lower total scope; faster to initial publication.
- Good: Pragmatic, immediately useful to industry.
- Bad: Leaves the clean-redesign research contribution on the table.
- Bad: Extension layering has inherent limits (overhead, fragmentation
  risk, inelegant Byzantine fusion); these limits are themselves a
  publishable finding but only if there is a comparison point.

### Option B: I4C only

Build only the clean redesign.

- Good: Stronger single-paper research contribution.
- Good: Unified semantics from day one.
- Bad: Higher adoption friction; requires new silicon or FPGA.
- Bad: Longer time to first publication; chicken-and-egg adoption
  problem.
- Bad: Lacks empirical motivation for the redesign; reviewers will ask
  "why not extend I3C?" and we would have no data-driven answer.

### Option C: Both, sequentially

Build both in order: I3C-EX first, then I4C informed by what I3C-EX
taught us.

- Good: Strong narrative arc; Paper 2 cites Paper 1 as evidence.
- Good: Risk diversified across two distinct contributions.
- Bad: Roughly double the total work.
- Bad: Requires sustained discipline over multiple years.

## References

- `../../../README.md` — project overview.
- `../../../GOVERNANCE.md` — decision log entry for dual-track architecture.
- `../../../specs/I3CEX-0.1.0-draft.md` — draft specification.
- `../../../specs/I4C-0.0.1-placeholder.md` — I4C placeholder.
