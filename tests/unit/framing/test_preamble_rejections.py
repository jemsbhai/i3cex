"""Rejection tests for Option A preamble encoder and decoder.

These tests exercise the remaining rejection branches of
``encode_option_a`` and ``decode_option_a`` that the spec-vector tests
in ``test_preamble.py`` and the generative tests in
``tests/property/framing/test_preamble.py`` do not explicitly cover.

Specifically:

- Encoder rejects ``version != 1`` (reserved for future spec versions).
- Encoder rejects ``extension_follows=True`` (reserved in v0.1).
- Decoder rejects an input byte whose extension-follows bit is set.

Together with the existing suite these tests bring ``preamble.py``
coverage to effectively 100% of reachable branches.
"""

from __future__ import annotations

import pytest

from i3cex.framing.preamble import (
    Preamble,
    PreambleDecodeError,
    PreambleEncodeError,
    decode_option_a,
    encode_option_a,
)

# ---------------------------------------------------------------------------
# Encoder rejection: unsupported version
# ---------------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.parametrize("bad_version", [0, 2, 3, 42, 255])
def test_encode_rejects_non_v1_version(bad_version: int) -> None:
    """Encoding MUST reject any Preamble whose version is not 1 in v0.1.

    Future specification versions will be handled by new encode
    functions; the v0.1 Option A encoder MUST NOT silently accept a
    Preamble that claims to be a different version.
    """
    # Use an otherwise-valid preamble body so only the version field
    # is the cause of rejection.
    with pytest.raises(PreambleEncodeError, match="version"):
        encode_option_a(
            Preamble(
                capability_level=1,
                sublayer_bitmap=0b0000_0001,
                extension_follows=False,
                version=bad_version,
            )
        )


# ---------------------------------------------------------------------------
# Encoder rejection: extension_follows=True
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_encode_rejects_extension_follows_true() -> None:
    """Encoding MUST reject a Preamble with ``extension_follows=True``.

    Per spec section 5.1.1 and ADR-0005, the extension-follows flag is
    reserved in v0.1. When a future specification version defines the
    subsequent-byte format, a new encode function will handle it; the
    v0.1 encoder MUST NOT emit such a frame.
    """
    with pytest.raises(PreambleEncodeError, match="extension_follows"):
        encode_option_a(
            Preamble(
                capability_level=1,
                sublayer_bitmap=0b0000_0001,
                extension_follows=True,
                version=1,
            )
        )


# ---------------------------------------------------------------------------
# Decoder rejection: extension-follows bit set on the wire
# ---------------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.parametrize(
    ("input_byte", "description"),
    [
        # EX-present=1, level=0, extension-follows=1, reserved=0 -> 0x88
        (0x88, "EX-0 with extension-follows set"),
        # EX-present=1, level=1, extension-follows=1, reserved=0 -> 0x98
        (0x98, "EX-1 with extension-follows set"),
        # EX-present=1, level=6, extension-follows=1, reserved=0 -> 0xE8
        (0xE8, "EX-6 with extension-follows set"),
    ],
)
def test_decode_rejects_extension_follows_bit_set(input_byte: int, description: str) -> None:
    """Decoding MUST reject any input byte with the extension-follows bit set.

    Per spec section 5.1.4: v0.1 decoders observing this flag MUST NOT
    attempt to interpret the subsequent bytes. The library API surfaces
    this as a :class:`PreambleDecodeError`; higher layers are expected
    to catch and dispatch to a newer decoder or fall back to legacy
    I3C handling.
    """
    with pytest.raises(PreambleDecodeError, match="extension-follows"):
        decode_option_a(bytes([input_byte]))
