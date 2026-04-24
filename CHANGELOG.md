# Changelog — i3cex

All notable changes to the `i3cex` package are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Pre-1.0.0 versions are understood to have unstable APIs; breaking changes
bump the `MINOR` component.

## [Unreleased]

### Added

#### Scaffolding

- Initial package scaffold following Hatch / PEP 517 conventions.
- `pyproject.toml` with strict ruff / strict mypy / pytest / hypothesis
  / coverage configuration, plus Hatch environment scripts (`test`,
  `test-all`, `cov`, `lint`, `fix`, `typecheck`, `check`, separate
  `cosim` and `docs` environments).
- `README.md`, `LICENSE` (MIT), `CHANGELOG.md`, `.gitignore`.
- `.pre-commit-config.yaml` with ruff + mypy + conventional-commits.
- `scripts/run_pytest.py` cross-platform pytest runner.
- Package skeleton with sublayer stubs for envelope, qos, fusion,
  timesync, provenance, confidence, and sim.
- Test tree with unit / property / integration / cosim / vectors
  layers and package-level sanity tests.
- CI workflow `.github/workflows/ci.yml`.

#### Framing: Option A preamble encoder/decoder

- `src/i3cex/framing/preamble.py`: first real implementation. Encodes
  and decodes the Option A 1-byte preamble wire format per spec v0.1
  section 5.1 and ADR-0005:
  - `Preamble` frozen dataclass modelling the full information space
    (wire-format-agnostic by design, supports future Option B / C
    migration without consumer changes).
  - `encode_option_a()` with full invariant enforcement: rejects
    non-v1 version, level > 6, non-monotonic bitmap, and
    `extension_follows=True`.
  - `decode_option_a()` with full rejection discipline: empty input,
    EX-present flag zero, non-zero reserved bits, level 7, set
    extension-follows flag.
  - Exported bit-mask constants (`EX_PRESENT_FLAG_MASK`, `LEVEL_MASK`,
    `LEVEL_SHIFT`, `EXTENSION_FOLLOWS_FLAG_MASK`, `RESERVED_BITS_MASK`,
    `MAX_CAPABILITY_LEVEL_V01`) for consumers that need wire-level
    manipulation.
  - `PreambleEncodeError` and `PreambleDecodeError` exception types.
- `tests/unit/framing/test_preamble.py`: 19 unit tests including all
  3 spec Appendix A vectors (0x90, 0xE0, 0x91) and parametrised
  coverage of all 7 valid capability levels.
- `tests/unit/framing/test_preamble_rejections.py`: 9 additional unit
  tests covering previously-uncovered rejection branches (version
  rejection with 5 parametrised cases, extension_follows=True
  encoder rejection, extension-follows decoder rejection with 3
  parametrised cases).
- `tests/property/framing/test_preamble.py`: 9 Hypothesis property
  tests covering roundtrip, byte-count, bit-discipline, and
  rejection invariants.

#### TLV framing design (ADRs only; implementation in a later commit)

- ADR-0006: TLV length encoding — fixed 1-byte, 0-127 range; Length
  values 0x80-0xFF reserved for Path β future extension.
- ADR-0007: TLV nesting deferred. v0.1 records are flat (no
  protocol-level nesting). Type 0xFE reserved as placeholder for
  future container semantics.
- ADR-0008: TLV maximum block size. Device-negotiated, advertised in
  EX-Discovery CCC response as a 2-byte field. Default 4096 bytes
  when unadvertised. No minimum floor; devices may advertise any
  cap >= 1. Effective cap for a (controller, target) pair is the
  minimum of the two advertised values.
- ADR-0009: Efficiency Principle. Every sublayer specification MUST
  include an Overhead Analysis section documenting worst-case bytes,
  parse complexity delta, bit-packing technique, and an explicit
  trade-off statement. Sanctioned and unsanctioned optimisation
  techniques enumerated.
- ADR index updated.

### Changed

- Coverage floor (`--cov-fail-under`) raised from 0 to 60 after
  initial preamble implementation landed, then ratcheted to 80
  after `preamble.py` reached 100% line and branch coverage.
