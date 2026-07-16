# I3C-EX Specification, Version 0.2.0 (DRAFT)

**Status**: Draft — Unstable. Breaking changes expected without notice.
**Version**: 0.2.0-draft
**Date**: 2026-07-15
**Replaces**: I3CEX-0.1.0-draft as the active working draft
**Superseded by**: None

> This is an early-stage draft. Large portions of this document are
> skeletal and marked `[TBD]`. The draft exists to pre-register the
> research hypothesis before implementation begins, per the project's
> pre-registration policy (see `../GOVERNANCE.md`).

> **Independent research notice:** I3C-EX is not affiliated with, sponsored by,
> approved by, certified by, or endorsed by MIPI Alliance. This document is an
> original higher-layer content-protocol proposal and does not reproduce,
> replace, or amend the I3C Basic specification. See `../NOTICE.md`.

---

## 1. Scope

### 1.1 In Scope

This specification defines **I3C-EX**, an optional higher-layer content
protocol based on MIPI I3C Basic v1.2 plus published errata. I3C-EX provides:

1. A **metadata envelope format** for wrapping I3C transactions with
   auxiliary information (timestamps, confidence, provenance, etc.).
2. A **quality-of-service negotiation sublayer** for controller-target
   bandwidth, latency, and power agreements.
3. A **Byzantine fusion signalling sublayer** for voting, quorum, and
   disagreement propagation across redundant sensors.
4. A **distributed timestamping sublayer** for cross-bus temporal
   correlation using I3C's existing in-band interrupt mechanism.
5. A **provenance and attestation sublayer** for hash-chained source
   attribution and transform history.
6. A **confidence propagation and extended error sublayer** for
   bit-level data quality metadata and richer error recovery.

I3C-EX may run through firmware updates on platforms whose controller and
target interfaces already expose every required I3C Basic mechanism, including
Private SDR transfers, SETBUSCON, a suitable directed extension CCC, and any
optional IBI facilities used by a sublayer. This is a platform-specific
compatibility goal, not a claim that all existing hardware needs no changes.
Devices that do not implement I3C-EX continue to operate as ordinary I3C
devices; I3C-EX semantics are disabled until explicitly selected and negotiated.

### 1.2 Out of Scope

- Any change to I3C physical-layer signalling (voltage levels, timing
  parameters, open-drain/push-pull modes).
- Any change to I3C Dynamic Address Assignment, base Common Command Codes,
  frame-level arbitration, or the I3C conformance requirements.
- Full MIPI I3C features that are not part of the public I3C Basic baseline.
- Assignment of MIPI-managed Context Byte, CCC, or Mandatory Data Byte values.
- Clean-slate protocol redesign.
- Any application-layer semantics (sensor types, calibration,
  quantisation schemes). I3C-EX carries metadata; interpretation is the
  application's responsibility.
- Any claim of MIPI affiliation, endorsement, certification, or approval.

---

## 2. Terminology

