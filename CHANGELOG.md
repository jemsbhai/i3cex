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
  3 spec Appendix A vectors (0x90, 0xC0, 0x91) and parametrised
  coverage of all 7 valid capability levels.
- `tests/property/framing/test_preamble.py`: 9 Hypothesis property
  tests covering:
  - Roundtrip invariant `decode(encode(p)) == p`.
  - Roundtrip with trailing payload bytes.
  - Byte-count invariant (always 1 byte in v0.1).
  - Reserved-bits-are-zero invariant.
  - EX-present-flag-is-set invariant.
  - Extension-follows-is-zero-in-v01 invariant.
  - Decode rejects non-zero reserved bits.
  - Encode rejects reserved level 7.
  - Encode rejects non-monotonic bitmap.
  - Decode rejects empty input.
  - Decode rejects zero EX-present flag.

### Changed

- Coverage floor (`--cov-fail-under`) raised from 0 to 60 now that
  real code is landing. Will ratchet up toward 95% as sublayers are
  implemented.
