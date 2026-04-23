"""Unit tests for Option A preamble framing: known-good wire vectors.

These vectors are derived directly from I3C-EX v0.1 specification
Appendix A. They MUST produce bit-exact wire output; any deviation
indicates a bug in either the specification or the implementation.

Vectors live in ``tests/vectors/v0.1.0-draft/framing/preamble/`` as
JSON files for conformance-suite use. The tests here are the
implementation-side check.
"""

from __future__ import annotations

import pytest

from i3cex.framing.preamble import (
    Preamble,
    PreambleDecodeError,
    decode_option_a,
    encode_option_a,
)

# ---------------------------------------------------------------------------
# Spec Appendix A.1: Minimal EX-1 preamble
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_spec_appendix_a1_minimal_ex1_encodes_to_0x90() -> None:
    """Spec A.1: EX-1, no ext-follows, reserved=0 MUST encode to 0x90."""
    preamble = Preamble(
        capability_level=1,
        sublayer_bitmap=0b0000_0001,  # (1 << 1) - 1
        extension_follows=False,
        version=1,
    )
    assert encode_option_a(preamble) == b"\x90"


@pytest.mark.unit
def test_spec_appendix_a1_minimal_ex1_decodes_correctly() -> None:
    """Spec A.1: 0x90 MUST decode to EX-1 with bitmap=0x01."""
    decoded, remaining = decode_option_a(b"\x90")
    assert decoded == Preamble(
        capability_level=1,
        sublayer_bitmap=0b0000_0001,
        extension_follows=False,
        version=1,
    )
    assert remaining == b""


# ---------------------------------------------------------------------------
# Spec Appendix A.2: EX-6 preamble with no extension
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_spec_appendix_a2_ex6_encodes_to_0xe0() -> None:
    """Spec A.2: EX-6, no ext-follows, reserved=0 MUST encode to 0xE0.

    The value is (1 << 7) | (6 << 4) = 0x80 | 0x60 = 0xE0.
    """
    preamble = Preamble(
        capability_level=6,
        sublayer_bitmap=0b0011_1111,  # (1 << 6) - 1
        extension_follows=False,
        version=1,
    )
    assert encode_option_a(preamble) == b"\xe0"


@pytest.mark.unit
def test_spec_appendix_a2_ex6_decodes_correctly() -> None:
    """Spec A.2: 0xE0 MUST decode to EX-6 with bitmap=0x3F."""
    decoded, remaining = decode_option_a(b"\xe0")
    assert decoded == Preamble(
        capability_level=6,
        sublayer_bitmap=0b0011_1111,
        extension_follows=False,
        version=1,
    )
    assert remaining == b""


# ---------------------------------------------------------------------------
# Spec Appendix A.3: Invalid preamble (reserved bit non-zero)
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_spec_appendix_a3_invalid_preamble_rejected() -> None:
    """Spec A.3: 0x91 (EX-1 with reserved bit 0 set) MUST be rejected."""
    with pytest.raises(PreambleDecodeError):
        decode_option_a(b"\x91")


# ---------------------------------------------------------------------------
# Comprehensive encoding table for all v0.1 valid levels (Spec A.4)
# ---------------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.parametrize(
    ("level", "expected_byte"),
    [
        # level, expected encoded byte: (1 << 7) | (level << 4)
        (0, 0x80),  # EX-0 (negotiation only): 0b1000_0000
        (1, 0x90),  # EX-1:                    0b1001_0000
        (2, 0xA0),  # EX-2:                    0b1010_0000
        (3, 0xB0),  # EX-3:                    0b1011_0000
        (4, 0xC0),  # EX-4:                    0b1100_0000
        (5, 0xD0),  # EX-5:                    0b1101_0000
        (6, 0xE0),  # EX-6:                    0b1110_0000
    ],
)
def test_encode_all_valid_levels(level: int, expected_byte: int) -> None:
    """Every valid v0.1 capability level MUST encode to its canonical byte."""
    preamble = Preamble(
        capability_level=level,
        sublayer_bitmap=(1 << level) - 1,
        extension_follows=False,
        version=1,
    )
    assert encode_option_a(preamble) == bytes([expected_byte])


@pytest.mark.unit
@pytest.mark.parametrize(
    ("input_byte", "expected_level", "expected_bitmap"),
    [
        (0x80, 0, 0b0000_0000),
        (0x90, 1, 0b0000_0001),
        (0xA0, 2, 0b0000_0011),
        (0xB0, 3, 0b0000_0111),
        (0xC0, 4, 0b0000_1111),
        (0xD0, 5, 0b0001_1111),
        (0xE0, 6, 0b0011_1111),
    ],
)
def test_decode_all_valid_levels(
    input_byte: int, expected_level: int, expected_bitmap: int
) -> None:
    """Every valid v0.1 encoded byte MUST decode to its canonical Preamble."""
    decoded, remaining = decode_option_a(bytes([input_byte]))
    assert decoded.capability_level == expected_level
    assert decoded.sublayer_bitmap == expected_bitmap
    assert decoded.extension_follows is False
    assert decoded.version == 1
    assert remaining == b""


@pytest.mark.unit
def test_decode_reserved_level_7_rejected() -> None:
    """Level 7 is reserved in v0.1; decoding MUST reject 0xF0."""
    with pytest.raises(PreambleDecodeError):
        decode_option_a(b"\xf0")