Key words **MUST**, **MUST NOT**, **REQUIRED**, **SHALL**, **SHALL NOT**,
**SHOULD**, **SHOULD NOT**, **RECOMMENDED**, **NOT RECOMMENDED**, **MAY**,
and **OPTIONAL** in this document are to be interpreted as described in
[BCP 14](https://datatracker.ietf.org/doc/html/bcp14)
([RFC 2119](https://datatracker.ietf.org/doc/html/rfc2119),
[RFC 8174](https://datatracker.ietf.org/doc/html/rfc8174)) when, and only when,
they appear in all capitals.

### 2.1 Roles

- **Controller**: An I3C bus controller (the device that drives SCL).
  Uses the MIPI-normative term "Active Controller" or "Secondary
  Controller" as appropriate.
- **Target**: An I3C bus target (the device that responds to controller
  transactions). Replaces the deprecated I²C term "slave."
- **EX-Controller**: A controller implementing I3C-EX.
- **EX-Target**: A target implementing I3C-EX.
- **Legacy-Target**: A target implementing only I3C (or I²C) without I3C-EX.

### 2.2 Capability Levels

I3C-EX support is **compositional**. A device declares which sublayers it
supports during initialisation. Capability levels:

- **EX-0**: Declares EX support but implements no sublayers.
  (Reserved for negotiation and discovery only.)
- **EX-1**: Metadata envelope only.
- **EX-2**: EX-1 plus QoS negotiation.
- **EX-3**: EX-2 plus Byzantine fusion signalling.
- **EX-4**: EX-3 plus distributed timestamping.
- **EX-5**: EX-4 plus provenance and attestation.
- **EX-6**: EX-5 plus confidence propagation and extended error recovery.

A device supporting level N MUST support all sublayers of levels 1..N.

Levels beyond EX-6 are reserved for future extension.

### 2.3 Terms

- **Envelope**: A wrapper structure around an I3C payload carrying
  extension metadata.
- **Sublayer**: A logically distinct extension capability (e.g., QoS,
  fusion, timestamping).
- **Framing strategy**: The wire-level format used to carry envelope data.
  This specification compares two: *preamble-byte* and *TLV*.
- **TLV record**: A Type-Length-Value tuple. See Section 5.2.
- **TLV block**: A concatenated sequence of one or more TLV records
  within a single I3C transaction.

---

## 3. Background and Motivation

`[TBD]` Full background section. Draft points:

- I2C (1982) and I3C (2018) gaps for edge AI/ML workloads.
- No wire-level metadata, provenance, confidence, or fusion primitives.
- Clock-stretching elimination creates real-time brittleness.
- HDR fragmentation breaks interoperability.
- Zero native security or attestation.
- Request-response model poorly suited to continuous inference streams.
- Dynamic Address Assignment collision edge cases under hot-join swarms.

See `../README.md` for the broader research motivation.

---

## 4. Protocol Overview

### 4.1 Architecture

I3C-EX is a **higher-layer content protocol** carried in standard I3C Basic
Private SDR Read/Write transfers. Every I3C-EX exchange is, at the wire level,
a valid base-protocol exchange. The framing candidates define content within
the Private SDR payload; they do not modify I3C framing. Content is encoded in
one of two ways:

1. **Preamble-byte framing**: A single I3C-EX byte precedes the application
   content within the negotiated Private SDR payload and encodes a compact
   header.
2. **TLV framing**: Extension data is encoded as Type-Length-Value
   records appended to or embedded within the negotiated Private SDR payload
   per a negotiated schema.

Both framing strategies are being prototyped. The specification will
standardise one based on empirical comparison. See Section 5.

### 4.2 Discovery and Negotiation

I3C-EX semantics MUST be disabled after reset and Dynamic Address Assignment.
Before discovery, the controller MUST select an assigned I3C-EX bus context by
issuing SETBUSCON with the registered I3C-EX Context Byte. No such Context Byte
has been assigned at the time of this draft; therefore this section defines an
integration contract, not a deployable public numeric encoding.

After context selection, the controller uses a **directed** standards/vendor
extension CCC, symbolically named `EXDISC`, to negotiate with one addressed
target at a time. `EXDISC` is configuration/control only; I3C-EX data MUST NOT
be transported in the CCC. This draft assigns no numeric CCC value and MUST NOT
be implemented by choosing an unallocated public value.

The negotiation flow:

1. Controller selects the assigned I3C-EX context using SETBUSCON.
2. EX-Controller issues the directed `EXDISC` extension CCC.
3. EX-Targets respond with the I3C-EX specification version, capability
   level (EX-0..EX-6), the
   sublayers they support, and their advertised maximum TLV block
   size (see Section 5.2.3).
4. Controller and target agree on the minimum common level for each
   interaction. Level-0 interactions (no EX) are always available as a
   fallback.

Legacy or unknown targets may NACK or otherwise decline the directed extension
CCC; they remain ordinary I3C devices. The controller MUST NOT send I3C-EX
content to a target unless the correct context is active and negotiation with
that target succeeded.

Controlled experiments MAY use an explicitly configured Context Byte in the
MIPI private-use range 192-255. Such a value MUST be opt-in, recorded in the
experiment manifest, and described as private and non-interoperable. This
permission does not assign a stable value to I3C-EX.

### 4.3 Relationship to I3C

- The base compatibility target is I3C Basic v1.2 plus published errata.
- All I3C-EX data uses standard Private SDR Read/Write transfers.
- HDR-mode extension support is deferred to a future minor version.
- I3C-EX does not require clock stretching (I3C does not support it).
- I3C-EX does not change I3C's open-drain/push-pull signalling.
- I3C-EX does not change DAA, arbitration, or hot-join semantics.
- I3C-EX payload sizes respect the limits established by SETMRL and SETMWL.

### 4.4 Non-goals

- I3C-EX does not attempt to improve I3C's physical-layer characteristics.
- I3C-EX does not redefine error semantics at the I3C level; it adds a
  supplementary confidence/error sublayer.
- I3C-EX does not impose a security model; attestation and provenance
  are optional.
- I3C-EX conformance does not imply base I3C Basic conformance or MIPI
  certification.
- I3C-EX does not assign MIPI-managed identifiers or redistribute MIPI
  specifications and test materials.

---

## 5. Framing Strategy (Comparative)

The core of the v0.2.0 draft is the comparative prototyping of two
framing strategies. The final specification (``I3CEX-1.0.0``) will
standardise one based on empirical comparison; see Section 5.3 for the
comparison criteria.

References below to the "v0.1 wire format" identify the framing encodings
pre-registered in I3CEX-0.1.0-draft and retained unchanged here; they do not
change the active document version, which is 0.2.0-draft.

### 5.1 Preamble-Byte Framing (Candidate A)

A single-byte preamble immediately precedes the I3C payload. The v0.1
wire format corresponds to "Option A" in ADR-0005: a compact,
level-monotonic encoding with reserved bits that preserve a forward-
compatibility path to bitmap (Option B) and table (Option C) forms in
future specification versions.

#### 5.1.1 Bit layout

```
bit 7:     EX-present flag (MUST be 1 when a preamble is present)
bits 6-4:  capability level (0..7)
             - 0: EX-0 (negotiation/discovery only)
             - 1..6: EX-1..EX-6
             - 7: reserved for future use
bit 3:     extension-follows flag
             - 0: preamble is complete at byte 0 (v0.1 form)
             - 1: additional bytes follow the preamble (reserved for
                  future specification versions)
bits 2-0:  reserved; MUST be zero in v0.1
```

#### 5.1.2 Semantic constraints

An I3C-EX v0.1 Preamble has two normative invariants:

1. **Level-monotonic sublayer semantics.** When the preamble declares
   capability level N, all sublayers from EX-1 through EX-N are
   considered active for the associated transaction. Sparse sublayer
   sets (e.g., EX-5 without EX-2) cannot be expressed in v0.1 and
   MUST NOT be assumed by implementations.
2. **Reserved-bit discipline.** Bits 2-0 MUST be transmitted as zero.
   Receivers decoding a v0.1 frame MUST reject any frame with a
   non-zero reserved bit, because a future specification version may
   claim those bits to signal a different wire format.

#### 5.1.3 Preamble byte detection

I3C-EX-aware devices detect the presence of a preamble only through the
context-scoped endpoint negotiation in Section 4.2. A matching byte pattern in
an unnegotiated payload has no I3C-EX meaning. When EX-1 or higher has been
negotiated for a (controller, target, direction) tuple, the first content byte
of a transaction designated as I3C-EX is treated as a preamble. The EX-present
flag (bit 7) is a safety check; if it is zero, the receiver MUST treat the
Private SDR payload as non-EX application content and MUST NOT parse subsequent
bytes as I3C-EX.

#### 5.1.4 Forward compatibility

The reserved bits (2-0) and the extension-follows flag (bit 3) form
the forward-compatibility mechanism. Future specification versions
MAY:

- Assign meaning to one or more reserved bits to signal a wire-format
  extension, with v0.1 decoders correctly rejecting the frame as
  malformed (via the reserved-bit-must-be-zero rule).
- Define the structure of bytes following a preamble with bit 3 set.
  v0.1 decoders observing this flag SHOULD either fall back to
  legacy I3C handling or raise a well-defined error; they MUST NOT
  attempt to interpret the subsequent bytes.

See ADR-0005 for the migration strategy to Option B (two-byte bitmap)
and Option C (table-indexed) forms.

#### 5.1.5 Trade-offs (informative)

Preamble framing:

- **Advantages**: minimum wire overhead (1 byte per transaction);
  trivial to parse; stateless; matches the level-monotonic sublayer
  model.
- **Disadvantages**: cannot express sparse sublayer sets; only 7
  capability levels addressable (one slot currently unused); finite
  reserved-bit budget for future evolution.

### 5.2 TLV Framing (Candidate B)

Extension data is encoded as a sequence of Type-Length-Value records
(TLV records) concatenated end-to-end within the I3C payload to form
a TLV block. The v0.1 wire format is defined in ADR-0006 (length
encoding), ADR-0007 (nesting policy), and ADR-0008 (max block size).

#### 5.2.1 Record layout

Each TLV record has three fields:

```
byte 0:       Type   (1 byte)
byte 1:       Length (1 byte, 0-127; values 0x80-0xFF are reserved)
bytes 2..N:   Value  (Length bytes of sublayer-specific payload)
```

The minimum record size is 2 bytes (Type + Length with zero-length
Value). The maximum record size in v0.1 is 129 bytes (Type + Length +
127-byte Value).

##### 5.2.1.1 Type field

The Type field identifies the sublayer and record subtype. Each
sublayer owns a non-overlapping Type range:

| Type range   | Owner               |
|--------------|---------------------|
| 0x00 - 0x0F  | EX-1 (envelope)     |
| 0x10 - 0x1F  | EX-2 (QoS)          |
| 0x20 - 0x2F  | EX-3 (fusion)       |
| 0x30 - 0x3F  | EX-4 (timesync)     |
| 0x40 - 0x4F  | EX-5 (provenance)   |
| 0x50 - 0x5F  | EX-6 (confidence)   |
| 0x60 - 0xFD  | unallocated         |
| 0xFE         | **reserved** — see 5.2.2 |
| 0xFF         | unallocated         |

Encoders MUST NOT emit a Type value of 0xFE. Decoders MUST reject
any record with Type = 0xFE as malformed.

Within each sublayer range, specific Type values are defined in the
corresponding sublayer section (Sections 6.1 - 6.6).

##### 5.2.1.2 Length field

The Length field is a 1-byte unsigned integer declaring the number
of Value bytes that follow.

**Normative constraints (v0.1)**:

- Length values 0-127 (0x00 - 0x7F) are valid.
- Length values 128-255 (0x80 - 0xFF) are **reserved**. Encoders MUST
  NOT emit such values. Decoders MUST reject any record whose Length
  byte has the high bit set.

This high-bit reservation preserves Path β forward compatibility (see
Section 5.2.4).

##### 5.2.1.3 Value field

The Value field is an opaque byte sequence of exactly Length bytes.
Its internal structure is defined by the owning sublayer.

Decoders MUST treat the Value field as opaque bytes for the purpose
of TLV parsing. Decoders MUST NOT recursively parse the Value field
as further TLV records in v0.1 (see Section 5.2.2).

#### 5.2.2 Nesting policy (flat only; Type 0xFE reserved)

v0.1 TLV records are **flat**. Any hierarchy between records is
expressed by sibling records at the top level of the TLV block, not
by nested records within a Value field.

Type 0xFE is **reserved as a placeholder for future container
semantics**. v0.1 encoders MUST NOT emit Type 0xFE. v0.1 decoders
MUST reject any record with Type 0xFE as malformed.

A future specification version MAY define Type 0xFE as a container
record whose Value field is a sequence of TLV sub-records to be
parsed recursively, or as another form of grouping primitive. The
reservation ensures v0.1 decoders cleanly reject such frames rather
than silently misinterpreting them.

See ADR-0007 for the full reasoning.

#### 5.2.3 Maximum block size (negotiated)

Each I3C-EX transaction contains a TLV block whose total length (sum
of all TLV records) MUST NOT exceed the **effective cap** for the
(controller, target) pair.

##### 5.2.3.1 Advertisement via directed `EXDISC`

Each EX-capable device MAY advertise a maximum TLV block size during
bus initialisation. The cap is a 2-byte unsigned integer included in
the directed `EXDISC` response, alongside the capability level and
supported sublayers.

Encoding: 2 bytes, big-endian, in units of bytes.

If a device does not include a max-block-size field in its `EXDISC` response,
its I3C-EX protocol cap is **4096 bytes** (the default). The base-protocol
transfer budget described below still takes precedence.

##### 5.2.3.2 Effective cap computation

For a given (controller, target) pair, the effective cap is:

```
effective_cap = min(
    controller_advertised_cap,
    target_advertised_cap,
    direction_specific_private_sdr_content_budget,
)
```

Where any unadvertised I3C-EX value is treated as 4096. The direction-specific
Private SDR content budget is derived from the applicable SETMWL or SETMRL
limit after accounting for base-protocol and I3C-EX framing overhead. An
implementation MUST NOT use the 4096-byte default to exceed the base limit.

##### 5.2.3.3 Enforcement

- Encoders MUST NOT emit a TLV block whose total length exceeds the
  effective cap for the target they are transmitting to.
- Decoders MUST reject any TLV block whose total length exceeds
  the effective cap, including the base-protocol directional limit, raising a
  decode error. Implementations MAY continue to process subsequent
  frames after rejecting a malformed block.

##### 5.2.3.4 Minimum floor

There is no minimum advertised cap in v0.1. Devices MAY advertise
any cap >= 1. Advertising a cap too small to contain meaningful
sublayer records is a device-design choice, not a protocol violation.

#### 5.2.4 Forward compatibility

Three migration paths are documented for lifting the 127-byte
per-record limit in future specification versions without breaking
v0.1 devices:

- **Path α (recommended)**: A future version assigns a reserved Type
  value to mean "extended length follows," with the actual length
  encoded in a 2-byte or 4-byte field within the record's Value. v0.1
  decoders reject the reserved Type as unknown; v0.2 decoders handle
  it.
- **Path β**: A future version assigns meaning to Length values in
  the 0x80-0xFF range (high bit set), triggering an extended-length
  follow-on byte. v0.1 decoders reject high-bit Length values as
  malformed, cleanly signalling the incompatibility.
- **Path γ**: A future version defines a "continuation" Type whose
  Value is concatenated with the next record's Value during decoding.
  Supports arbitrary-length records via multi-record reassembly. No
  length-field changes; stateful.

See ADR-0006 for the full reasoning and trade-offs.

The 2-byte max-block-size advertisement in Section 5.2.3.1 supports caps up to
65535 bytes. Future versions MAY raise the I3C-EX default, but no advertised or
default value overrides SETMRL, SETMWL, or another applicable base-protocol
limit.

#### 5.2.5 Trade-offs (informative)

TLV framing:

- **Advantages**: arbitrary sublayer combinations; self-delimiting
  records that allow skipping unknown Types; clear forward
  compatibility via Type-range allocation.
- **Disadvantages**: higher minimum overhead (2 bytes per record);
  slightly higher decoder complexity than preamble framing; the
  flat-only nesting policy forces sublayers with hierarchical data
  to flatten their representation.

### 5.3 Comparison Criteria

The following criteria will be measured in the reference implementation
and reported in Paper 1:

1. **Wire overhead**: Bytes added per transaction for EX-1 through EX-6.
2. **Parse complexity**: Cyclomatic complexity of the receiver decoder.
3. **Extensibility**: Compatibility, framing intervention, namespace use, and
   implementation change required to add or evolve protocol semantics.
4. **Legacy safety**: Behaviour when an EX-aware device receives
   malformed EX data from a misbehaving peer.
5. **Worst-case latency impact**: Additional decode time under load.
6. **Throughput impact**: Effective payload bandwidth given envelope
   overhead.

Both strategies will be implemented. If the registered evidence selects a
loser, it will be documented in an ADR and in Paper 1 as a negative result. If
the evidence establishes a trade-off without a unique winner, that result will
be reported without forcing a ranking.

Methodology is pre-registered before benchmark implementation:

- ADR-0010 requires all six axes and separates cross-cutting rules from
  per-axis methods.
- ADR-0011 requires independent Python and C implementations with embedded C
  as the primary runtime endpoint and within-language paired comparisons.
- ADR-0012 defines a twelve-scenario framing-neutral extensibility taxonomy.
- ADR-0013 requires exhaustive candidate/version/direction coverage plus
  measured pairwise coverage of nuisance factors.
- ADR-0014 defines fixed semantic outcomes, a safety gate, and Pareto
  comparison without a weighted extensibility score.
- ADR-0016 defines exact wire-byte accounting over a finite boundary
  grid, including fragmentation and setup amortization.
- ADR-0017 defines a parser-structure and embedded-resource vector
  without a composite complexity score.
- ADR-0018 defines negotiation-state, version-skew, mutation,
  sanitizer, fixed-run fuzzing, and embedded-replay safety gates.
- ADR-0019 distinguishes safe WCET upper bounds, bounded-domain
  maxima, and sampled maxima while separating compute from wire occupancy.
- ADR-0020 defines analytical goodput ceilings and a zero-loss
  offered-load search for empirical application goodput.

A new machine-readable manifest version MUST freeze all six axes before the
benchmark harness or labeled bakeoff measurements begin. The frozen
extensibility manifest v1 MUST remain unchanged.

---

## 6. Sublayer Specifications

Every sublayer specification MUST include an **Overhead Analysis**
subsection per the Efficiency Principle (see `../GOVERNANCE.md` and
ADR-0009) before progressing beyond `-draft` status.

### 6.1 Metadata Envelope (EX-1) — Primary Focus of 0.2.0-draft

The metadata envelope is the foundational sublayer on which all others
ride. It carries a minimal set of always-useful metadata:

- **Sequence number**: Monotonic per (controller, target) pair.
- **Timestamp**: Local-clock timestamp at send time. Width `[TBD]`.
- **Flags**: Bitmap indicating which higher sublayers are present.
- **Checksum**: `[TBD — relationship to I3C's existing parity]`.

Detailed bit-level layout: `[TBD, pending framing decision]`.

**Overhead Analysis**: `[TBD — required before EX-1 graduates from -draft]`.

### 6.2 Quality-of-Service Negotiation (EX-2)

`[TBD]`. Will include:
- Latency budget declarations (target → controller).
- Bandwidth requests.
- Power-mode hints.
- Priority class assignment.

**Overhead Analysis**: `[TBD — required before EX-2 graduates from -draft]`.

### 6.3 Byzantine Fusion Signalling (EX-3)

`[TBD]`. Will include:
- Voting tokens for redundant sensor clusters.
- Disagreement flags.
- Quorum-state propagation.

**Overhead Analysis**: `[TBD — required before EX-3 graduates from -draft]`.

### 6.4 Distributed Timestamping (EX-4)

`[TBD]`. May include:
- Clock beacon notifications via In-Band Interrupt, but only if the semantics
  can use a permitted registered Mandatory Data Byte value or an appropriate
  value is assigned. This draft assigns no MDB value.
- Skew estimation across controllers.
- Cross-bus timestamp federation.

**Overhead Analysis**: `[TBD — required before EX-4 graduates from -draft]`.

### 6.5 Provenance and Attestation (EX-5)

`[TBD]`. Will include:
- Hash-chain record per value.
- Source attribution identifiers.
- Transform history encoding.

**Overhead Analysis**: `[TBD — required before EX-5 graduates from -draft]`.

### 6.6 Confidence Propagation and Extended Error (EX-6)

`[TBD]`. Will include:
- Bit-level confidence scores.
- Extended CRC / FEC options.
- Retransmission hints tied to inference criticality.

**Overhead Analysis**: `[TBD — required before EX-6 graduates from -draft]`.

---

## 7. Conformance

Conformance is layered and produces two separate claims:

1. **Base implementation evidence**, identifying the I3C Basic v1.2
   implementation, applicable errata, and its independent validation status.
2. **I3C-EX conformance**, identifying the exact I3C-EX draft or release and
   capability level implemented.

I3C-EX conformance MUST NOT be described as MIPI certification, MIPI
conformance, or MIPI endorsement. Minimal I3C-EX requirements are:

- An EX-Controller conforming to level N MUST implement all mandatory
  behaviours of levels 1..N.
- An EX-Target MUST implement all mandatory behaviours through its advertised
  monotonic capability level. Sparse sublayer support, if later introduced,
  requires a future negotiation format and MUST NOT be inferred in this draft.
- The target MUST default I3C-EX semantics to disabled and enable them only for
  the correctly selected context and successfully negotiated endpoint.
- Controllers and targets MUST obey the applicable SETMRL/SETMWL-derived
  content budget.
- All conforming implementations MUST pass the I3C-EX test vectors
  (published alongside this specification in `tests/vectors/`).
- A test report MUST state that I3C-EX vectors do not establish I3C Basic
  conformance.

While this specification and its vector corpus remain incomplete drafts, an
implementation MUST describe its result as experimental compatibility with the
named draft, not as conformance to a released I3C-EX standard.

---

## 8. Security Considerations

`[TBD]`. Key points to cover:

- I3C-EX does not itself provide confidentiality or authentication.
  Devices concerned with adversarial scenarios MUST layer attestation
  (EX-5) on top or use I3C Interface for SSP.
- Malicious targets MAY forge metadata. EX-1 metadata is advisory
  unless EX-5 attestation is present.
- Sequence numbers prevent trivial replay only; they do not replace
  cryptographic freshness guarantees.
- **TLV block-size DoS**: the negotiated max-block-size cap (Section
  5.2.3) is a first-line defence against malicious peers flooding
  constrained devices with large TLV blocks. Decoders MUST enforce
  their advertised cap.

---

## 9. References

### Normative

- MIPI Alliance Specification for I3C Basic, Version 1.2, adopted 17 April
  2025, plus published errata. Obtain it from the
  [official I3C specification page](https://www.mipi.org/specifications/i3c-sensor-specification).
- [RFC 2119](https://datatracker.ietf.org/doc/html/rfc2119) and
  [RFC 8174](https://datatracker.ietf.org/doc/html/rfc8174) / BCP 14 — Keywords
  for normative language.

### Informative

- [chipsalliance/i3c-core](https://github.com/chipsalliance/i3c-core) —
  Apache-2.0 open-source I3C controller RTL used as cosimulation
  ground truth.
- Open-Source FPGA Implementation of an I3C Controller, MDPI 2025.
- ADR-0005 — Preamble wire format (Option A) with forward-compatibility
  to bitmap and table forms.
- ADR-0006 — TLV length encoding.
- ADR-0007 — TLV nesting deferred.
- ADR-0008 — TLV maximum block size.
- ADR-0009 — Efficiency Principle.
- [MIPI I3C Basic terms and conditions](https://www.mipi.org/terms-conditions-i3c-basic).
- [MIPI I3C frequently asked questions](https://www.mipi.org/resources/i3c-frequently-asked-questions).
- [Public Bus Context Byte registry](https://www.mipi.org/mipi_i3c_bus_context_byte_values_public.html).
- [Public Mandatory Data Byte registry](https://www.mipi.org/MIPI_I3C_mandatory_data_byte_values_public).
- ADR-0015 — I3C Basic v1.2 standards alignment.

---

## Appendix A: Non-normative examples

### A.1 Minimal EX-1 preamble

A transaction declaring capability level EX-1 (metadata envelope only)
with no extension bytes and no reserved bits set:

```
Binary:   1 001 0 000
Hex:      0x90     (= 0x80 | (1 << 4))
```

Breakdown:
- Bit 7 (EX-present)        = 1
- Bits 6-4 (level=EX-1)     = 001
- Bit 3 (extension-follows) = 0
- Bits 2-0 (reserved)       = 000

### A.2 EX-6 preamble with no extension

A transaction declaring capability level EX-6 (all sublayers active):

```
Binary:   1 110 0 000
Hex:      0xE0     (= 0x80 | (6 << 4))
```

Breakdown:
- Bit 7 (EX-present)        = 1
- Bits 6-4 (level=EX-6)     = 110
- Bit 3 (extension-follows) = 0
- Bits 2-0 (reserved)       = 000

### A.3 Invalid preamble (reserved bit non-zero)

A v0.1 decoder MUST reject the following preamble because bit 0 is
set, which is reserved:

```
Binary:   1 001 0 001
Hex:      0x91
```

### A.4 Complete encoding table for all valid preamble levels

For reference, the full set of valid v0.1 preamble bytes is:

| Level | Name  | Encoded byte | Binary      |
|-------|-------|--------------|-------------|
| 0     | EX-0  | 0x80         | 1 000 0 000 |
| 1     | EX-1  | 0x90         | 1 001 0 000 |
| 2     | EX-2  | 0xA0         | 1 010 0 000 |
| 3     | EX-3  | 0xB0         | 1 011 0 000 |
| 4     | EX-4  | 0xC0         | 1 100 0 000 |
| 5     | EX-5  | 0xD0         | 1 101 0 000 |
| 6     | EX-6  | 0xE0         | 1 110 0 000 |
| 7     | ---   | reserved     | ---         |

### A.5 Minimal single-record TLV block

A TLV block containing one record of Type 0x00 (an EX-1 envelope
record), Length 4, Value = `0x01 0x02 0x03 0x04`:

```
Bytes: 0x00 0x04 0x01 0x02 0x03 0x04
       ^^^^ ^^^^ ^^^^^^^^^^^^^^^^^^^
       Type Len  Value (4 bytes)
```

Total block size: 6 bytes.

### A.6 Multi-record TLV block

A TLV block containing two records: an EX-1 envelope (Type 0x00,
3-byte Value) followed by an EX-3 fusion record (Type 0x20, 2-byte
Value):

```
Bytes: 0x00 0x03 0xAA 0xBB 0xCC 0x20 0x02 0xDE 0xAD
       ^^^^ ^^^^ ^^^^^^^^^^^^^^ ^^^^ ^^^^ ^^^^^^^^^
       T    L    V (envelope)   T    L    V (fusion)
```

Total block size: 9 bytes.

### A.7 Rejected TLV record (reserved Type 0xFE)

A v0.1 decoder MUST reject any record beginning with Type 0xFE:

```
Bytes: 0xFE 0x00
       ^^^^ ^^^^
       Type Len (reserved by Section 5.2.2)
```

### A.8 Rejected TLV record (reserved Length range)

A v0.1 decoder MUST reject any record whose Length byte has the high
bit set:

```
Bytes: 0x00 0x80 ...
            ^^^^
            Length with high bit set; reserved by Section 5.2.1.2
```

Further examples (EX-3 fusion with disagreement, EX-4 cross-bus
timestamp correlation) are `[TBD]`.

---

## Appendix B: Open questions tracker

This appendix tracks unresolved design questions. Once resolved, the
question moves into the main body of the specification and is removed
from this list.

1. Which framing strategy wins the comparative bakeoff? (Section 5)
2. Assigned SETBUSCON Context Byte for public I3C-EX use. (Section 4.2)
3. Exact directed standards/vendor extension CCC mechanism and assignment for
   `EXDISC`. (Section 4.2)
4. Permitted or assigned MDB semantics for optional IBI use. (Section 6.4)
5. Timestamp width and clock reference semantics. (Section 6.1, 6.4)
6. Relationship between EX checksum and I3C parity. (Section 6.1)
7. HDR-mode extension path. (Section 4.3)
8. Detailed Type-value allocation within each sublayer range. (Section 5.2.1.1)
9. Overhead Analysis sections for each sublayer per the Efficiency
   Principle. (Section 6, GOVERNANCE, ADR-0009)

### Resolved

- ~~Preamble bit layout.~~ See ADR-0005 and Section 5.1.
- ~~TLV length encoding — fixed vs variable.~~ See ADR-0006 and
  Section 5.2.1.2. Fixed 1-byte, 0-127 range; 0x80-0xFF reserved.
- ~~Nested TLV semantics.~~ See ADR-0007 and Section 5.2.2. Flat
  only in v0.1; Type 0xFE reserved for future container semantics.
- ~~Maximum TLV block size.~~ See ADR-0008 and Section 5.2.3.
  Device-negotiated, default 4096 bytes, no minimum floor,
  advertised in the directed `EXDISC` response and further constrained by the
  applicable SETMRL/SETMWL-derived content budget.

---

*End of I3CEX-0.2.0-draft.md*
