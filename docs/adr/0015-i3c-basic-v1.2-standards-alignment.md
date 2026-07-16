# ADR-0015: Align I3C-EX as an independent I3C Basic v1.2 content protocol

**Status:** Accepted  
**Date:** 2026-07-15

## Context

The original I3C-EX draft described a generic backward-compatible extension
and left discovery to an unspecified CCC. That was too loose for an
interoperability paper and could be read as changing I3C itself. The project is
not presently a MIPI member, adopter, contributor, or endorsed activity.

The current public baseline is I3C Basic v1.2. Its public integration mechanisms
include SETBUSCON context selection, Private SDR transfers, directed extension
CCCs, SETMRL/SETMWL limits, and registered IBI Mandatory Data Byte meanings.

ADR-0010 reserves ADR-0011 through ADR-0014 for the framing methodology family.
This decision therefore uses ADR-0015.

## Decision

I3C-EX is positioned as an **independent higher-layer content protocol based on
I3C Basic v1.2**, not as an amendment, new transfer mode, or certified extension
of I3C.

- I3C-EX data uses standard Private SDR Read/Write transfers.
- Extension semantics default to disabled and require SETBUSCON selection of an
  assigned I3C-EX Context Byte.
- Capability discovery is a directed extension CCC used only after that context
  is selected.
- All numeric identifiers remain undefined until an appropriate assignment is
  obtained. Private experimental values are opt-in and non-interoperable.
- SETMRL and SETMWL constrain the I3C-EX content budget.
- IBI usage is deferred until it can use a permitted registered MDB meaning.
- Base I3C Basic conformance and I3C-EX conformance are separate claims.
- Project materials carry a prominent no-affiliation/no-endorsement notice.
- The MIT License applies only to original project materials.

The normative details live in
[I3C_BASIC_V1_2_ALIGNMENT.md](../standards/I3C_BASIC_V1_2_ALIGNMENT.md).

## Alternatives considered

### Treat the framing byte as an implicit I3C extension marker

Rejected. Payload bytes have application meaning; a byte pattern cannot safely
claim new semantics without prior context and endpoint negotiation.

### Allocate a custom broadcast CCC

Rejected. A broadcast command risks changing the interpretation of unrelated
targets and bypasses the standard context mechanism.

### Select private numeric identifiers as permanent values

Rejected. Private-use values support controlled experiments, not public
multi-vendor interoperability or a standards proposal.

### Wait for MIPI membership before publishing any research

Rejected. The public I3C Basic specification supports independent research and
implementation under its applicable terms. The project can publish original
work now while reserving formal standardization and identifiers for the proper
liaison or contribution process.

## Consequences

- The specification can make precise backward-compatibility claims without
  claiming MIPI approval.
- Discovery and interrupt integration remain incomplete until identifiers are
  coordinated.
- Hardware compatibility must be demonstrated platform by platform.
- Paper evaluation must report the base implementation and I3C-EX layer
  separately.
- A written naming/marks review and formal MIPI engagement remain release risks.
