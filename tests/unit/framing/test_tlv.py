"""Unit tests for TLV block framing: known-good wire vectors.

Vectors derived from I3C-EX v0.1 specification Appendix A, examples
A.5 through A.8. These MUST produce bit-exact wire output; any
deviation indicates a bug in either the specification or the
implementation.
"""

from __future__ import annotations

import pytest

from i3cex.framing.tlv import (
    DEFAULT_MAX_TLV_BLOCK_SIZE_V01,
    RESERVED_CONTAINER_TYPE,
    TLVBlockDecodeError,
    TLVBlockEncodeError,
    TLVRecord,
    decode_tlv_block,
    encode_tlv_block,
)

# ---------------------------------------------------------------------------
# Default max size constant
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_default_max_block_size_is_4096() -> None:
    """Spec section 5.2.3: default cap is 4096 bytes."""
    assert DEFAULT_MAX_TLV_BLOCK_SIZE_V01 == 4096


@pytest.mark.unit
def test_reserved_container_type_is_0xfe() -> None:
    """Spec section 5.2.2: Type 0xFE is reserved."""
    assert RESERVED_CONTAINER_TYPE == 0xFE


# ---------------------------------------------------------------------------
# Spec Appendix A.5: Minimal single-record TLV block
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_spec_a5_single_record_encodes_correctly() -> None:
    """Spec A.5: Type=0x00, Length=4, Value=0x01020304 -> 6 bytes."""
    records = [TLVRecord(type_=0x00, value=b"\x01\x02\x03\x04")]
    assert encode_tlv_block(records) == b"\x00\x04\x01\x02\x03\x04"


@pytest.mark.unit
def test_spec_a5_single_record_decodes_correctly() -> None:
    """Spec A.5: 0x00 0x04 0x01 0x02 0x03 0x04 decodes to one record."""
    decoded = decode_tlv_block(b"\x00\x04\x01\x02\x03\x04")
    assert decoded == [TLVRecord(type_=0x00, value=b"\x01\x02\x03\x04")]


# ---------------------------------------------------------------------------
# Spec Appendix A.6: Multi-record TLV block
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_spec_a6_multi_record_encodes_correctly() -> None:
    """Spec A.6: envelope (Type=0x00, 3B) + fusion (Type=0x20, 2B) -> 9 bytes."""
    records = [
        TLVRecord(type_=0x00, value=b"\xaa\xbb\xcc"),
        TLVRecord(type_=0x20, value=b"\xde\xad"),
    ]
    expected = b"\x00\x03\xaa\xbb\xcc\x20\x02\xde\xad"
    assert encode_tlv_block(records) == expected


@pytest.mark.unit
def test_spec_a6_multi_record_decodes_correctly() -> None:
    """Spec A.6: concatenated block decodes back into two records."""
    encoded = b"\x00\x03\xaa\xbb\xcc\x20\x02\xde\xad"
    decoded = decode_tlv_block(encoded)
    assert decoded == [
        TLVRecord(type_=0x00, value=b"\xaa\xbb\xcc"),
        TLVRecord(type_=0x20, value=b"\xde\xad"),
    ]


# ---------------------------------------------------------------------------
# Spec Appendix A.7: Rejected record (reserved Type 0xFE)
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_spec_a7_reserved_type_0xfe_rejected_on_decode() -> None:
    """Spec A.7: 0xFE 0x00 (reserved Type) MUST be rejected by decoder."""
    with pytest.raises(TLVBlockDecodeError):
        decode_tlv_block(b"\xfe\x00")


@pytest.mark.unit
def test_spec_a7_reserved_type_0xfe_rejected_on_encode() -> None:
    """Spec A.7: encoding a Type=0xFE record MUST be rejected."""
    with pytest.raises(TLVBlockEncodeError):
        encode_tlv_block([TLVRecord(type_=0xFE, value=b"")])


# ---------------------------------------------------------------------------
# Spec Appendix A.8: Rejected record (reserved Length range)
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_spec_a8_reserved_length_range_rejected_on_decode() -> None:
    """Spec A.8: Length byte 0x80 (high bit set) MUST be rejected."""
    with pytest.raises(TLVBlockDecodeError):
        decode_tlv_block(b"\x00\x80")


# ---------------------------------------------------------------------------
# Zero-length Values are allowed
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_zero_length_value_roundtrips() -> None:
    """A record with an empty Value MUST encode and decode correctly."""
    records = [TLVRecord(type_=0x00, value=b"")]
    encoded = encode_tlv_block(records)
    assert encoded == b"\x00\x00"
    assert decode_tlv_block(encoded) == records


