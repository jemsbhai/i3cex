# Governance, Versioning, and Development Standards

This document establishes the governance model, versioning scheme,
development practices, and quality standards for the I3C-EX and I4C
projects.

## Project Scope and Boundaries

This repository hosts two related but independent projects:

1. **I3C-EX**: An extension layer atop MIPI I3C. Lives in `i3cex/`.
2. **I4C**: A clean-slate redesign sharing I3C's physical layer. Lives
   in `i4c/`.

Specifications live in `specs/` for both projects. Each project has its
own package, CHANGELOG, and independent version trajectory.

## Versioning

### Specification Versioning

Specifications follow semantic versioning with the pattern
`PROJECT-MAJOR.MINOR.PATCH-STAGE` where stage is one of
`draft`, `rc`, or omitted for final releases.

- **MAJOR**: Breaking protocol changes (incompatible frame formats)
- **MINOR**: Backward-compatible additions (new optional sublayers)
- **PATCH**: Clarifications, errata, non-normative fixes
- **draft**: Specification under active development, breaking changes expected
- **rc**: Release candidate, stable unless critical issues found

Examples:
- `I3CEX-0.1.0-draft.md` — first draft, unstable
- `I3CEX-1.0.0-rc1.md` — first release candidate
- `I3CEX-1.0.0.md` — first stable release

### Software Versioning

