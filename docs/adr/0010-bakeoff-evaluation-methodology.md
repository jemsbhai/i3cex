# ADR-0010: Bakeoff evaluation methodology

- **Status**: Accepted
- **Date**: 2026-04-24
- **Deciders**: Muntaser Syed
- **Consulted**: Claude (Anthropic)
- **Informed**: Future collaborators, reviewers

## Context and Problem Statement

ADR-0002 committed the project to comparative prototyping of two
framing strategies (preamble byte and TLV) and to selecting the winner
on evidence. That ADR did not, however, specify *how* the evidence
would be gathered — which axes of comparison, at what depth, under
what measurement methodology, and against what rigor standard.

Spec `I3CEX-0.1.0-draft.md` section 5.3 enumerates six axes of
comparison: wire overhead, parse complexity, extensibility, legacy
safety, worst-case latency impact, and throughput impact. The question
now is whether Paper 1 evaluates all six, whether each axis is
measured at the same level of rigor, and how per-axis methodology is
organised across ADRs.

Paper 1 targets a top-tier embedded systems / IoT venue. Reviewers at
that tier will probe methodology aggressively. A bakeoff that
evaluates some axes rigorously and handwaves others produces a weaker
paper than one that covers all six consistently, even if the full
six-axis treatment is more work.

## Decision Drivers

- Scientific rigor over convenience: the project's stated standard is
  a stringent reviewer (NeurIPS-level) who will reject shallow or
  ad-hoc methodology.
- Publishability: Paper 1's central bakeoff result must withstand
  review at a top-tier venue.
- Pre-registration discipline: methodology choices are fixed before
  measurement, via ADRs, not discovered retroactively.
- Per-axis methodology can be complex. Bundling all six axes into a
  single ADR produces an unwieldy document; fragmenting into too
  many ADRs loses the meta-framework.
- Cross-cutting rules (e.g., Python-plus-C side-by-side measurement)
  apply across multiple axes and warrant their own ADR rather than
  being buried inside per-axis documents.

## Considered Options

- Option A: Evaluate a subset of axes in Paper 1, defer the rest to
  Paper 2.
- Option B: Evaluate all six axes in Paper 1 with uniform rigor, one
  dedicated ADR per axis, plus a meta-ADR (this document) and
  cross-cutting rule ADRs.
- Option C: Evaluate all six axes in Paper 1, but capture all
  methodology in a single large ADR.

## Decision Outcome

Chosen option: **Option B — all six axes evaluated in Paper 1 with
uniform rigor, organised across a meta-ADR (this one), a cross-cutting
Python-plus-C rule ADR (ADR-0011), and per-axis methodology ADRs
(ADR-0012 onward)**, because covering all six axes is required to
meet the project's rigor standard, and the ADR split produces
auditable, independently-supersedable decisions.

### Consequences

**Good:**

- Paper 1's bakeoff is defensible across the full six-axis
  comparison framework defined in spec section 5.3.
- Per-axis methodology decisions are documented in focused ADRs that
  reviewers can audit independently.
- Cross-cutting rules (Python-plus-C measurement) are documented
  once in ADR-0011 rather than repeated across per-axis ADRs.
- Meta-framework decisions (this ADR) anchor the bakeoff against
  drift during per-axis methodology work.

**Bad:**

- Significantly more methodology work before implementation begins.
- Five or more ADRs to be written before benchmark harness
  implementation starts.
- Risk of inconsistency between per-axis ADRs if downstream
  decisions invalidate upstream framing; mitigated by the
  superseding-ADR mechanism.

## Pros and Cons of the Options

### Option A: Evaluate a subset of axes in Paper 1

- Good: Less methodology work upfront; faster path to implementation.
- Bad: Reviewers will ask why omitted axes were omitted; "deferred to
  Paper 2" is a weak defence for axes the spec itself enumerates as
  evaluation criteria.
- Bad: Bakeoff conclusion is narrower; a framing that wins on
  selected axes may lose on omitted ones, and the paper cannot
  claim otherwise.

### Option B: Evaluate all six axes in Paper 1, ADR-split methodology

- Good: Matches the project's rigor standard; reviewers cannot
  object on coverage grounds.
- Good: ADR split keeps each document focused and independently
  supersedable.
- Good: Cross-cutting rules (ADR-0011) avoid duplication across
  per-axis ADRs.
- Bad: Substantial upfront methodology work (this ADR plus ADR-0011
  plus per-axis ADRs) before any implementation.

### Option C: Evaluate all six axes in a single monolithic ADR

- Good: Single-document simplicity; all methodology in one place.
- Bad: Document grows unwieldy (likely 30+ pages) and cross-reference
  becomes awkward.
- Bad: Any revision to any axis's methodology requires superseding
  the entire ADR, losing granularity of the decision trail.
- Bad: Cross-cutting rules are buried rather than surfaced.

## Scope of this ADR

This ADR establishes the meta-framework. It does not specify per-axis
methodology; those live in downstream ADRs.

The six axes from `I3CEX-0.1.0-draft.md` section 5.3 are:

1. Wire overhead.
2. Parse complexity.
3. Extensibility.
4. Legacy safety.
5. Worst-case latency impact.
6. Throughput impact.

Paper 1 evaluates all six. Per-axis methodology is documented in
dedicated ADRs:

- Axis 1 (wire overhead): documented in a forthcoming ADR.
- Axis 2 (parse complexity): documented in a forthcoming ADR.
- Axis 3 (extensibility): documented in ADR-0012 (taxonomy), ADR-0013
  (coverage strategy), and ADR-0014 (per-scenario measurement set).
- Axis 4 (legacy safety): documented in a forthcoming ADR.
- Axis 5 (worst-case latency impact): documented in a forthcoming
  ADR.
- Axis 6 (throughput impact): documented in a forthcoming ADR.

Cross-cutting rules that apply across multiple axes are documented in
their own ADRs. The first is:

- ADR-0011: Python-plus-C side-by-side measurement for runtime axes.

Additional cross-cutting ADRs may be added as methodology work on
axes 1, 2, 4, 5, 6 surfaces further cross-cutting concerns.

## Rigor posture

The project's governing standard is a stringent reviewer (NeurIPS-
level). The methodology captured across this ADR family is chosen to
withstand that standard. Where a per-axis methodology decision
involves a trade-off between rigor and engineering cost, the rigorous
option is chosen unless the cost is demonstrably infeasible for
Paper 1's timeline. Infeasibility claims themselves require
justification; they are not accepted as self-evident.

## References

- `../../specs/I3CEX-0.1.0-draft.md` section 5.3 — six axes of
  framing comparison.
- `./0002-framing-comparative-prototyping.md` — commitment to
  comparative prototyping.
- `./0009-efficiency-principle.md` — normative Efficiency Principle
  that shapes some axis 1 and axis 2 measurements.
- `../../GOVERNANCE.md` — project-level decision log.
- ADR-0011 (forthcoming) — Python-plus-C side-by-side measurement
  rule.
- ADR-0012, ADR-0013, ADR-0014 (forthcoming) — axis 3 methodology.
