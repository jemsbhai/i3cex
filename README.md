# I3C-EX

I3C-EX is an independent research project exploring a higher-layer content
protocol for edge AI/ML metadata and coordination over MIPI I3C Basic.

> **Independent pre-alpha research.** This project is not affiliated with,
> sponsored by, approved by, or endorsed by MIPI Alliance. I3C and I3C Basic
> are MIPI Alliance specifications and marks. See [NOTICE.md](./NOTICE.md).

The current compatibility target is the publicly available **MIPI I3C Basic
v1.2** specification, adopted 17 April 2025, together with its published
errata. I3C-EX does not alter I3C signalling, addressing, arbitration, or
base framing. It proposes optional content carried in standard Private SDR
Read/Write transfers after explicit, context-scoped negotiation.

## Status

- Current specification: [I3CEX-0.2.0-draft](./specs/I3CEX-0.2.0-draft.md).
- Implemented: the two experimental framing candidates, preamble and TLV.
- Not implemented: discovery, base-bus integration, simulator, cosimulation,
  and the six proposed semantic sublayers.
- Not published to PyPI.
- No MIPI Context Byte, extension CCC, or Mandatory Data Byte value has been
  assigned to this project. Draft names are symbolic and have no wire value.

The project is intended to produce a reproducible research paper and, if the
evidence supports it, a future proposal to MIPI Alliance. It does not claim
MIPI conformance, certification, or endorsement.

## Architecture boundary

I3C-EX is a content protocol based on I3C Basic, not a replacement or modified
edition of I3C. A conforming experiment uses:

1. a separately conforming I3C Basic v1.2 controller and target;
2. standard Private SDR Read/Write transfers for I3C-EX data;
3. SETBUSCON with an assigned Context Byte before I3C-EX semantics are enabled;
4. a directed extension CCC, once assigned, for capability discovery only; and
5. the base transfer limits established by SETMRL and SETMWL.

Until public identifiers are assigned, experiments may use only deliberately
configured private values in the MIPI-reserved private range and must not
represent those values as interoperable allocations. See the normative
[standards alignment policy](./docs/standards/I3C_BASIC_V1_2_ALIGNMENT.md).

Existing hardware may be usable where its controller and target interfaces
already expose the required Private SDR, SETBUSCON, directed extension CCC,
and optional IBI facilities. A firmware update alone is therefore a platform-
specific possibility, not a universal compatibility claim.

## Research roadmap

The first milestone is a framing bakeoff, using the pre-registered methodology
in [ADR-0010](./docs/adr/0010-bakeoff-evaluation-methodology.md). Accepted
ADR-0011 through ADR-0014 define cross-language runtime measurement and the
extensibility taxonomy, coverage, outcomes, and decision rule. Only after the
remaining methodology family and machine-readable experiment manifest are
frozen will the benchmark harness be implemented.

Proposed sublayers are developed sequentially:

1. EX-1 metadata envelope
2. EX-2 quality-of-service negotiation
3. EX-3 Byzantine fusion signalling
4. EX-4 distributed timestamping
5. EX-5 provenance and attestation
6. EX-6 confidence propagation and extended error reporting

## Development

Requirements are Python 3.11 or later and
[Hatch](https://hatch.pypa.io/). From the repository root:

```bash
hatch env create
hatch run test
hatch run cov
hatch run lint
hatch run typecheck
hatch run check
hatch run docs:build
```

The test tree separates unit, property, integration, optional RTL cosimulation,
and protocol-vector tests. See [GOVERNANCE.md](./GOVERNANCE.md) for contribution,
quality, publication, and standards-boundary rules.

## Repository layout

```text
src/i3cex/          Python reference implementation
tests/              Unit, property, integration, cosim, and vector tests
specs/              Versioned I3C-EX specification drafts
docs/adr/           Architecture decision records
docs/standards/     Standards alignment and conformance boundary
experiments/        Frozen experiment manifests and reproducibility metadata
scripts/            Cross-platform development helpers
```

## License

The project's original code and documents are licensed under the MIT License.
That license does not apply to MIPI specifications, MIPI marks, third-party
materials, or patent rights. See [LICENSE](./LICENSE) and [NOTICE.md](./NOTICE.md).
