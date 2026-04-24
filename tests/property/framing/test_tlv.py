"""Property-based tests for TLV block framing (Candidate B).

These tests verify the core invariants of the TLV wire format per
I3C-EX v0.1 specification section 5.2 and ADRs 0006, 0007, 0008:

- Roundtrip: decode(encode(records)) == records for every valid record list.
- Wire size: encoded block is exactly sum(2 + len(record.value)) bytes.
- Length-byte discipline: encoded Length bytes are always in 0-127.
- Type-0xFE reservation: encoder rejects, decoder rejects.
- Length-byte reservation: encoder rejects oversized values, decoder
  rejects Length bytes >= 0x80.
- Max-block-size enforcement: encoder and decoder both enforce the cap.

Hypothesis strategies constrain inputs to the v0.1 valid domain:
Type in 0..255 except 0xFE; Value length 0..127 bytes.
"""

from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st

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
# Strategies
# ---------------------------------------------------------------------------

# Type values valid in v0.1: 0..255 except 0xFE (reserved).
valid_v01_types = st.integers(min_value=0, max_value=255).filter(
    lambda t: t != RESERVED_CONTAINER_TYPE
)

# Value bytes valid in v0.1: 0..127 bytes long.
valid_v01_values = st.binary(min_size=0, max_size=127)


@st.composite
def valid_v01_records(draw: st.DrawFn) -> TLVRecord:
    """Hypothesis strategy for a single valid v0.1 TLVRecord."""
    return TLVRecord(type_=draw(valid_v01_types), value=draw(valid_v01_values))


@st.composite
def valid_v01_record_lists(draw: st.DrawFn) -> list[TLVRecord]:
    """Strategy for a list of records whose total encoded size <= 4096.

    Rather than filter, we construct eagerly with a running budget so
    generation is efficient.
    """
    records: list[TLVRecord] = []
    remaining_budget = DEFAULT_MAX_TLV_BLOCK_SIZE_V01
    max_records = draw(st.integers(min_value=0, max_value=30))
    for _ in range(max_records):
        # Each record costs 2 + len(value) bytes. Need at least 2 bytes left.
        if remaining_budget < 2:
            break
        max_value_len = min(127, remaining_budget - 2)
        type_ = draw(valid_v01_types)
        value = draw(st.binary(min_size=0, max_size=max_value_len))
        records.append(TLVRecord(type_=type_, value=value))
        remaining_budget -= 2 + len(value)
    return records


# ---------------------------------------------------------------------------
# Roundtrip invariant
# ---------------------------------------------------------------------------


@pytest.mark.property
@given(records=valid_v01_record_lists())
def test_roundtrip_preserves_record_list(records: list[TLVRecord]) -> None:
    """decode(encode(records)) MUST equal records for every valid input."""
    encoded = encode_tlv_block(records)
    decoded = decode_tlv_block(encoded)
    assert decoded == records


# ---------------------------------------------------------------------------
# Wire-size invariant
# ---------------------------------------------------------------------------


@pytest.mark.property
@given(records=valid_v01_record_lists())
def test_encoded_size_matches_expected(records: list[TLVRecord]) -> None:
    """Encoded block MUST be exactly sum(2 + len(value)) bytes."""
    expected_size = sum(2 + len(r.value) for r in records)
    encoded = encode_tlv_block(records)
    assert len(encoded) == expected_size


# ---------------------------------------------------------------------------
# Length-byte discipline
# ---------------------------------------------------------------------------


@pytest.mark.property
@given(records=valid_v01_record_lists())
def test_all_encoded_length_bytes_below_0x80(records: list[TLVRecord]) -> None:
    """Every Length byte in the encoded block MUST be < 0x80.

    Per spec section 5.2.1.2, the high bit of Length is reserved for
    Path beta future extension.
    """
    encoded = encode_tlv_block(records)
    # Walk records by tracking cumulative offset; Length byte is the
    # second byte of each record's header.
    offset = 0
    for r in records:
        length_byte = encoded[offset + 1]
        assert length_byte < 0x80, (
            f"Encoded Length byte {length_byte:#x} has high bit set; reserved in v0.1"
        )
        offset += 2 + len(r.value)


# ---------------------------------------------------------------------------
# Empty block
# ---------------------------------------------------------------------------


@pytest.mark.property
def test_empty_record_list_encodes_to_empty_bytes() -> None:
    """An empty record list MUST encode to b'' (zero bytes)."""
    assert encode_tlv_block([]) == b""


