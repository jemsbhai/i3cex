# ADR-0006: TLV length encoding — fixed 1-byte with documented extension paths

- **Status**: Accepted
- **Date**: 2026-04-23
- **Deciders**: Muntaser Syed
- **Consulted**: Claude (Anthropic)
- **Informed**: Future collaborators, reviewers

## Context and Problem Statement

The I3C-EX TLV framing strategy (Candidate B in the framing bakeoff —
see ADR-0002) needs a concrete length-encoding format. Each TLV record
declares how many bytes its Value field contains, and the decoder uses
this to advance to the next record. Three candidate length encodings
were considered: a fixed 1-byte length, a variable-length (varint)
encoding, and a hybrid with an "extended length" escape.

The decision must balance wire overhead, parse complexity, forward
compatibility, and fairness of the framing bakeoff against the
preamble-byte alternative.

## Decision Drivers

- Keep decoder complexity low so the framing bakeoff comparison
  (ADR-0002) remains apples-to-apples with Option A preamble framing.
- Minimise per-frame wire overhead for small values.
- Preserve a clean migration path if larger values are ever needed.
- Avoid variable decode latency where practical.

## Considered Options

- Option 1a: Fixed 1-byte length (0-255).
- Option 1b: Variable-length (varint/LEB128) encoding.
- Option 1c: Hybrid — 1-byte length with an "extended length" escape
  code (e.g., 0xFF triggers a 2-byte follow-on length).

## Decision Outcome

Chosen option: **Option 1a — fixed 1-byte length**, with extension
paths documented in the specification for future versions.

### Bit layout (v0.1)

```
Type (1 byte) | Length (1 byte, 0-127) | Value (0-127 bytes)
```

Note: Length values 0x80-0xFF are **reserved** in v0.1. Encoders MUST
NOT emit a Length byte >= 0x80. Decoders MUST reject any Length byte
>= 0x80 as malformed. This reserves the high bit for Path β (below)
as a forward-compatibility hook.

### Documented extension paths

Three concrete migration paths are documented in the specification
for lifting the 127-byte cap in future versions without breaking
v0.1 devices:

- **Path α (recommended)**: A future specification version assigns a
  reserved Type value to signal "the following record has an extended
  length." Such a record carries a 2-byte or 4-byte length in its own
  Value field, followed by the actual record. v0.1 decoders reject
  the reserved Type as unknown; v0.2 decoders handle it. No bit-level
  changes to existing records.

- **Path β**: A future specification version assigns meaning to the
  reserved high-bit range of the Length byte. Length bytes with the
  high bit set trigger an extended-length follow-on byte, similar to
  varint but with only two possible sizes. v0.1 decoders reject any
  length >= 0x80 as malformed, so this extension is cleanly
  detectable. This path cuts the v0.1 direct range to 0-127.

- **Path γ**: A future specification version defines a "continuation"
  Type whose Value bytes are concatenated with the next record's Value
  bytes. Supports arbitrary-length records via multi-record
  reassembly. No length-field changes; works with any length encoding.
  Stateful, with frame-loss hazards, so positioned as a last resort.

### Type-value allocation (v0.1)

Type values are not pre-reserved at the framing level. Each sublayer
owns a range of Type values defined in its own specification section.
A large "unallocated" range is preserved for future sublayers and
extension signalling. The specific choice of reserved Type for Path α
is deferred to the specification version that adopts it.

(Exception: Type 0xFE is reserved for future container semantics per
ADR-0007; see that ADR for details.)

### Consequences

**Good:**

- Decoder is trivial: read Type byte, read Length byte, read Value
  bytes. Constant-time per record.
- Matches the decoder simplicity of Option A preamble framing,
  keeping the bakeoff comparison fair.
- Three documented extension paths preserve flexibility without
  committing to complexity in v0.1.
- The 0x80-0xFF Length reservation echoes the reserved-bit discipline
  already established for Option A preamble framing (ADR-0005),
  creating a consistent forward-compatibility pattern across the
  specification.

**Bad:**

- 127-byte hard cap per Value field (after reserving the high bit).
  Sublayers needing larger values must either split across multiple
  TLV records (Path γ at the sublayer level) or wait for Path α
  adoption in v0.2.
- Half of the Length-byte range (128 values) is reserved at v0.1.
  This is a real efficiency cost compared to unrestricted 0-255.
- Encoding overhead is 2 bytes per record (Type + Length), regardless
  of Value size. Very small values (e.g., a single-bit flag) have
  high relative overhead.

## Pros and Cons of the Options

### Option 1a: Fixed 1-byte length

- Good: Trivial decoder. Constant-time parse per record.
- Good: Matches common embedded-protocol precedent (BLE GAP, USB
  descriptors, many SCSI CDBs).
- Good: Predictable worst-case record size.
- Bad: Hard cap on Value size (127 bytes after high-bit reservation).
- Bad: Can waste a byte on very small values.

### Option 1b: Variable-length (varint) encoding

- Good: Compact for small values (1 byte for 0-127).
- Good: No hard cap on Value size within practical I3C frame limits.
- Good: Matches Protobuf, LEB128, and many modern wire formats.
- Bad: Decoder is loopy — "read byte, check top bit, maybe read more."
- Bad: Cyclomatic complexity rises; variable decode latency.
- Bad: Would unfairly penalise TLV in the decode-complexity axis of
  the framing bakeoff.

### Option 1c: Hybrid with extended-length escape

- Good: Common case is 1-byte fixed.
- Good: Escape hatch for large records without full varint complexity.
- Good: Decoder is single if-else, not a loop.
- Bad: Two encoding paths means two sets of test vectors and edge
  cases.
- Bad: Wastes the escape sentinel (e.g., 0xFF) from the length space.
- Bad: Introduces complexity that a sublayer-specific Path α
  migration could handle more cleanly at the Type level.

## References

- `../../../specs/I3CEX-0.1.0-draft.md` section 5.2 — TLV framing
  (updated in the same commit as this ADR).
- [`./0002-framing-comparative-prototyping.md`](./0002-framing-comparative-prototyping.md)
  — parent decision establishing the framing bakeoff.
- [`./0005-preamble-wire-format.md`](./0005-preamble-wire-format.md)
  — precedent for reserved-bit forward-compatibility discipline.
- [`./0007-tlv-nesting-deferred.md`](./0007-tlv-nesting-deferred.md)
  — Type-value reservation policy for containers.
- [`../../../../i3cex/src/i3cex/framing/tlv.py`](../../../../i3cex/src/i3cex/framing/tlv.py)
  — reference implementation.
