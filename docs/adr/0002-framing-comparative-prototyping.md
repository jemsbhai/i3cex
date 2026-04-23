# ADR-0002: Comparative prototyping of framing strategies

- **Status**: Accepted
- **Date**: 2026-04-23
- **Deciders**: Muntaser Syed
- **Consulted**: Claude (Anthropic)
- **Informed**: Future collaborators, reviewers

## Context and Problem Statement

I3C-EX metadata must be carried on the wire somehow. Two natural
strategies exist: a reserved preamble byte that prefaces the I3C
payload, or Type-Length-Value (TLV) records appended to or embedded
within the payload. Each has different trade-offs on overhead, parse
complexity, extensibility, worst-case latency, and legacy-safety
behaviour.

Choosing blindly based on intuition would be inappropriate for a
publication targeting a top-tier venue, and the comparison itself is
publishable material.

## Decision Drivers

- Empirical rigour: picking a framing strategy without benchmarks is
  insufficient for a top-tier publication.
- The comparison itself is a publishable contribution (negative
  results disclosure).
- Downstream design work on EX-1 through EX-6 depends on the framing
  format, so the decision must be made early but defensibly.

## Considered Options

- Option A: Pick preamble framing by intuition.
- Option B: Pick TLV framing by intuition.
- Option C: Implement both; measure; select the winner on evidence.

## Decision Outcome

Chosen option: **Option C — implement both, benchmark, select on
evidence**, because empirical rigour matters for the publication and
the comparison produces its own research contribution.

### Consequences

**Good:**

- Paper 1 includes a defensible framing-strategy comparison that
  reviewers cannot easily attack.
- The losing strategy's data is preserved as a negative result,
  aligned with the project's publication-ethics commitments.
- Implementation of both strategies exercises the abstractions in the
  package and surfaces design problems early.

**Bad:**

- Roughly double the framing-layer implementation effort.
- Either strategy's TDD tests must be maintained until the
  comparison is published.
- Test-vector authoring must cover both strategies.

## Pros and Cons of the Options

### Option A: Pick preamble framing by intuition

- Good: Faster initial implementation.
- Bad: Reviewers will reasonably ask "why not TLV?" without data.
- Bad: Intuition is a poor guide for wire-format decisions; real
  workloads often surprise designers.

### Option B: Pick TLV framing by intuition

- Good: Matches the extensibility pattern used by many modern
  protocols (e.g., CBOR, Protobuf tags).
- Bad: Higher per-frame overhead than preamble; this may be material
  on low-bandwidth I3C links.
- Bad: Same review objection as Option A.

### Option C: Implement both; measure; select the winner

- Good: Produces data, not opinion.
- Good: Comparison is a publishable contribution.
- Good: Forces the package to cleanly separate "framing strategy"
  from "envelope semantics," which is architecturally healthy.
- Bad: Double implementation and test-authoring effort for the
  framing layer.

## References

- `../../../specs/I3CEX-0.1.0-draft.md` section 5 — framing comparison
  criteria.
- `../../../GOVERNANCE.md` — decision log entry for framing strategy.
- `../../../../i3cex/src/i3cex/framing/preamble.py` — Candidate A.
- `../../../../i3cex/src/i3cex/framing/tlv.py` — Candidate B.
