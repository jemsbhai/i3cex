# ADR-0012: Extensibility scenario taxonomy

- **Status**: Proposed
- **Date**: 2026-07-16
- **Deciders**: Project maintainer
- **Consulted**: RFC 6709 and RFC 9170
- **Informed**: Future collaborators, artifact evaluators, and paper reviewers

## Context and Problem Statement

Spec section 5.3 names “effort to add a new sublayer or record type” as the
extensibility axis. That phrase is too narrow and permits cherry-picking: a
framing can make one kind of addition easy while failing under version skew,
unknown critical data, length growth, or identifier exhaustion.

The bakeoff needs a finite, framing-neutral taxonomy fixed before either
candidate is extended. The taxonomy must exercise the extension mechanisms
that a long-lived content protocol is expected to need without testing MIPI
base-bus mechanisms that are identical for both candidates.

## Decision Drivers

- Cover feature, schema, size, structure, and version evolution.
- Include safe behavior under old/new implementation skew.
- Exercise both ordinary growth and boundary exhaustion.
- Avoid scenarios tailored to the mechanics of either preamble or TLV.
- Keep the complete canonical catalog small enough for isolated implementations.
- Separate framing extensibility from SETBUSCON, CCC, MDB, and I3C conformance.

## Considered Options

- Option A: Measure only “add EX-7” and “add one TLV Type.”
- Option B: Let implementers select realistic extensions during development.
- Option C: Freeze a dimensional taxonomy and twelve canonical scenarios before
  implementation.

## Decision Outcome

Chosen option: **Option C — a dimensional taxonomy with twelve canonical
scenarios**, because it provides auditable coverage while remaining feasible to
implement as isolated experiments.

### Consequences

**Good:**

- Neither candidate can win by demonstrating only its natural extension path.
- Version skew, unknown elements, and namespace pressure become first-class.
- Scenario IDs provide stable keys across vectors, code, raw data, and paper
  tables.

**Bad:**

- Some scenarios intentionally force a candidate into clean rejection or
  “unsupported”; not every case yields a working extension.
- The catalog evaluates the current framing candidates, not all imaginable
  future I3C-EX control-plane designs.

## Scope boundary

The unit under test begins at the first byte of negotiated I3C-EX content and
ends at the last byte of that content. SETBUSCON selection, numeric CCC or MDB
assignment, Private SDR transfer mechanics, SETMRL/SETMWL signaling, DAA, IBI
transport, and electrical timing are excluded because they are base-protocol or
shared integration concerns.

The applicable directional payload budget is still an input constraint. A
scenario that needs more bytes than the base budget is recorded as infeasible
for that budget; the harness MUST NOT fragment it silently unless the scenario
explicitly tests framing-level continuation.

## Taxonomy dimensions

Every canonical scenario is tagged across five dimensions.

### A. Evolution locus

- **Feature set**: add or compose an I3C-EX sublayer.
- **Record set**: add a semantic element inside an existing sublayer.
- **Record schema**: evolve fields within a known semantic element.
- **Size encoding**: cross a length or block-size boundary.
- **Structure**: add grouping, nesting, or continuation.
- **Namespace/version**: consume or evolve a bounded identifier/version space.

### B. Requirement level

- **Optional/ignorable**: an old receiver may continue without the extension.
- **Critical**: correct interpretation requires understanding the extension.
- **Negotiated**: use is legal only after both endpoints advertise support.

### C. Deployment skew

- baseline sender to baseline receiver;
- baseline sender to extended receiver;
- extended sender to baseline receiver; and
- extended sender to extended receiver.

### D. Composition pressure

- one extension in isolation;
- multiple known extensions;
- known and unknown extensions together; and
- two independently developed extensions together.

### E. Boundary position

- ordinary interior value;
- last currently valid value;
- first value beyond the current boundary; and
- exhausted primary namespace.

## Canonical scenario catalog

The following scenarios are mandatory and immutable for this bakeoff. A later
ADR may supersede the taxonomy, but an implementation MUST NOT rename, remove,
or substitute a scenario after measurements begin.

