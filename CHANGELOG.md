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
  tests covering previously-uncovered rejection branches.
- `tests/property/framing/test_preamble.py`: 9 Hypothesis property
  tests covering roundtrip, byte-count, bit-discipline, and
  rejection invariants.

#### TLV framing design (ADRs)

- ADR-0006: TLV length encoding — fixed 1-byte, 0-127 range; Length
  values 0x80-0xFF reserved for Path beta future extension.
- ADR-0007: TLV nesting deferred. v0.1 records are flat. Type 0xFE
  reserved as placeholder for future container semantics.
- ADR-0008: TLV maximum block size. Device-negotiated, advertised in
  EX-Discovery CCC response. Default 4096 bytes when unadvertised.
  No minimum floor.
- ADR-0009: Efficiency Principle. Every sublayer specification MUST
  include an Overhead Analysis section.
- ADR index updated.

#### Framing: TLV block encoder/decoder (Candidate B)

- `src/i3cex/framing/tlv.py`: second framing implementation. Encodes
  and decodes the TLV wire format per spec v0.1 section 5.2 and
  ADRs 0006/0007/0008:
  - `TLVRecord` frozen dataclass with `type_` and `value` fields.
  - `encode_tlv_block(records, max_size=4096)` with full invariant
    enforcement: rejects out-of-range Type, reserved Type 0xFE,
    Value length > 127, and total block size > max_size.
  - `decode_tlv_block(data, max_size=4096)` with full rejection
    discipline: rejects blocks exceeding max_size, reserved Type
    0xFE, Length bytes >= 0x80, truncated headers, and truncated
    Value fields.
  - Exported constants: `DEFAULT_MAX_TLV_BLOCK_SIZE_V01` (4096),
    `MAX_VALUE_LENGTH_V01` (127), `RESERVED_LENGTH_MIN` (0x80),
    `RESERVED_CONTAINER_TYPE` (0xFE), `MIN_TYPE_VALUE` (0x00),
    `MAX_TYPE_VALUE` (0xFF).
  - `TLVBlockEncodeError` and `TLVBlockDecodeError` exception types.
- `tests/unit/framing/test_tlv.py`: 21 unit tests covering all spec
  Appendix A examples (A.5 single record, A.6 multi-record, A.7
  reserved Type rejection, A.8 reserved Length rejection) plus
  parametrised coverage of every non-reserved Type range boundary
  and max-size negotiation behaviour.
- `tests/property/framing/test_tlv.py`: 15 Hypothesis property tests
  covering roundtrip, wire-size, Length-byte discipline, empty block,
  and encoder/decoder rejection invariants.

### Changed

- Coverage floor (`--cov-fail-under`) ratchet progression:
  - 0 -> 60 after initial preamble implementation.
  - 60 -> 80 after `preamble.py` hit 100%, overall 82%.
  - 80 -> 90 after `tlv.py` hit 100%, overall 91%.
- `src/i3cex/framing/__init__.py`: now exposes both the preamble API
  (`Preamble`, `encode_option_a`, `decode_option_a`, error types) and
  the TLV API (`TLVRecord`, `encode_tlv_block`, `decode_tlv_block`,
  error types, and constants).