# ---------------------------------------------------------------------------
# Maximum single-record Value size (127 bytes)
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_max_value_127_bytes_roundtrips() -> None:
    """A record with a 127-byte Value is valid and roundtrips."""
    value = bytes(range(127))  # 0..126
    records = [TLVRecord(type_=0x42, value=value)]
    encoded = encode_tlv_block(records)
    assert len(encoded) == 129  # 2 header + 127 value
    assert encoded[0] == 0x42
    assert encoded[1] == 0x7F
    assert encoded[2:] == value
    assert decode_tlv_block(encoded) == records


# ---------------------------------------------------------------------------
# Type-range allocation per spec section 5.2.1.1
# ---------------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.parametrize(
    ("type_value", "owner"),
    [
        (0x00, "EX-1 envelope (low end)"),
        (0x0F, "EX-1 envelope (high end)"),
        (0x10, "EX-2 QoS (low end)"),
        (0x1F, "EX-2 QoS (high end)"),
        (0x20, "EX-3 fusion (low end)"),
        (0x2F, "EX-3 fusion (high end)"),
        (0x30, "EX-4 timesync"),
        (0x40, "EX-5 provenance"),
        (0x50, "EX-6 confidence"),
        (0x60, "unallocated (low end)"),
        (0xFD, "unallocated (high end)"),
        (0xFF, "unallocated (post-reserved)"),
    ],
)
def test_every_non_reserved_type_is_encodable(type_value: int, owner: str) -> None:
    """Every Type value except 0xFE MUST be encodable."""
    records = [TLVRecord(type_=type_value, value=b"\x42")]
    encoded = encode_tlv_block(records)
    assert encoded == bytes([type_value, 0x01, 0x42])
    assert decode_tlv_block(encoded) == records


# ---------------------------------------------------------------------------
# Max-size negotiation (spec section 5.2.3)
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_encode_respects_custom_max_size() -> None:
    """A custom max_size smaller than the default is enforced."""
    # 3 records of 129 bytes = 387 bytes.
    records = [TLVRecord(type_=0x00, value=b"\x00" * 127) for _ in range(3)]
    # Should succeed at max_size=400.
    encoded = encode_tlv_block(records, max_size=400)
    assert len(encoded) == 387
    # Should fail at max_size=300.
    with pytest.raises(TLVBlockEncodeError):
        encode_tlv_block(records, max_size=300)


@pytest.mark.unit
def test_decode_respects_custom_max_size() -> None:
    """A custom max_size smaller than the default is enforced on decode."""
    # Build a valid 387-byte block with default cap.
    records = [TLVRecord(type_=0x00, value=b"\x00" * 127) for _ in range(3)]
    encoded = encode_tlv_block(records)
    # Decoding should succeed at max_size=400.
    assert decode_tlv_block(encoded, max_size=400) == records
    # Decoding should fail at max_size=300.
    with pytest.raises(TLVBlockDecodeError):
        decode_tlv_block(encoded, max_size=300)


@pytest.mark.unit
def test_encode_at_exactly_max_size_succeeds() -> None:
    """Encoding a block whose size equals max_size exactly MUST succeed."""
    # Build a block of exactly 129 bytes with max_size=129.
    records = [TLVRecord(type_=0x00, value=b"\x00" * 127)]
    encoded = encode_tlv_block(records, max_size=129)
    assert len(encoded) == 129


@pytest.mark.unit
def test_default_cap_allows_4096_byte_block() -> None:
    """A block of exactly 4096 bytes MUST be accepted with the default cap."""
    # 31 records of 129 bytes + 1 record of (4096 - 31*129) = 97-byte record.
    # 31 * 129 = 3999, remaining = 97. 97-byte record has 2-byte header +
    # 95-byte value = 97 bytes. Total = 4096.
    records = [TLVRecord(type_=0x00, value=b"\x00" * 127) for _ in range(31)]
    records.append(TLVRecord(type_=0x00, value=b"\x00" * 95))
    encoded = encode_tlv_block(records)
    assert len(encoded) == 4096


# ---------------------------------------------------------------------------
# Trailing payload behaviour
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_decode_consumes_entire_input() -> None:
    """decode_tlv_block MUST consume all input; no 'remaining' concept.

    Unlike the preamble decoder (which returns (value, remaining)), the
    TLV decoder consumes the full block. Callers who need to embed TLV
    blocks within larger frames are responsible for slicing the input.
    """
    records = [TLVRecord(type_=0x00, value=b"\xaa\xbb")]
    encoded = encode_tlv_block(records)
    # No remaining bytes returned -- decoder returns list only.
    assert decode_tlv_block(encoded) == records
