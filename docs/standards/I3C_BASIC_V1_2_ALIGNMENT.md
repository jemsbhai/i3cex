# I3C Basic v1.2 alignment policy

**Status:** Normative project policy  
**Date:** 2026-07-15

This policy defines the boundary between the external I3C Basic standard and
the independent I3C-EX research protocol.

## Compatibility baseline

The compatibility baseline is the public **MIPI Alliance Specification for
I3C Basic, Version 1.2**, adopted 17 April 2025, plus subsequently published
errata. Published MIPI FAQ corrections are tracked as implementation guidance
until they appear in an erratum or a newer public specification.

Official sources:

- [MIPI I3C specification page](https://www.mipi.org/specifications/i3c-sensor-specification)
- [I3C Basic terms and conditions](https://www.mipi.org/terms-conditions-i3c-basic)
- [I3C frequently asked questions](https://www.mipi.org/resources/i3c-frequently-asked-questions)
- [Public I3C FAQ PDF](https://www.mipi.org/hubfs/I3C-Resources/MIPI-I3C-v1-2-FAQs-public-edition.pdf)
- [Public Bus Context Byte registry](https://www.mipi.org/mipi_i3c_bus_context_byte_values_public.html)
- [Public Mandatory Data Byte registry](https://www.mipi.org/MIPI_I3C_mandatory_data_byte_values_public)
- [MIPI I3C conformance test suite](https://www.mipi.org/i3c-test-suite-download)

The repository does not copy these materials. Contributors must consult the
official versions and comply with their applicable terms.

## Layer and claim boundary

| Responsibility | Authority and evidence |
|---|---|
| Electrical signalling, timing, bus states, addressing, DAA, arbitration, base CCCs, Private SDR transfer rules, IBI rules, SETMRL, and SETMWL | I3C Basic v1.2, published errata, and a separately validated base implementation |
| I3C-EX envelope, framing candidates, capability model, semantic sublayers, and I3C-EX vectors | The versioned I3C-EX specification and this repository |
| I3C Basic conformance claim | MIPI's applicable requirements and conformance process; never inferred from I3C-EX tests |
| I3C-EX conformance claim | The selected I3C-EX draft or release and its tests; never described as MIPI certification |

I3C-EX is a content protocol based on I3C Basic. It does not amend or replace
I3C Basic and does not define a new I3C transfer mode.

## Integration rules

1. I3C-EX content MUST use standard Private SDR Read/Write transfers in this
   draft. HDR support is out of scope.
2. Extension semantics MUST be disabled after reset and DAA. They become
   eligible only after the controller selects an assigned I3C-EX Context Byte
   with SETBUSCON for the relevant bus context.
3. Capability discovery MUST use a directed standards/vendor extension CCC,
   not a custom broadcast CCC, after context selection. Its encoding and value
   remain undefined until a suitable allocation is confirmed.
4. Unknown, legacy, or non-negotiating targets remain ordinary I3C targets.
   Controllers MUST NOT send them I3C-EX content.
5. The I3C-EX payload limit for each direction MUST NOT exceed the applicable
   transfer budget derived from SETMRL or SETMWL after base-protocol and
   I3C-EX framing overhead.
6. Any IBI or Mandatory Data Byte use MUST follow I3C Basic and the public MDB
   registry. No project-specific MDB is currently assigned.
7. Implementation-specific firmware-only deployment claims MUST be supported
   by evidence that the hardware exposes every required base mechanism.

## Identifier status

| Mechanism | Draft status | Release gate |
|---|---|---|
| SETBUSCON Context Byte | Unassigned | Obtain or coordinate an appropriate public assignment before interoperable release |
| Directed extension CCC (`EXDISC`) | Symbolic; no numeric value | Confirm the standards/vendor extension mechanism and assignment with MIPI |
| IBI Mandatory Data Byte | Unassigned | Use only a registered permitted value or obtain an assignment |
| Manufacturer-specific identifiers | Device-specific only | Must not be presented as a public multi-vendor I3C-EX allocation |

For closed experiments, an explicitly configured Context Byte in the 192-255
private-use range may be used. Experimental values MUST be documented in the
experiment manifest, MUST NOT be enabled by default, and MUST NOT be advertised
as stable or interoperable allocations.

## Release gates

Before an I3C-EX specification can advance beyond draft:

- the exact I3C Basic revision and errata set are recorded;
- every normative dependency on I3C is mapped to its official mechanism;
- public identifier requirements are resolved or the feature is removed;
- at least one independently validated base I3C implementation is exercised;
- base I3C and I3C-EX results are reported separately;
- no test, document, badge, or package implies MIPI endorsement; and
- the naming and marks notice has received appropriate review.

See [ADR-0015](../adr/0015-i3c-basic-v1.2-standards-alignment.md) for the decision
and the repository [NOTICE](https://github.com/jemsbhai/i3cex/blob/main/NOTICE.md)
for the public disclaimer.