| ID | Scenario | Primary dimensions | Required extension behavior |
|---|---|---|---|
| X01 | Add the next monotonic sublayer after EX-6 | Feature set; negotiated | Represent EX-7 without changing meanings of EX-0 through EX-6 |
| X02 | Activate a sparse sublayer set | Feature set; composition | Represent EX-1 plus EX-4 without implying EX-2 or EX-3 |
| X03 | Add an optional record subtype inside EX-1 | Record set; optional | Old receivers preserve known content and safely ignore the new subtype |
| X04 | Add a critical record subtype inside EX-1 | Record set; critical | Old receivers fail closed or negotiate fallback; silent ignore is forbidden |
| X05 | Append an optional field to a known EX-1 record | Record schema; optional | Old and new parsers retain an unambiguous common prefix |
| X06 | Mix one known and one unknown optional element | Composition; optional | The known element remains usable and boundaries remain synchronized |
| X07 | Grow one value from 127 to 128 bytes | Size encoding; boundary | Cross the current TLV single-value boundary without ambiguous parsing |
| X08 | Grow one content block from 4096 to 4097 bytes | Size encoding; boundary | Respect a raised I3C-EX cap and the still-stricter base directional budget |
| X09 | Represent one parent with two child elements | Structure; negotiated | Preserve child boundaries and deterministic parent association |
| X10 | Carry two independently allocated extensions | Composition; namespace | Avoid identifier collision and preserve both extensions' semantics |
| X11 | Introduce a second framing revision | Namespace/version; skew | Define baseline/extended sender-receiver behavior in all four pairings |
| X12 | Exhaust the candidate's primary extension namespace | Namespace; exhaustion | Provide a documented continuation path or report clean exhaustion |

## Scenario fixtures

Each scenario specification in the experiment manifest MUST contain:

- a framing-neutral semantic input and expected semantic output;
- its optional, critical, or negotiated requirement level;
- the four expected version-pair outcomes before implementation;
- minimum, typical, and boundary payload fixtures where applicable;
- the applicable base directional payload budget;
- identifiers consumed by the scenario;
- a prohibition list describing outcomes that would be unsafe; and
- a rationale tying every candidate-specific encoding to the same semantics.

Candidate-specific encodings MAY differ, but candidate-specific semantics MUST
NOT. An extension that can be represented only by changing the common semantic
fixture is recorded as unsupported for that candidate.

## Excluded scenarios

The following are important but belong to other axes or later work:

- random corruption, truncation, and hostile lengths: legacy-safety axis;
- cryptographic algorithm agility: EX-5 security design;
- I3C context, CCC, and MDB allocation: standards alignment and integration;
- physical-bus bandwidth and HDR evolution: base-bus/wire methodology; and
- developer elapsed time: too confounded by order, familiarity, and a single
  implementer to serve as a primary extensibility metric.

## Pros and Cons of the Options

### Option A: Two obvious additions

- Good: Small and easy to explain.
- Bad: Directly favors each candidate's advertised strength and misses
  versioning, size, and structure.

### Option B: Select scenarios during implementation

- Good: Allows realistic cases to emerge naturally.
- Bad: Creates researcher degrees of freedom after candidate behavior is known.

### Option C: Frozen twelve-scenario catalog

- Good: Broad, finite, reproducible, and reviewable before code exists.
- Bad: Higher implementation cost and inevitably incomplete beyond the bounded
  taxonomy.

## References

- [I3CEX-0.2.0-draft section 5.3](https://github.com/jemsbhai/i3cex/blob/main/specs/I3CEX-0.2.0-draft.md#53-comparison-criteria).
- [ADR-0010](./0010-bakeoff-evaluation-methodology.md) — bakeoff
  meta-methodology.
- [RFC 6709, Design Considerations for Protocol Extensions](https://www.rfc-editor.org/rfc/rfc6709.html)
  — versioning, unknown extensions, testability, and parameter-space design.
- [RFC 9170, Long-Term Viability of Protocol Extension Mechanisms](https://www.rfc-editor.org/rfc/rfc9170.html)
  — active use and intolerance risks for extension points.
