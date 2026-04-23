"""Property-based tests for Option A preamble-byte framing.

These tests verify the core invariants of the Option A wire format
per the I3C-EX v0.1 specification section 5.1:

- Roundtrip: decode(encode(p)) == p for every valid Preamble.
- Byte-count: encode always produces exactly 1 byte for v0.1 (bit 3 = 0).
- Reserved-bit discipline: encode always emits zero for bits 2-0.
- EX-present flag: encode always emits 1 for bit 7.
- Rejection: decode rejects bytes with any reserved bit non-zero.

Hypothesis strategies constrain test inputs to the v0.1 valid domain:
capability_level in 0..6, extension_follows=False, version=1. Out-of-
domain inputs are tested separately as rejection cases.
"""

from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st

from i3cex.framing.preamble import (
    Preamble,
    PreambleDecodeError,
    PreambleEncodeError,
    decode_option_a,
    encode_option_a,
)

# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

# Valid v0.1 capability levels. 0 is EX-0 (negotiation only); 1..6 are
# EX-1..EX-6. Level 7 is reserved and MUST NOT be emitted.
valid_capability_levels = st.integers(min_value=0, max_value=6)


@st.composite
def valid_v01_preambles(draw: st.DrawFn) -> Preamble:
    """Hypothesis strategy generating valid v0.1 Option-A Preambles.

    v0.1 constrains:
    - capability_level in [0, 6]
    - extension_follows is False (bit 3 = 0 in v0.1)
    - version == 1
    - sublayer_bitmap is level-monotonic: (1 << level) - 1
    """
    level = draw(valid_capability_levels)
    return Preamble(
        capability_level=level,
        sublayer_bitmap=(1 << level) - 1,
        extension_follows=False,
        version=1,
    )


# ---------------------------------------------------------------------------
# Roundtrip invariant
# ---------------------------------------------------------------------------


@pytest.mark.property
@given(preamble=valid_v01_preambles())
def test_roundtrip_preamble_preserves_value(preamble: Preamble) -> None:
    """decode(encode(p)) MUST equal p for every valid v0.1 Preamble."""
    encoded = encode_option_a(preamble)
    decoded, remaining = decode_option_a(encoded)
    assert decoded == preamble
    assert remaining == b"", "Option A v0.1 preamble MUST consume exactly 1 byte"


@pytest.mark.property
@given(preamble=valid_v01_preambles(), payload=st.binary(max_size=256))
def test_roundtrip_with_trailing_payload(preamble: Preamble, payload: bytes) -> None:
    """decode MUST correctly separate the preamble from trailing payload bytes."""
    encoded = encode_option_a(preamble) + payload
    decoded, remaining = decode_option_a(encoded)
    assert decoded == preamble
    assert remaining == payload


# ---------------------------------------------------------------------------
# Byte-count invariant
# ---------------------------------------------------------------------------


@pytest.mark.property
@given(preamble=valid_v01_preambles())
def test_encode_produces_exactly_one_byte(preamble: Preamble) -> None:
    """v0.1 Option-A encode MUST produce a 1-byte result (bit 3 = 0)."""
    encoded = encode_option_a(preamble)
    assert len(encoded) == 1


# ---------------------------------------------------------------------------
# Bit-discipline invariants
# ---------------------------------------------------------------------------


@pytest.mark.property
@given(preamble=valid_v01_preambles())
def test_encoded_reserved_bits_are_zero(preamble: Preamble) -> None:
    """Bits 2-0 of the encoded byte MUST be zero per v0.1 spec section 5.1.2."""
    encoded = encode_option_a(preamble)
    assert (encoded[0] & 0b0000_0111) == 0


@pytest.mark.property
@given(preamble=valid_v01_preambles())
def test_encoded_ex_present_flag_is_set(preamble: Preamble) -> None:
    """Bit 7 (EX-present) MUST be 1 for every encoded preamble."""
    encoded = encode_option_a(preamble)
    assert (encoded[0] & 0b1000_0000) != 0


@pytest.mark.property
@given(preamble=valid_v01_preambles())
def test_encoded_extension_follows_is_zero_in_v01(preamble: Preamble) -> None:
    """Bit 3 (extension-follows) MUST be 0 in v0.1."""
    encoded = encode_option_a(preamble)
    assert (encoded[0] & 0b0000_1000) == 0


# ---------------------------------------------------------------------------
# Rejection invariants
# ---------------------------------------------------------------------------


@pytest.mark.property
@given(reserved_bits=st.integers(min_value=1, max_value=7))
def test_decode_rejects_nonzero_reserved_bits(reserved_bits: int) -> None:
    """Decoding MUST reject any byte with non-zero reserved bits (bits 2-0).

    Per v0.1 spec section 5.1.2: ``Receivers decoding a v0.1 frame MUST
    reject any frame with a non-zero reserved bit.``
    """
    # Construct a byte with EX-present=1, level=1 (EX-1), ext=0, and
    # reserved=non-zero.
    byte = 0b1001_0000 | reserved_bits
    with pytest.raises(PreambleDecodeError):
        decode_option_a(bytes([byte]))


@pytest.mark.property
@given(level=st.integers(min_value=7, max_value=7))
def test_encode_rejects_reserved_capability_level(level: int) -> None:
    """Encoding MUST reject capability level 7 (reserved in v0.1)."""
    with pytest.raises(PreambleEncodeError):
        encode_option_a(
            Preamble(
                capability_level=level,
                sublayer_bitmap=(1 << level) - 1,
                extension_follows=False,
                version=1,
            )
        )


@pytest.mark.property
@given(
    level=valid_capability_levels,
    bogus_bitmap=st.integers(min_value=0, max_value=255),
)
def test_encode_rejects_non_monotonic_bitmap(level: int, bogus_bitmap: int) -> None:
    """Encoding MUST reject a Preamble whose bitmap is not level-monotonic.

    Option A can only represent bitmaps of the form ``(1 << level) - 1``
    (all sublayers 1..N present). Any other bitmap is information the
    wire format cannot faithfully encode.
    """
    correct_bitmap = (1 << level) - 1
    if bogus_bitmap == correct_bitmap:
        # This case would be valid; skip it.
        return
    with pytest.raises(PreambleEncodeError):
        encode_option_a(
            Preamble(
                capability_level=level,
                sublayer_bitmap=bogus_bitmap,
                extension_follows=False,
                version=1,
            )
        )


@pytest.mark.property
def test_decode_rejects_empty_input() -> None:
    """Decoding an empty byte sequence MUST raise."""
    with pytest.raises(PreambleDecodeError):
        decode_option_a(b"")


@pytest.mark.property
def test_decode_rejects_zero_ex_present_flag() -> None:
    """Decoding MUST reject a byte with bit 7 = 0 (EX-present flag unset).

    Per v0.1 spec section 5.1.3: ``if [the EX-present flag] is zero, the
    receiver MUST treat the frame as non-EX and process it per legacy
    I3C semantics.`` In the library API, this means decode_option_a
    raises, and higher layers are expected to catch that and dispatch
    to legacy handling.
    """
    byte = 0b0001_0000  # bit 7 = 0; everything else fine
    with pytest.raises(PreambleDecodeError):
        decode_option_a(bytes([byte]))
