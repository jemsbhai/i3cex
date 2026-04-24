"""TLV block framing for I3C-EX v0.1 (Candidate B).

This module implements the TLV (Type-Length-Value) wire format defined
in I3C-EX specification v0.1 section 5.2, governed by:

- ADR-0006: fixed 1-byte Length, 0-127 range; 0x80-0xFF reserved.
- ADR-0007: flat-only records; Type 0xFE reserved for future container
  semantics.
- ADR-0008: device-negotiated maximum block size, default 4096 bytes.

Wire format summary
-------------------

A TLV *block* is a sequence of TLV *records* concatenated end-to-end.
Each record is::

    byte 0:       Type   (1 byte, value 0-255 except 0xFE)
    byte 1:       Length (1 byte, value 0-127)
    bytes 2..N:   Value  (Length bytes of sublayer-specific payload)

The minimum record is 2 bytes (Type + Length with zero-length Value).
The maximum record is 129 bytes (2-byte header + 127-byte Value).

Invariants enforced by this module
----------------------------------

Encoder (``encode_tlv_block``):

- Every record's ``type_`` MUST be in ``range(0, 256)``.
- Every record's ``type_`` MUST NOT equal 0xFE (reserved for future
  container semantics; ADR-0007).
- Every record's ``value`` MUST be at most 127 bytes long.
- The total encoded block size MUST NOT exceed ``max_size``.

Decoder (``decode_tlv_block``):

- Every Length byte MUST be < 0x80 (0x80-0xFF reserved; ADR-0006).
- Every record MUST be complete: no truncated headers, no truncated
  Value fields.
- No record MUST have Type == 0xFE.
- The total block size MUST NOT exceed ``max_size``.

Extension paths (informative, non-binding)
------------------------------------------

Three forward-compatibility paths are reserved at the spec level for
lifting the 127-byte Value cap in future versions:

- **Path alpha**: reserve a Type value for "extended length follows";
  the reserved record's Value carries a 2 or 4-byte length.
- **Path beta**: assign meaning to Length bytes >= 0x80.
- **Path gamma**: reserve a "continuation" Type for multi-record
  Value reassembly.

See ADR-0006 for the full forward-compatibility discussion and the
rationale for choosing fixed 1-byte Length in v0.1.

API design notes
----------------

- The record list API (concrete ``list[TLVRecord]``) was chosen over a
  streaming iterator API at the 4096-byte cap where laziness offers no
  meaningful benefit. A streaming decoder may be added in a later
  version without breaking this API.
- The decoder consumes its entire input and returns a list of records.
  Callers embedding TLV blocks within larger frames are responsible
  for slicing their input before invoking ``decode_tlv_block``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

__all__ = [
    "DEFAULT_MAX_TLV_BLOCK_SIZE_V01",
    "MAX_TYPE_VALUE",
    "MAX_VALUE_LENGTH_V01",
    "MIN_TYPE_VALUE",
    "RESERVED_CONTAINER_TYPE",
    "RESERVED_LENGTH_MIN",
    "TLVBlockDecodeError",
    "TLVBlockEncodeError",
    "TLVRecord",
    "decode_tlv_block",
    "encode_tlv_block",
]


# ---------------------------------------------------------------------------
# Constants derived from spec section 5.2 and ADRs 0006/0007/0008
# ---------------------------------------------------------------------------

DEFAULT_MAX_TLV_BLOCK_SIZE_V01: Final[int] = 4096
"""Default maximum TLV block size in bytes (ADR-0008, spec 5.2.3).

Used when the caller does not pass an explicit ``max_size``. Represents
the size a device advertises when it declines to include an explicit
cap in its EX-Discovery CCC response.
"""

MAX_VALUE_LENGTH_V01: Final[int] = 0x7F  # 127
"""Maximum Value length per record in v0.1 (ADR-0006, spec 5.2.1.2).

Length bytes in the range 0x80-0xFF are reserved for Path beta future
extensions.
"""

RESERVED_LENGTH_MIN: Final[int] = 0x80
"""Smallest Length byte value considered reserved in v0.1."""

RESERVED_CONTAINER_TYPE: Final[int] = 0xFE
"""Type value reserved as a placeholder for future container semantics.