@pytest.mark.property
def test_empty_bytes_decode_to_empty_record_list() -> None:
    """b'' MUST decode to an empty record list."""
    assert decode_tlv_block(b"") == []


# ---------------------------------------------------------------------------
# Encoder rejection invariants
# ---------------------------------------------------------------------------


@pytest.mark.property
def test_encode_rejects_reserved_type_0xfe() -> None:
    """Encoding a record with Type == 0xFE MUST raise TLVBlockEncodeError."""
    with pytest.raises(TLVBlockEncodeError, match=r"0xFE|reserved"):
        encode_tlv_block([TLVRecord(type_=RESERVED_CONTAINER_TYPE, value=b"")])


@pytest.mark.property
@given(bad_length=st.integers(min_value=128, max_value=1000))
def test_encode_rejects_oversized_value(bad_length: int) -> None:
    """Encoding a record with value longer than 127 MUST raise."""
    with pytest.raises(TLVBlockEncodeError, match=r"length|127"):
        encode_tlv_block([TLVRecord(type_=0x00, value=b"\x00" * bad_length)])


@pytest.mark.property
@given(bad_type=st.integers().filter(lambda t: t < 0 or t > 255))
def test_encode_rejects_out_of_range_type(bad_type: int) -> None:
    """Encoding a record whose Type is outside 0..255 MUST raise."""
    with pytest.raises(TLVBlockEncodeError, match=r"type|range"):
        encode_tlv_block([TLVRecord(type_=bad_type, value=b"")])


@pytest.mark.property
def test_encode_rejects_block_exceeding_max_size() -> None:
    """A record list whose total encoded size exceeds max_size MUST raise.

    We construct a list that fits under default 4096 but exceeds a
    smaller explicit cap.
    """
    # 5 records of 2+127 = 129 bytes each -> 645 bytes total.
    records = [TLVRecord(type_=0x00, value=b"\x00" * 127) for _ in range(5)]
    # Cap at 500 bytes; 645 exceeds it.
    with pytest.raises(TLVBlockEncodeError, match=r"max|cap|size"):
        encode_tlv_block(records, max_size=500)


# ---------------------------------------------------------------------------
# Decoder rejection invariants
# ---------------------------------------------------------------------------


@pytest.mark.property
def test_decode_rejects_reserved_type_0xfe() -> None:
    """A block containing a record with Type == 0xFE MUST be rejected."""
    # Construct a valid-looking record with reserved Type 0xFE.
    encoded = bytes([RESERVED_CONTAINER_TYPE, 0x00])  # Type=0xFE, Length=0
    with pytest.raises(TLVBlockDecodeError, match=r"0xFE|reserved"):
        decode_tlv_block(encoded)


@pytest.mark.property
@given(bad_length=st.integers(min_value=0x80, max_value=0xFF))
def test_decode_rejects_length_byte_with_high_bit_set(bad_length: int) -> None:
    """A block with a Length byte >= 0x80 MUST be rejected."""
    encoded = bytes([0x00, bad_length])  # Type=0x00, reserved Length
    with pytest.raises(TLVBlockDecodeError, match=r"length|reserved|0x80"):
        decode_tlv_block(encoded)


@pytest.mark.property
def test_decode_rejects_truncated_header() -> None:
    """A block ending mid-header (1 byte with no Length) MUST be rejected."""
    with pytest.raises(TLVBlockDecodeError, match=r"truncated|incomplete"):
        decode_tlv_block(b"\x00")


@pytest.mark.property
def test_decode_rejects_truncated_value() -> None:
    """A block declaring more Value bytes than remain MUST be rejected."""
    # Type=0x00, Length=0x05, but only 3 Value bytes follow.
    encoded = b"\x00\x05\xaa\xbb\xcc"
    with pytest.raises(TLVBlockDecodeError, match=r"truncated|value"):
        decode_tlv_block(encoded)


@pytest.mark.property
def test_decode_rejects_block_exceeding_max_size() -> None:
    """A block whose total length exceeds max_size MUST be rejected."""
    # Build a valid 600-byte block, pass a 500-byte cap.
    records = [TLVRecord(type_=0x00, value=b"\x00" * 127) for _ in range(4)]
    encoded = encode_tlv_block(records)  # 4 * 129 = 516 bytes
    assert len(encoded) == 516
    with pytest.raises(TLVBlockDecodeError, match=r"max|cap|size"):
        decode_tlv_block(encoded, max_size=500)