Software packages follow [Semantic Versioning 2.0.0](https://semver.org).

Pre-1.0.0 rules:
- `0.x.y` versions are understood to have unstable APIs
- Breaking changes bump the `MINOR` component (e.g., `0.1.x` → `0.2.0`)
- `1.0.0` release is reserved for feature-complete, spec-stable state

Post-1.0.0 rules:
- Breaking changes bump `MAJOR`
- Feature additions bump `MINOR`
- Bug fixes and clarifications bump `PATCH`

## Development Standards

### Test-Driven Development (strict)

All code in this project follows strict TDD:

1. Write a failing test that encodes the desired behaviour
2. Write the minimum code to make the test pass
3. Refactor while keeping tests green

**No code is committed without an accompanying test.** Coverage targets:

- Core protocol logic: **95%+ line coverage, 90%+ branch coverage**
- Utility/infrastructure code: **85%+ line coverage**
- Simulation code: **80%+ line coverage**

Coverage is enforced in CI. PRs that reduce coverage below thresholds
are blocked.

### Testing Layers

Each package implements four layers of tests:

1. **Unit tests** (`tests/unit/`): Pure function, no I/O, no network,
   millisecond-scale. Use `pytest`.
2. **Property tests** (`tests/property/`): Hypothesis-based generative
   testing for parsers, framers, encoders. Every frame format MUST have
   a roundtrip property test.
3. **Integration tests** (`tests/integration/`): Multi-component
   interaction, uses the pure-Python simulator, second-scale.
4. **Cosimulation tests** (`tests/cosim/`, optional): cocotb-driven
   tests against chipsalliance/i3c-core RTL. Linux/WSL2 only. Excluded
   from default `pytest` runs; triggered explicitly via `make cosim`.

### Code Quality Tooling

All packages use the same toolchain:

- **Formatter**: `ruff format` (replaces `black`)
- **Linter**: `ruff check` with strict ruleset
- **Type checker**: `mypy --strict`
- **Pre-commit**: All of the above on every commit
- **Python version**: 3.12+ (3.11 minimum for compatibility with
  chipsalliance/i3c-core cocotb tests)

### Commit Conventions

[Conventional Commits](https://www.conventionalcommits.org/) are
required:

```
<type>(<scope>): <short description>

<body>

<footer>
```

Types: `feat`, `fix`, `docs`, `test`, `refactor`, `perf`, `chore`,
`ci`, `build`, `revert`, `spec`.

Scopes for this project: `i3cex`, `i4c`, `specs`, `sim`, `framing`,
`envelope`, `qos`, `fusion`, `ci`, `repo`.

Examples:
- `feat(framing): add TLV encoder with length-prefix validation`
- `spec(i3cex): draft section 3.2 on metadata envelope semantics`
- `test(envelope): add roundtrip property test for preamble framing`

### Changelog Discipline

Every package maintains a `CHANGELOG.md` following
[Keep a Changelog](https://keepachangelog.com/) format. Sections:
`Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Security`.

Each merged PR that changes user-visible behaviour MUST add a
changelog entry to the `[Unreleased]` section.

### Documentation

- **Code**: Google-style docstrings, typed signatures everywhere.
- **Specs**: Markdown, versioned, immutable once released. Drafts can
  change freely.
- **Design decisions**: Architecture Decision Records (ADRs) in
  `docs/adr/` for each package. One ADR per significant choice.

## Efficiency Principle

This section is normative. See [ADR-0009](./i3cex/docs/adr/0009-efficiency-principle.md)
for the full reasoning and alternatives considered.

> **Every I3C-EX sublayer specification MUST include an "Overhead
> Analysis" section documenting:**
>
> 1. **Worst-case bytes added per frame** by the sublayer, broken
>    down by record type.
> 2. **Parse complexity impact**, stated in terms of cyclomatic
>    complexity delta and worst-case cycles on a representative
>    constrained microcontroller (Cortex-M0 reference target).
> 3. **At least one bit-packing or amortisation technique applied**
>    to the sublayer's wire representation. Sublayers whose wire
>    representation uses byte-aligned fields where fewer bits would
>    suffice MUST document why the byte alignment was chosen.
> 4. **An explicit trade-off statement** in the form:
>    *"This sublayer adds X bytes to typical frames and Y cycles to
>    the decoder. The benefit is Z. This trade-off is justified
>    because W."*
>
> Sublayer specifications that do not satisfy this principle MUST
> NOT progress beyond `-draft` status.

### Sanctioned optimisation techniques

The following techniques are encouraged:

1. **Bit-packing within sublayer payloads.** Pack related fields to
   the bit level where possible. Required consideration for every
   sublayer.
2. **Reserved-bit forward-compatibility** (per ADR-0005 and ADR-0006).
3. **Sublayer-internal delta encoding** for streaming data. Stateful
   and sublayer-specific; does not affect the framing layer.
4. **Schema template negotiation** as a v0.2+ extension path.

### Unsanctioned techniques at v0.1

Documented to prevent accidental re-adoption:

1. Variable-length (varint) length encoding (rejected in ADR-0006).
2. Combo Types encoding multiple sublayers in one record.
3. Implicit-length Types (Type value implies a fixed Length).
4. Protocol-level record nesting (deferred in ADR-0007).

## Decision Log

This section records high-level project decisions. New decisions
append; existing decisions are not edited (superseding decisions get
new entries referencing the old).

### 2026-04-23: Dual-track architecture

**Decision**: Publish two papers sequentially. Paper 1 on I3C-EX as a
backward-compatible extension. Paper 2 on I4C as a principled
redesign informed by I3C-EX findings.

**Rationale**: Extension-first derisks adoption while building
evidence for the redesign case. Each paper stands alone but together
they form a stronger narrative arc.

**Alternatives considered**: (a) I3C-EX only — leaves redesign
opportunity on the table; (b) I4C only — harder to adopt and
publish without prior extension evidence.

### 2026-04-23: Framing strategy — comparative prototyping

**Decision**: Implement both preamble-byte framing and TLV framing
in the reference implementation. Benchmark both on overhead, parse
complexity, extensibility, and wire efficiency. Select the winner
based on evidence.

**Rationale**: Framing choice is a foundational design decision; the
comparison itself is publishable material.

### 2026-04-23: Sublayer development order

**Decision**: Sequential. Metadata envelope first, then QoS
negotiation, then Byzantine fusion, then distributed timestamping,
then provenance/attestation.

**Rationale**: Each sublayer builds on primitives from the previous.
Metadata envelope is foundational; everything else rides on it.

### 2026-04-23: Licensing — MIT

**Decision**: MIT license for both I3C-EX and I4C code and
specifications.

**Rationale**: Maximally permissive; encourages industry adoption.
Compatible with the Apache-2.0-licensed chipsalliance/i3c-core which
we will depend on for RTL cosimulation.

### 2026-04-23: Simulation strategy — hybrid stack

**Decision**: Three-layer simulation strategy.

1. **Pure Python behavioural simulator** (`i3cex.sim`) for fast TDD
   iteration on protocol logic. No hardware tooling required. Runs
   on Windows, Linux, macOS.
2. **chipsalliance/i3c-core RTL via cocotb + Verilator** for
   cycle-accurate validation. Linux/WSL2 only. Gated behind
   `make cosim`.
3. **FPGA deployment** (Paper 2 era) on Digilent Cora Z7 or DE10-Nano
   per the MDPI open-source I3C controller precedent.

**Rationale**: Pure Python enables rapid TDD; RTL cosim gives
publication-credible cycle accuracy; FPGA deployment closes the loop
for Paper 2.

### 2026-04-23: Python packaging — hatch

**Decision**: Use Hatch (PEP 517/518 native) over Poetry.

**Rationale**: Hatch is the current PyPA-aligned standard, uses
standard `pyproject.toml` without a proprietary lockfile, and has
better long-term maintenance trajectory.

### 2026-04-23: Preamble wire format (Option A)

**Decision**: Adopt Option A — 1-byte preamble with capability level,
extension-follows flag, and reserved bits — for v0.1, with documented
migration paths to 2-byte bitmap (Option B) and 1-byte table-indexed
(Option C) forms for future versions.

**Rationale**: Minimum wire overhead and trivial decoder; reserved-
bit discipline preserves forward compatibility. See ADR-0005.

### 2026-04-23: TLV length encoding

**Decision**: Fixed 1-byte Length field, 0-127 range. Values 0x80-0xFF
are reserved for future extension. Three migration paths (reserved
Type, high-bit Length extension, continuation records) are documented
for future use.

**Rationale**: Keeps TLV decoder complexity comparable to preamble
framing for a fair bakeoff; reserved-bit discipline matches the
forward-compatibility pattern established elsewhere. See ADR-0006.

### 2026-04-23: TLV nesting deferred

**Decision**: v0.1 TLV records are flat (no protocol-level nesting).
Type 0xFE is reserved as a placeholder for future container
semantics; v0.1 encoders MUST NOT emit it and v0.1 decoders MUST
reject it.

**Rationale**: Evidence-based — sublayer designs (EX-3/5/6) have not
yet demonstrated a need for hierarchy. Flat TLV keeps the bakeoff
fair against preamble framing. See ADR-0007.

### 2026-04-23: TLV maximum block size

**Decision**: Device-negotiated maximum block size, advertised in
the EX-Discovery CCC response as a 2-byte field. Default 4096 bytes
when unadvertised. No minimum floor; devices may advertise any
cap >= 1. Effective cap for a (controller, target) pair is the
minimum of the two advertised values.

**Rationale**: Flexibility across device classes without added per-
frame latency; init-time cost is 2 bytes of CCC payload. See ADR-0008.

### 2026-04-23: Efficiency Principle

**Decision**: Adopt a formal Efficiency Principle (see normative
section above) requiring every sublayer specification to include an
Overhead Analysis section with worst-case byte count, parse
complexity delta, a documented bit-packing or amortisation technique,
and an explicit trade-off statement.

**Rationale**: Prevents feature accretion at the specification stage;
establishes a publishable position on principled extension-layer
design for Paper 1. See ADR-0009.

## Publication Ethics

- All work is pre-registered via specification drafts in `specs/`
  before implementation begins. This creates an immutable record of
  the research hypothesis and design.
- Negative results are reported. If preamble framing loses to TLV,
  we publish that. If I3C-EX sublayer X turns out to be unnecessary,
  we publish that.
- All benchmarks are reproducible. Every experiment ships with:
  its exact code, the simulator version, the workload traces, and a
  runnable `make reproduce` target.
- Artifact evaluation readiness from day one. Every package is
  packaged and versioned such that reviewers can install and run
  experiments with a single command.

## Contribution Process

Until public release:

1. Work is tracked in the repository commit history.
2. Each significant change is accompanied by an ADR if design-level.
3. Specification drafts go through internal review before being
   committed as `-draft` versions.

Post public release (post-Paper-1 submission):

1. GitHub PRs required for all changes.
2. Two-reviewer approval for spec changes.
3. One-reviewer approval for code changes that don't modify specs.

## References

- MIPI I3C Basic v1.1.1 specification
- [chipsalliance/i3c-core](https://github.com/chipsalliance/i3c-core)
- [Semantic Versioning 2.0.0](https://semver.org)
- [Keep a Changelog](https://keepachangelog.com/)
- [Conventional Commits](https://www.conventionalcommits.org/)
