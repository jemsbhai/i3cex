# ADR-0008: TLV maximum block size — negotiated with 4096-byte default

- **Status**: Accepted
- **Date**: 2026-04-23
- **Deciders**: Muntaser Syed
- **Consulted**: Claude (Anthropic)
- **Informed**: Future collaborators, reviewers

## Context and Problem Statement

A single I3C transaction carrying I3C-EX data may contain multiple
TLV records chained end-to-end. The specification must define the
maximum total size of this TLV block within one I3C transaction. This
cap is distinct from the per-record length cap defined in ADR-0006.

I3C SDR mode does not impose a strict maximum transfer length at the
protocol level; a controller may keep transmitting until it issues a
STOP condition. In practice, typical sensor reads are short (1-16
bytes), but bulk transfers (e.g., image data from a camera sensor)
can be hundreds of bytes, and I3C controller FIFO depths are
typically around 128 bytes. The cap is therefore a spec-level design
choice, not a protocol-imposed value.

The decision must balance flexibility (different devices have
different buffer budgets), efficiency (no added per-frame latency),
and predictability (implementations need to pre-allocate buffers).

## Decision Drivers

- Must not add measurable per-frame latency to steady-state
  operation, per project efficiency principle (ADR-0009).
- Must admit a wide range of device classes, from constrained
  ultra-low-power sensors to bulk data producers.
- Must allow edge AI workloads (sensor fusion traces, compressed
  tile data, confidence maps) that typically run into hundreds of
  bytes.
- Must be predictable enough for constrained devices to
  pre-allocate buffers.

## Considered Options

- Option 3a: No explicit cap; TLV block fills the I3C transaction.
- Option 3b: Fixed cap of 255 bytes.
- Option 3c: Fixed cap of 4096 bytes.
- Option 3d: Device-negotiated cap advertised at bus initialisation.

Three sub-decisions within Option 3d were also resolved:
- (A) Minimum floor for the negotiated cap.
- (B) Where the cap value lives on the wire.
- (C) What happens if a device does not advertise a cap.

## Decision Outcome

Chosen option: **Option 3d — device-negotiated cap** with the
following sub-decisions:

- **(A) No minimum floor.** Devices MAY advertise any cap >= 1.
  Constrained devices are admitted.
- **(B) Cap advertised in the EX-Discovery CCC response**, as a
  2-byte field, one-shot at bus initialisation.
- **(C) Unadvertised caps default to 4096 bytes.**

### Effective cap computation

For a given (controller, target) pair:

```
effective_cap = min(
    controller_advertised_cap or 4096,
    target_advertised_cap or 4096,
)
```

Encoders MUST NOT emit a TLV block exceeding the effective cap.
Decoders MUST reject any TLV block exceeding their own advertised
cap (or 4096 if unadvertised), raising `TLVDecodeError`.

### Default for library-level use

The reference implementation exposes:

```python
DEFAULT_MAX_TLV_BLOCK_SIZE_V01 = 4096  # bytes
```

Higher layers that participate in bus-init negotiation may override
this default when invoking encoder/decoder functions. Library users
without a full bus-init dance receive the 4096 default automatically.

### Latency analysis

The latency impact of Option 3d versus the fixed-cap alternative
(3c) is as follows:

- **Init-time cost**: 2 additional bytes in the EX-Discovery CCC
  response, paid once per bus initialisation.
- **Per-frame cost**: one integer comparison (`block_size <= cap`).
  In 3c the cap is a compile-time constant; in 3d it is a per-target
  field. The difference is at most one additional memory load per
  frame, well below the noise floor of I3C's megahertz-scale
  transaction timing. **Effectively zero latency difference in
  steady state.**

This analysis is published here for traceability and is the primary
justification for adopting 3d over the simpler 3c.

### Consequences

**Good:**

- Maximum flexibility across device classes without per-frame
  overhead.
- Constrained ultra-low-power devices can advertise tiny caps; bulk
  devices can advertise larger caps (subject to future-version cap
  ceiling, if ever raised).
- Default of 4096 provides headroom for realistic edge AI workloads
  (sensor fusion + provenance + confidence combinations).
- Library users without bus-init participation get a sensible
  default automatically.
- DoS resistance: a malicious target cannot flood a constrained
  controller; the cap is a first-line defence.
- The 2-byte advertisement field has forward-compatibility headroom
  if larger caps are ever needed (16-bit field supports up to
  65535 bytes, so v0.2 can extend to 8 KiB or 16 KiB simply by
  raising the library default).

**Bad:**

- Controllers must track per-target caps, adding a small amount of
  state beyond what Option 3c would require.
- Interop testing matrix grows: small-cap controller ↔ large-cap
  target, large-cap controller ↔ small-cap target, etc. This is
  manageable but nonzero.
- "No minimum floor" means a device could advertise an absurdly
  small cap (e.g., 4 bytes) that cannot fit any meaningful
  sublayer record. Such devices would effectively be unable to
  participate in most sublayer exchanges. This is left as a
  device-design concern rather than a protocol-enforced minimum.

## Pros and Cons of the Options

### Option 3a: No explicit cap

- Good: Maximally flexible; matches how I3C itself works.
- Bad: Implementations cannot pre-allocate buffers.
- Bad: No way to validate "frame looks correct" at parse time.
- Bad: Denial-of-service vector on constrained devices.

### Option 3b: Fixed 255-byte cap

- Good: Matches single-record cap from ADR-0006; consistent mental
  model.
- Good: Pre-allocatable buffers; every device knows the ceiling.
- Bad: Very tight; forces multi-frame sequences for moderately
  complex sublayer combinations (e.g., EX-4 timestamp + EX-5
  provenance together).

### Option 3c: Fixed 4096-byte cap

- Good: Large enough for realistic edge AI workloads.
- Good: Predictable; simple implementation.
- Bad: Wastes buffer potential on devices that could run smaller.
- Bad: No flexibility to accommodate devices with tighter budgets.

### Option 3d: Device-negotiated cap

- Good: Most flexible across device classes.
- Good: Matches existing negotiation pattern (capability level is
  already negotiated at discovery).
- Good: Library-level default provides convenience for non-
  negotiating users.
- Bad: Controllers must track per-target state.
- Bad: Interop testing matrix grows.

## References

- `../../../specs/I3CEX-0.1.0-draft.md` section 5.2.3 — TLV maximum
  block size and negotiation.
- [`./0006-tlv-length-encoding.md`](./0006-tlv-length-encoding.md)
  — per-record length cap.
- [`./0009-efficiency-principle.md`](./0009-efficiency-principle.md)
  — efficiency principle under which this decision's latency
  analysis was conducted.
- [`../../../../i3cex/src/i3cex/framing/tlv.py`](../../../../i3cex/src/i3cex/framing/tlv.py)
  — reference implementation.
