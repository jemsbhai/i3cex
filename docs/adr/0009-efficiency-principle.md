# ADR-0009: Efficiency Principle — every feature must offset its cost

- **Status**: Accepted
- **Date**: 2026-04-23
- **Deciders**: Muntaser Syed
- **Consulted**: Claude (Anthropic)
- **Informed**: Future collaborators, reviewers, paper reviewers

## Context and Problem Statement

I3C-EX adds functionality to I3C, and every added functionality has a
cost — bytes on the wire, cycles in the decoder, state in the
controller, or complexity in the specification. Without a principled
approach, extension-layer design tends toward feature accretion where
each addition looks locally justified but the cumulative cost erodes
the protocol's efficiency below the point where the extension layer
is worth adopting.

The project needs an explicit discipline for controlling this cost.
This discipline must be:
- Quantifiable: reasoning in terms of bytes and cycles, not feelings.
- Forcing: it must cause designers to apply optimisation techniques
  up-front, not retrofit them later.
- Reviewable: publishable research reviewers should be able to
  evaluate the trade-off analysis in each sublayer design.

## Decision Drivers

- Publishable credibility: a paper claiming "extension layer with
  minimal overhead" must back that claim with per-feature analysis.
- Long-term spec health: accretion is easier than subtraction.
  Prevention at the design stage is cheaper than retrofit.
- Contributor guidance: future contributors need a clear standard for
  what constitutes an acceptable feature addition.

## Considered Options

- Option 1: No formal principle; rely on case-by-case judgement.
- Option 2: A publishable Efficiency Principle with mandatory
  Overhead Analysis sections in every sublayer specification.
- Option 3: Numeric efficiency budgets (e.g., "no sublayer may add
  more than 4 bytes per frame") enforced at spec-review time.

## Decision Outcome

Chosen option: **Option 2 — formal Efficiency Principle with
mandatory Overhead Analysis sections**.

### The Efficiency Principle (normative)

> Every I3C-EX sublayer specification MUST include an "Overhead
> Analysis" section documenting:
>
> 1. **Worst-case bytes added per frame** by the sublayer, broken
>    down by record type.
> 2. **Parse complexity impact**, stated in terms of cyclomatic
>    complexity delta and worst-case cycles on a representative
>    constrained microcontroller (Cortex-M0 reference target).
> 3. **At least one bit-packing or amortisation technique applied**
>    to the sublayer's wire representation. Sublayers whose wire
>    representation uses byte-aligned fields where fewer bits would
>    suffice MUST document why the byte alignment was chosen.
> 4. **An explicit trade-off statement** in the form:
>    *"This sublayer adds X bytes to typical frames and Y cycles to
>    the decoder. The benefit is Z. This trade-off is justified
>    because W."*
>
> Sublayer specifications that do not satisfy this principle MUST
> NOT progress beyond `-draft` status.

### Sanctioned optimisation techniques

The following techniques are encouraged and documented as available
tools:

1. **Bit-packing within sublayer payloads.** Pack related fields to
   the bit level. Zero parse latency cost on modern platforms.
   *Required consideration for every sublayer.*

2. **Reserved-bit forward-compatibility** (per ADR-0005 and ADR-0006).
   Reserve high bits or reserved field values for future extensions.
   Decoders reject reserved values as malformed.

3. **Sublayer-internal delta encoding** for streaming data (e.g.,
   EX-6 confidence scores over time). Stateful and sublayer-specific;
   does not affect the framing layer.

4. **Schema template negotiation** as a v0.2+ extension path. Pre-
   register the technique now; defer implementation until evidence
   supports the complexity cost.

### Explicitly unsanctioned techniques at v0.1

The following techniques are documented as considered-and-rejected
to prevent accidental re-adoption:

1. **Variable-length (varint) length encoding** (rejected in
   ADR-0006). Adds decoder complexity incompatible with the framing
   bakeoff's fairness requirement.

2. **Combo Types encoding multiple sublayers in one record**.
   Explodes the Type-value space; breaks forward compatibility;
   breaks sublayer skipping.

3. **Implicit-length Types** (Type value implies a fixed Length).
   Creates two parallel TLV formats; contradicts ADR-0006's
   single-encoding rule.

4. **Protocol-level record nesting** (rejected in ADR-0007).
   Deferred to a future version via the Type 0xFE reservation.

### Integration with specification process

- The Efficiency Principle is recorded as a normative section in
  `GOVERNANCE.md`.
- Every sublayer specification (sections 6.1 through 6.6 of
  `I3CEX-*.md`) MUST include an "Overhead Analysis" subsection
  before graduating from `-draft` to `-rc1`.
- Paper 1 will cite this principle as a research contribution in its
  own right — it is not merely internal discipline but a publishable
  position on extension-layer design methodology.

### Consequences

**Good:**

- Every feature addition is forced through a quantitative trade-off
  analysis, preventing accretion.
- The project has a publishable position on principled extension-
  layer design, useful for Paper 1's contributions list.
- Future contributors have a clear standard for feature proposals.
- The Overhead Analysis sections themselves become useful
  documentation for practitioners evaluating adoption.
- The sanctioned/unsanctioned technique lists prevent re-
  relitigating past decisions.

**Bad:**

- Design work slows down at the specification stage; every sublayer
  must document overhead before it can be implemented.
- Some sublayers may have overheads that look high when analysed
  honestly but are unavoidable (e.g., provenance hash chains are
  inherently costly). The principle does not forbid high-overhead
  sublayers; it forbids undocumented high-overhead sublayers.
  Authors must justify.
- Adopting the principle now is a commitment. Future pressure to
  "just add a feature quickly" must be resisted, which requires
  sustained discipline.

## Pros and Cons of the Options

### Option 1: No formal principle

- Good: Maximum speed of iteration.
- Bad: No forcing function against accretion.
- Bad: Nothing to cite in Paper 1 as a methodological contribution.
- Bad: Future contributors have no standard.

### Option 2: Formal principle with Overhead Analysis

- Good: Quantitative, reviewable, publishable.
- Good: Forcing function applies at the specification stage, before
  cost is baked in.
- Good: Integrates cleanly with the existing ADR and governance
  discipline.
- Bad: Slows down specification work by requiring analysis up-front.

### Option 3: Numeric efficiency budgets

- Good: Hardest possible enforcement.
- Good: No judgement calls; the budget is a line in the sand.
- Bad: Arbitrary budgets invite gaming (e.g., "my sublayer splits
  into three records to fit three 4-byte budgets").
- Bad: Legitimately heavy sublayers (provenance hash chains) get
  locked out.
- Bad: Overly rigid for a research project still discovering its
  own workload characteristics.

## References

- `../../../GOVERNANCE.md` — normative Efficiency Principle section
  (added in the same commit as this ADR).
- [`./0006-tlv-length-encoding.md`](./0006-tlv-length-encoding.md)
  — decision that applied the "no added decoder complexity"
  discipline.
- [`./0007-tlv-nesting-deferred.md`](./0007-tlv-nesting-deferred.md)
  — decision that applied the "defer complexity until evidence
  supports it" discipline.
- [`./0008-tlv-max-block-size.md`](./0008-tlv-max-block-size.md)
  — decision whose latency analysis establishes the quantitative
  style this principle formalises.