v0.1 encoders MUST NOT emit this Type; v0.1 decoders MUST reject any
record with this Type. See ADR-0007 and spec section 5.2.2.
"""

MIN_TYPE_VALUE: Final[int] = 0x00
"""Smallest valid Type byte value."""

MAX_TYPE_VALUE: Final[int] = 0xFF
"""Largest valid Type byte value. Type 0xFE is reserved in v0.1; see
:data:`RESERVED_CONTAINER_TYPE`.
"""


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class TLVBlockEncodeError(ValueError):
    """Raised when a record list cannot be encoded as a v0.1 TLV block."""


class TLVBlockDecodeError(ValueError):
    """Raised when bytes cannot be decoded as a v0.1 TLV block."""


# ---------------------------------------------------------------------------
# Record dataclass
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TLVRecord:
    """A single Type-Length-Value record.

    Attributes:
        type_: Type field, 0-255 except 0xFE. Each sublayer owns a
            non-overlapping Type range (see spec section 5.2.1.1 and
            the sublayer sections 6.1 through 6.6).
        value: Value field as bytes, 0-127 bytes long. Its internal
            structure is defined by the owning sublayer; the framing
            layer treats it as opaque.
    """

    type_: int
    value: bytes


# ---------------------------------------------------------------------------
# Encoder
# ---------------------------------------------------------------------------


def encode_tlv_block(
    records: list[TLVRecord] | tuple[TLVRecord, ...],
    max_size: int = DEFAULT_MAX_TLV_BLOCK_SIZE_V01,
) -> bytes:
    """Encode a sequence of :class:`TLVRecord` into a v0.1 TLV block.

    Args:
        records: The records to encode, in order. An empty sequence
            encodes to ``b""``.
        max_size: The maximum allowed total encoded size in bytes.
            Defaults to :data:`DEFAULT_MAX_TLV_BLOCK_SIZE_V01`.

    Returns:
        The encoded TLV block as ``bytes``.

    Raises:
        TLVBlockEncodeError: If any record violates v0.1 invariants or
            if the total encoded size exceeds ``max_size``.
    """
    chunks: list[bytes] = []
    total_size = 0

    for index, record in enumerate(records):
        _validate_record_for_encoding(record, index)

        record_size = 2 + len(record.value)
        if total_size + record_size > max_size:
            raise TLVBlockEncodeError(
                f"Encoded block size {total_size + record_size} exceeds "
                f"max_size {max_size} after appending record at index {index}"
            )

        chunks.append(bytes([record.type_, len(record.value)]))
        chunks.append(record.value)
        total_size += record_size

    return b"".join(chunks)


def _validate_record_for_encoding(record: TLVRecord, index: int) -> None:
    """Validate a single record's fields before encoding.

    Split out for readability; pytest output is clearer when the
    precondition-check logic is isolated from the concatenation logic.
    """
    if not (MIN_TYPE_VALUE <= record.type_ <= MAX_TYPE_VALUE):
        raise TLVBlockEncodeError(
            f"Record at index {index}: type_ {record.type_} is out of "
            f"range {MIN_TYPE_VALUE}..{MAX_TYPE_VALUE}"
        )
    if record.type_ == RESERVED_CONTAINER_TYPE:
        raise TLVBlockEncodeError(
            f"Record at index {index}: Type 0xFE is reserved in v0.1 "
            f"(container semantics placeholder per ADR-0007)"
        )
    if len(record.value) > MAX_VALUE_LENGTH_V01:
        raise TLVBlockEncodeError(
            f"Record at index {index}: value length {len(record.value)} "
            f"exceeds v0.1 maximum of {MAX_VALUE_LENGTH_V01} bytes "
            f"(Length byte would overflow the 0x00-0x7F v0.1 range)"
        )


# ---------------------------------------------------------------------------
# Decoder
# ---------------------------------------------------------------------------


def decode_tlv_block(
    data: bytes,
    max_size: int = DEFAULT_MAX_TLV_BLOCK_SIZE_V01,
) -> list[TLVRecord]:
    """Decode a v0.1 TLV block into a list of :class:`TLVRecord`.

    Args:
        data: The encoded TLV block. An empty byte sequence decodes
            to an empty list.
        max_size: The maximum allowed block size in bytes. If
            ``len(data)`` exceeds this, decoding is rejected without
            parsing any records.

    Returns:
        The decoded list of records, in wire order.

    Raises:
        TLVBlockDecodeError: If ``data`` exceeds ``max_size``, if any
            record has Type 0xFE, any Length byte is >= 0x80, or the
            block is truncated (incomplete header or Value).
    """
    if len(data) > max_size:
        raise TLVBlockDecodeError(f"Block size {len(data)} exceeds max_size {max_size}")

    records: list[TLVRecord] = []
    offset = 0
    end = len(data)

    while offset < end:
        # Header: Type + Length, always exactly 2 bytes.
        if offset + 2 > end:
            raise TLVBlockDecodeError(
                f"Truncated TLV record at offset {offset}: "
                f"incomplete header (need 2 bytes, have {end - offset})"
            )

        type_byte = data[offset]
        length_byte = data[offset + 1]

        if type_byte == RESERVED_CONTAINER_TYPE:
            raise TLVBlockDecodeError(
                f"Record at offset {offset}: Type 0xFE is reserved in "
                f"v0.1 (container semantics placeholder per ADR-0007)"
            )

        if length_byte >= RESERVED_LENGTH_MIN:
            raise TLVBlockDecodeError(
                f"Record at offset {offset}: length byte "
                f"{length_byte:#04x} is reserved in v0.1 "
                f"(0x80-0xFF reserved for Path beta future extension)"
            )

        value_start = offset + 2
        value_end = value_start + length_byte
        if value_end > end:
            raise TLVBlockDecodeError(
                f"Record at offset {offset}: truncated value "
                f"(Length byte claims {length_byte} bytes, but only "
                f"{end - value_start} bytes remain)"
            )

        records.append(TLVRecord(type_=type_byte, value=data[value_start:value_end]))
        offset = value_end

    return records
