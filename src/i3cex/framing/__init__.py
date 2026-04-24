"""Wire-level framing strategies for I3C-EX.

This subpackage implements two candidate framing strategies for I3C-EX
metadata. Both are implemented so that we can empirically compare them
on wire overhead, parse complexity, extensibility, and other criteria
per :doc:`../../../specs/I3CEX-0.1.0-draft.md` section 5.

Modules:
    preamble:  Candidate A. Single reserved byte preceding the I3C payload.
    tlv:       Candidate B. Type-Length-Value records appended to the payload.

The final specification (``I3CEX-1.0.0``) will standardise one strategy
based on benchmarking results. The losing strategy will be documented as
a negative result in Paper 1 and preserved in the repository history.

Until the comparison is complete, both strategies are considered
experimental and their APIs are unstable.
"""

from __future__ import annotations

from i3cex.framing.preamble import (
    Preamble,
    PreambleDecodeError,
    PreambleEncodeError,
    decode_option_a,
    encode_option_a,
)
from i3cex.framing.tlv import (
    DEFAULT_MAX_TLV_BLOCK_SIZE_V01,
    RESERVED_CONTAINER_TYPE,
    TLVBlockDecodeError,
    TLVBlockEncodeError,
    TLVRecord,
    decode_tlv_block,
    encode_tlv_block,
)

__all__ = [
    "DEFAULT_MAX_TLV_BLOCK_SIZE_V01",
    "RESERVED_CONTAINER_TYPE",
    "Preamble",
    "PreambleDecodeError",
    "PreambleEncodeError",
    "TLVBlockDecodeError",
    "TLVBlockEncodeError",
    "TLVRecord",
    "decode_option_a",
    "decode_tlv_block",
    "encode_option_a",
    "encode_tlv_block",
]
