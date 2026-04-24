# ADR-0007: TLV nesting deferred, Type 0xFE reserved for future container semantics

- **Status**: Accepted
- **Date**: 2026-04-23
- **Deciders**: Muntaser Syed
- **Consulted**: Claude (Anthropic)
- **Informed**: Future collaborators, reviewers

## Context and Problem Statement

Some I3C-EX sublayers have naturally hierarchical data. A Byzantine
fusion sensor cluster (EX-3) contains multiple vote sub-records. A
provenance hash chain (EX-5) contains multiple chain-link sub-records.
A confidence summary (EX-6) contains multiple per-field confidence
sub-records.

The TLV framing layer must decide how to express (or whether to
express) this hierarchy. Three positions were considered: full nested
TLVs with recursive decoding, flat-only sibling records with
begin/end markers, or deferred — v0.1 supports only flat records and
nesting is a documented future extension.

## Decision Drivers

- Keep decoder complexity low to maintain fairness in the framing
  bakeoff against Option A preamble framing.
- Avoid committing to nesting semantics before the sublayer designs
  that would consume them (EX-3/5/6) are specified — this would
  violate the pre-registration discipline in GOVERNANCE.md.
- Preserve a clean migration path if nesting turns out to be
  essential.

## Considered Options

- Option 2a: Full nesting with recursive TLV decoding.
- Option 2b: Flat-only with begin/end marker records for grouping.
- Option 2c: Deferred — flat-only in v0.1, nesting as future extension.

## Decision Outcome

Chosen option: **Option 2c — flat-only in v0.1, nesting deferred as a
future extension path**, with one additional constraint: **Type 0xFE
is reserved as a placeholder for future container semantics**.

### Enforcement (v0.1)

- All TLV records in a v0.1 frame are siblings at the top level.
- Every byte after a record's Length byte is treated as that record's
  opaque Value. Decoders MUST NOT attempt to recursively parse the
  Value as further TLV records in v0.1.
- Type 0xFE MUST NOT be emitted by v0.1 encoders.
- Type 0xFE MUST be rejected by v0.1 decoders as reserved.
- The 0xFE reservation applies across all sublayer Type namespaces;
  no sublayer may allocate 0xFE for its own use.

### Future extension (informative, non-binding)

A future specification version may define Type 0xFE as a "container
record" whose Value field is a sequence of TLV sub-records to be
parsed recursively. v0.1 decoders will cleanly reject such frames as
malformed (per the 0xFE rejection rule), preserving the migration
boundary.

Alternatively, a future version may redefine 0xFE for a different
container semantic (e.g., reference to a shared sub-structure),
provided it preserves the reservation invariant that v0.1 decoders
reject 0xFE.

### Consequences

**Good:**

- Decoder is a simple loop: read Type, read Length, skip Length
  bytes, repeat.
- Parse complexity matches or undershoots flat-only TLV precedents
  such as BLE GAP EIR/AD structure.
- The 0xFE reservation mirrors the reserved-bit discipline used in
  Option A preamble framing (ADR-0005) and the Length-byte
  reservation in TLV length encoding (ADR-0006). This gives the
  specification a consistent forward-compatibility pattern across
  every wire-level field.
- Sublayer designs (EX-3/5/6) remain free to evolve without
  constraining the TLV layer prematurely.

**Bad:**

- If nesting turns out to be essential for a sublayer, it will
  require a spec revision (v0.2) before that sublayer can be
  finalised. This is an acceptable risk because it creates a
  forcing function for evidence-based design.
- Sublayers with naturally hierarchical data must flatten their
  representation into sibling records, potentially increasing per-
  record overhead for deeply hierarchical data.
- Reserving Type 0xFE consumes one slot from the 256-value Type
  namespace. This is a minor efficiency cost justified by the
  forward-compatibility benefit.

## Pros and Cons of the Options

### Option 2a: Full nesting with recursive decoding

- Good: Natural representation for hierarchical data.
- Good: Matches ASN.1, Protobuf embedded messages, BLE advertising
  data container structure.
- Bad: Decoder recursion (or explicit stack) increases parse
  complexity.
- Bad: Error recovery is harder; a malformed inner record can
  corrupt the outer's length accounting.
- Bad: Max nesting depth needs a limit to prevent stack exhaustion.
- Bad: Commits to hierarchy semantics before sublayer designs are
  finalised; contradicts pre-registration discipline.
- Bad: Would unfairly penalise TLV in the decode-complexity axis of
  the framing bakeoff.

### Option 2b: Flat-only with begin/end markers

- Good: Decoder remains a simple loop; no recursion.
- Good: Clear parse boundaries — every record is length-prefixed at
  the top level.
- Bad: Sublayer designers must invent begin/end markers or implicit
  grouping conventions, which is error-prone.
- Bad: Ambiguity if a frame is truncated mid-group.
- Bad: Higher overhead per sub-record (every sub-record pays the
  full Type+Length tax).

### Option 2c: Deferred with 0xFE placeholder

- Good: Smallest v0.1 scope; ships flat TLV fast.
- Good: Evidence-based — sublayer designs (EX-3/5/6) can inform
  whether nesting is actually needed.
- Good: Keeps the TLV-vs-preamble bakeoff fair (preamble has no
  nesting story, so flat-only TLV is apples-to-apples).
- Good: Forward extension path is explicit and reserved now.
- Good: BLE precedent — billions of deployed devices use flat TLV
  with no protocol-level nesting.
- Bad: If nesting turns out to be essential, requires a v0.2 spec
  bump before dependent sublayers can be finalised.

## References

- `../../../specs/I3CEX-0.1.0-draft.md` section 5.2 — TLV framing
  (updated in the same commit as this ADR).
- [`./0002-framing-comparative-prototyping.md`](./0002-framing-comparative-prototyping.md)
  — parent decision establishing the framing bakeoff.
- [`./0005-preamble-wire-format.md`](./0005-preamble-wire-format.md)
  — precedent for reserved-field forward-compatibility discipline.
- [`./0006-tlv-length-encoding.md`](./0006-tlv-length-encoding.md)
  — companion TLV decision on length encoding.
- BLE Core Specification — EIR/AD structure as flat-TLV precedent.
