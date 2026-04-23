"""Option A preamble-byte framing for I3C-EX v0.1.

This module implements the single-byte preamble wire format defined in
I3C-EX specification v0.1 section 5.1 and ADR-0005. The format is
deliberately simple:

- Exactly 1 byte on the wire in v0.1 (extension-follows flag is reserved).
- Bit layout:

    bit 7:     EX-present flag (MUST be 1)
    bits 6-4:  capability level (0..6 valid; 7 reserved)
    bit 3:     extension-follows flag (0 in v0.1)
    bits 2-0:  reserved (MUST be 0 in v0.1)

The in-memory :class:`Preamble` dataclass is intentionally richer than
the Option A wire format supports, so that future wire formats
(Option B 2-byte bitmap, Option C table-indexed) can be added as new
encode/decode functions without changing the dataclass or its
consumers. See ADR-0005 for the migration strategy.

Invariants enforced by this module
----------------------------------
Encoder:
    - ``capability_level`` MUST be in ``range(0, 7)``. Level 7 is
      reserved and encoding raises :class:`PreambleEncodeError`.
    - ``sublayer_bitmap`` MUST equal ``(1 << capability_level) - 1``.
      Option A can only represent level-monotonic sublayer sets;
      any other bitmap raises :class:`PreambleEncodeError`.
    - In v0.1, ``extension_follows`` MUST be ``False``. Setting it
      True raises :class:`PreambleEncodeError` until a future
      specification version defines the follow-on byte format.
    - ``version`` MUST be 1. Future versions will be handled by new
      encode functions.

Decoder:
    - Input MUST be non-empty. Empty input raises :class:`PreambleDecodeError`.
    - Bit 7 (EX-present) MUST be 1. Zero raises :class:`PreambleDecodeError`;
      higher layers are expected to catch and dispatch to legacy I3C handling.
    - Bits 2-0 MUST be 0. Any non-zero reserved bit raises
      :class:`PreambleDecodeError` (per spec section 5.1.2).
    - Bits 6-4 MUST be in ``range(0, 7)``. Level 7 raises
      :class:`PreambleDecodeError` (reserved in v0.1).
    - In v0.1, bit 3 (extension-follows) MUST be 0. A set bit raises
      :class:`PreambleDecodeError` until a future version defines the
      subsequent bytes.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

# __all__ is sorted isort-style: classes first (alphabetical), then
# all-caps constants (alphabetical), then lowercase functions
# (alphabetical). This satisfies ruff rule RUF022.
__all__ = [
    "EXTENSION_FOLLOWS_FLAG_MASK",
    "EX_PRESENT_FLAG_MASK",
    "LEVEL_MASK",
    "LEVEL_SHIFT",
    "MAX_CAPABILITY_LEVEL_V01",
    "RESERVED_BITS_MASK",
    "Preamble",
    "PreambleDecodeError",
    "PreambleEncodeError",
    "decode_option_a",
    "encode_option_a",
]

# Bit masks and shifts derived from the spec section 5.1.1 layout.
EX_PRESENT_FLAG_MASK: Final[int] = 0b1000_0000
LEVEL_MASK: Final[int] = 0b0111_0000
LEVEL_SHIFT: Final[int] = 4
EXTENSION_FOLLOWS_FLAG_MASK: Final[int] = 0b0000_1000
RESERVED_BITS_MASK: Final[int] = 0b0000_0111

# Maximum valid capability level in v0.1. Levels 0..6 map to EX-0..EX-6;
# level 7 is reserved.
MAX_CAPABILITY_LEVEL_V01: Final[int] = 6


class PreambleEncodeError(ValueError):
    """Raised when a Preamble cannot be encoded in the target wire format."""


class PreambleDecodeError(ValueError):
    """Raised when bytes cannot be decoded as a valid Preamble."""


@dataclass(frozen=True)
class Preamble:
    """Wire-format-agnostic representation of an I3C-EX preamble.

    This dataclass carries the full information space that any preamble
    wire format (Option A, B, or C per ADR-0005) could encode. Not
    every combination is representable by every wire format; the
    ``encode_option_a`` function validates its inputs accordingly.

    Attributes:
        capability_level: Numeric capability level. 0 = EX-0
            (negotiation only); 1..6 = EX-1..EX-6. Level 7 is
            reserved in v0.1. Levels beyond 6 are reserved for future
            specification versions.
        sublayer_bitmap: 8-bit bitmap of active sublayers. Bit ``n``
            corresponds to EX-``(n+1)``. In Option A, this MUST equal
            ``(1 << capability_level) - 1``; other wire formats may
            permit arbitrary bitmaps.
        extension_follows: True if additional bytes follow the
            preamble. MUST be False in v0.1; reserved for future
            specification versions.
        version: Protocol version. MUST be 1 in v0.1.
    """

    capability_level: int
    sublayer_bitmap: int
    extension_follows: bool
    version: int = 1


def encode_option_a(preamble: Preamble) -> bytes:
    """Encode a :class:`Preamble` using the Option A 1-byte wire format.

    Args:
        preamble: The preamble to encode. See module docstring for the
            invariants this function enforces on its input.

    Returns:
        A ``bytes`` object of length 1 containing the encoded preamble.

    Raises:
        PreambleEncodeError: If the Preamble violates any Option A
            v0.1 invariant (reserved level, non-monotonic bitmap,
            extension_follows=True, unsupported version).
    """
    if preamble.version != 1:
        raise PreambleEncodeError(
            f"Option A v0.1 supports only version=1, got version={preamble.version}"
        )
    if not (0 <= preamble.capability_level <= MAX_CAPABILITY_LEVEL_V01):
        raise PreambleEncodeError(
            "capability_level MUST be in range(0, 7) for v0.1 Option A; "
            f"got {preamble.capability_level}"
        )

    expected_bitmap = (1 << preamble.capability_level) - 1
    if preamble.sublayer_bitmap != expected_bitmap:
        raise PreambleEncodeError(
            "Option A can only encode level-monotonic sublayer bitmaps. "
            f"Expected bitmap={expected_bitmap:#010b} for level="
            f"{preamble.capability_level}, got bitmap="
            f"{preamble.sublayer_bitmap:#010b}."
        )

    if preamble.extension_follows:
        raise PreambleEncodeError(
            "extension_follows=True is reserved for future specification "
            "versions; MUST be False in v0.1 Option A."
        )

    byte = (
        EX_PRESENT_FLAG_MASK | ((preamble.capability_level << LEVEL_SHIFT) & LEVEL_MASK)
        # bit 3 (extension_follows) is 0 in v0.1; reserved bits 2-0 are 0.
    )
    return bytes([byte])


def decode_option_a(data: bytes) -> tuple[Preamble, bytes]:
    """Decode a single Option A preamble byte from the head of ``data``.

    Args:
        data: Byte sequence whose first byte is an Option A preamble.
            Any bytes beyond the first are returned unchanged as the
            ``remaining`` part of the tuple.

    Returns:
        A 2-tuple ``(preamble, remaining)`` where ``preamble`` is the
        decoded :class:`Preamble` and ``remaining`` is ``data[1:]``.

    Raises:
        PreambleDecodeError: If ``data`` is empty, the EX-present flag
            is zero, any reserved bit is non-zero, the capability
            level field is 7, or the extension-follows flag is set.
    """
    if len(data) == 0:
        raise PreambleDecodeError("Cannot decode preamble from empty input")

    byte = data[0]

    if (byte & EX_PRESENT_FLAG_MASK) == 0:
        raise PreambleDecodeError(
            f"EX-present flag (bit 7) is zero in byte {byte:#010b}; "
            "caller should dispatch to legacy I3C handling"
        )

    reserved = byte & RESERVED_BITS_MASK
    if reserved != 0:
        raise PreambleDecodeError(
            f"Reserved bits 2-0 MUST be zero in v0.1; got {reserved:#05b} in byte {byte:#010b}"
        )

    level = (byte & LEVEL_MASK) >> LEVEL_SHIFT
    if level > MAX_CAPABILITY_LEVEL_V01:
        raise PreambleDecodeError(
            f"Capability level {level} is reserved in v0.1 (max = {MAX_CAPABILITY_LEVEL_V01})"
        )

    extension_follows = bool(byte & EXTENSION_FOLLOWS_FLAG_MASK)
    if extension_follows:
        raise PreambleDecodeError(
            "extension-follows flag (bit 3) is set, but v0.1 does not "
            "define the subsequent-byte format. Caller should dispatch "
            "to a newer decoder or fall back to legacy I3C handling."
        )

    preamble = Preamble(
        capability_level=level,
        sublayer_bitmap=(1 << level) - 1,
        extension_follows=False,
        version=1,
    )
    return preamble, data[1:]
