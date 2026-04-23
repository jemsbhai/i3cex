# ADR-0005: Preamble wire format (Option A) with forward-compatibility to bitmap and table forms

- **Status**: Accepted
- **Date**: 2026-04-23
- **Deciders**: Muntaser Syed
- **Consulted**: Claude (Anthropic)
- **Informed**: Future collaborators, reviewers

## Context and Problem Statement

The I3C-EX preamble-byte framing strategy (Candidate A in the framing
bakeoff — see ADR-0002) needs a concrete bit layout. Three candidate
layouts were considered: a single-byte layout using a capability level
plus an extension flag (Option A), a two-byte layout with a full
sublayer bitmap (Option B), and a single-byte layout with a negotiated
table lookup (Option C).

Each has different trade-offs on wire overhead, expressiveness,
statefulness, debuggability, and forward-compatibility headroom. We
need to pick one for v0.1 of the specification, but we must also
preserve a path to adopt the others if evidence from the bakeoff
suggests they become preferable.

## Decision Drivers

- Minimise wire overhead for the common case (one byte ideal).
- Preserve stateless framing for debuggability and hot-join safety.
- Leave enough reserved-bit headroom to switch wire formats later
  without breaking v0.1 decoders.
- Keep conformance testing simple (no table-state dependencies).
- Align with the specification's current assumption that EX-N
  implies EX-1 through EX-N (level-monotonic sublayer sets).

## Considered Options

- Option A: 1 byte, level-implies-lower-sublayers + extension flag.
- Option B: 2 bytes, full 8-bit sublayer bitmap.
- Option C: 1 byte + negotiated table lookup.

## Decision Outcome

Chosen option: **Option A for v0.1**, designed so that B and C can be
added in later specification versions without breaking v0.1 devices.

The chosen bit layout for Option A:

```
bit 7:     EX-present flag (always 1 when a preamble is present)
bits 6-4:  capability level (0..7; 0 = EX-0 negotiation-only; 1..6 = EX-1..EX-6; 7 = reserved)
bit 3:     extension-follows flag (1 = additional bytes follow the preamble)
bits 2-0:  reserved (MUST be zero in v0.1; a future version may claim these)
```

### Forward-compatibility mechanism

The three reserved bits (bits 2-0) and the extension-follows flag
(bit 3) form the hooks for future wire-format evolution:

- **v0.2 path to Option B**: A future spec version MAY assign meaning
  to one of bits 2-0 such that when set, the preamble is interpreted
  as a two-byte layout with a full 8-bit bitmap in byte 1. v0.1
  decoders will correctly reject such frames as malformed (reserved
  bit non-zero), rather than silently misinterpret them.
- **v0.3 path to Option C**: A different reserved bit can signal that
  bits 3-0 are a table index rather than a flag plus reserved bits,
  gated on a negotiated table state established via CCC at bus
  initialisation.
- **Extension-follows flag** (bit 3): Already defined in v0.1. When
  set, additional bytes follow the preamble in a format to be
  specified by a later version. v0.1 decoders SHOULD treat frames
  with this flag as "EX-aware data present but in a format this
  decoder does not understand" and fall back to v0.1 semantics or
  raise a well-defined error.

### Code architecture for extensibility

To make the migration mechanical rather than invasive, the reference
implementation decouples the wire format from the in-memory
representation:

- A single `Preamble` dataclass carries the full information space
  that any wire format (A, B, or C) could encode — capability level,
  full 8-bit sublayer bitmap, extension flag, version.
- Separate `encode_option_a` / `decode_option_a` functions handle
  Option A specifically.
- Future versions add `encode_option_b` / `decode_option_b` etc.
  without touching the `Preamble` dataclass or its consumers.
- A format-selection layer chooses the correct encoder/decoder based
  on negotiated version; this layer does not exist in v0.1 because
  only one format is supported.

In Option A, the `Preamble.sublayer_bitmap` field is always
level-monotonic (equal to ``(1 << capability_level) - 1``). The
encoder MUST validate this invariant and raise on violation, so
callers cannot accidentally construct a `Preamble` that Option A
cannot represent faithfully.

### Consequences

**Good:**

- v0.1 delivers the minimum possible wire overhead (1 byte).
- Decoder is trivial: one byte, four bit-operations.
- `Preamble` dataclass is wire-format-agnostic, so v0.2 and v0.3
  migrations do not ripple through consumer code.
- Reserved-bit discipline means v0.1 decoders cleanly reject
  future formats rather than silently misinterpret them.
- Level-monotonic invariant aligns with the specification's current
  sublayer-dependency semantics.

**Bad:**

- Cannot signal sparse sublayer combinations in v0.1 (e.g., EX-5
  without EX-2/EX-3/EX-4). Accepted because the specification does
  not yet require this.
- Only 7 capability levels are addressable (0..7 with one reserved).
  We have EX-1..EX-6 specced, leaving exactly one slot. Migration
  to Option B is required if EX-8 or beyond is ever specified.
- Three reserved bits is a finite forward-compatibility budget.
  Each future protocol evolution consumes bits from this pool.

## Pros and Cons of the Options

### Option A: 1 byte, level + extension flag

- Good: Minimum wire overhead (1 byte).
- Good: Trivial to parse (four bit-operations).
- Good: Stateless; no table sync, no hot-join hazard.
- Good: Matches spec's level-implies-lower assumption.
- Good: Three reserved bits provide migration headroom.
- Bad: Cannot express sparse sublayer sets.
- Bad: Only 7 capability levels before exhaustion.
- Bad: Finite reserved-bit budget for future use.

### Option B: 2 bytes, full bitmap

- Good: Arbitrary sublayer combinations expressible.
- Good: Up to 8 sublayers natively addressable.
- Good: Built-in protocol version field (byte 0 bits 6-4).
- Good: Three reserved bits plus an unused byte 0 low nibble.
- Bad: Doubled wire overhead (2 bytes per frame).
- Bad: Overhead is paid on every frame even when the extra
  expressiveness is not used, which is expected to be the common
  case.

### Option C: 1 byte + negotiated table lookup

- Good: Combines 1-byte overhead with bitmap expressiveness.
- Good: Steady-state frames are maximally compact.
- Bad: Stateful. Requires CCC-driven table init and sync.
- Bad: Hot-join targets must re-sync the table before they can
  participate. Races are possible.
- Bad: 16-entry table cap creates a hard limit on concurrent
  sublayer-combination diversity.
- Bad: Wire captures are not self-describing; decoding requires the
  table state captured separately.
- Bad: Conformance test vectors become table-state-dependent,
  complicating verification.

## References

- `../../../specs/I3CEX-0.1.0-draft.md` section 5.1 — Option A bit
  layout (updated in the same commit as this ADR).
- [`./0002-framing-comparative-prototyping.md`](./0002-framing-comparative-prototyping.md)
  — parent decision establishing the framing bakeoff.
- [`../../../../i3cex/src/i3cex/framing/preamble.py`](../../../../i3cex/src/i3cex/framing/preamble.py)
  — reference implementation.
