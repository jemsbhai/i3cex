# i3cex

Extension layers for MIPI I3C targeting edge AI and edge ML workloads.

> **Pre-alpha**. Specification and implementation are in flux. Not yet
> published to PyPI. See [`../specs/I3CEX-0.1.0-draft.md`](../specs/I3CEX-0.1.0-draft.md)
> for the current specification draft.

## What is I3C-EX?

I3C-EX is a set of optional, backward-compatible extension layers atop
MIPI I3C. It adds metadata envelopes, QoS negotiation, Byzantine fusion
signalling, distributed timestamping, provenance/attestation, and
confidence propagation — all as optional sublayers that run on existing
I3C hardware with firmware updates only.

See the top-level [`../README.md`](../README.md) for project motivation
and dual-track strategy, and [`../GOVERNANCE.md`](../GOVERNANCE.md) for
development standards.

## Installation (once published)

```bash
pip install i3cex                   # core library
pip install "i3cex[sim]"            # with pure-Python simulator extras
pip install "i3cex[cosim]"          # with cocotb cosimulation (Linux/WSL2)
pip install "i3cex[dev]"            # development tooling
```

## Development

### Prerequisites

- Python 3.11 or later (3.12+ recommended).
- [Hatch](https://hatch.pypa.io/) for environment management
  (`pipx install hatch`).
- For cosimulation only: Linux or WSL2, Verilator 5.012+, Icarus Verilog 12.0+.

### Setup

```bash
# From repository root:
cd i3cex

# Create the dev environment
hatch env create

# Run unit and property tests
hatch run test

# Run full test suite with coverage
hatch run cov

# Run linter
hatch run lint

# Run type checker
hatch run typecheck

# Run all quality checks
hatch run check
```

### Project Structure

```
i3cex/
├── pyproject.toml              Hatch-based build configuration
├── README.md                   This file
├── LICENSE                     MIT
├── CHANGELOG.md                Keep-a-changelog format
├── .gitignore
├── .pre-commit-config.yaml     Ruff + mypy on every commit
├── src/
│   └── i3cex/
│       ├── __init__.py         Package root, version exported
│       ├── py.typed            PEP 561 marker
│       ├── framing/            Wire-level framing strategies
│       │   ├── __init__.py
│       │   ├── preamble.py     Candidate A: preamble-byte framing
│       │   └── tlv.py          Candidate B: TLV framing
│       ├── envelope/           EX-1: metadata envelope sublayer
│       │   └── __init__.py
│       ├── qos/                EX-2: quality-of-service (stub)
│       │   └── __init__.py
│       ├── fusion/             EX-3: Byzantine fusion signalling (stub)
│       │   └── __init__.py
│       ├── timesync/           EX-4: distributed timestamping (stub)
│       │   └── __init__.py
│       ├── provenance/         EX-5: provenance/attestation (stub)
│       │   └── __init__.py
│       ├── confidence/         EX-6: confidence propagation (stub)
│       │   └── __init__.py
│       └── sim/                Pure-Python I3C/I3C-EX simulator
│           └── __init__.py
├── tests/
│   ├── unit/                   Fast pure-function tests
│   ├── property/               Hypothesis-based generative tests
│   ├── integration/            Multi-component, uses sim
│   ├── cosim/                  cocotb tests vs chipsalliance/i3c-core RTL
│   └── vectors/                Normative test vectors (spec conformance)
└── docs/
    └── adr/                    Architecture Decision Records
```

## Testing Philosophy

See [`../GOVERNANCE.md`](../GOVERNANCE.md) for the full statement. Summary:

- **Strict TDD.** No implementation code lands without a failing test first.
- **Four test layers.** Unit, property, integration, cosim.
- **Coverage targets.** 95%+ line / 90%+ branch for core; 85%+ for
  utility; 80%+ for sim.
- **Property tests are mandatory for parsers and framers.** Every wire
  format decoder MUST have a `hypothesis` roundtrip test.
- **Pre-registered specifications.** The spec in `../specs/` is written
  first; code tracks the spec.

## Sublayer Roadmap

I3C-EX sublayers are implemented sequentially:

1. **EX-1 metadata envelope** — in progress (v0.1.0).
2. **EX-2 QoS negotiation** — after EX-1 stabilises.
3. **EX-3 Byzantine fusion** — after EX-2.
4. **EX-4 distributed timestamping** — after EX-3.
5. **EX-5 provenance/attestation** — after EX-4.
6. **EX-6 confidence propagation** — after EX-5.

Framing strategy (preamble-byte vs TLV) is chosen empirically before
EX-1 stabilises; see [`../specs/I3CEX-0.1.0-draft.md`](../specs/I3CEX-0.1.0-draft.md)
section 5.

## License

MIT. See [`LICENSE`](./LICENSE).
