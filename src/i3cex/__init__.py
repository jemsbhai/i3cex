"""i3cex: extension layers for MIPI I3C targeting edge AI and edge ML workloads.

This package implements the I3C-EX protocol extension layers defined in the
repository's ``specs/I3CEX-*.md`` specifications.

The package is organised by sublayer. Each sublayer is independently
usable and optional; devices declare which sublayers they support during
bus initialisation.

Sublayer modules:
    framing:      Wire-level framing strategies (preamble vs TLV).
    envelope:     EX-1 metadata envelope.
    qos:          EX-2 quality-of-service negotiation.
    fusion:       EX-3 Byzantine fusion signalling.
    timesync:     EX-4 distributed timestamping.
    provenance:   EX-5 provenance and attestation.
    confidence:   EX-6 confidence propagation and extended error recovery.
    sim:          Pure-Python I3C/I3C-EX behavioural simulator.

See the package README for installation, development setup, and testing.
See the repository's ``specs/`` directory for the authoritative protocol
specification.
"""

from __future__ import annotations

__version__ = "0.1.0.dev0"
"""Package version.

Exported at the package root so Hatch can read it via
``[tool.hatch.version] path = "src/i3cex/__init__.py"`` in pyproject.toml.

Follows Semantic Versioning 2.0.0. Pre-1.0.0 versions are understood to
have unstable APIs; breaking changes bump the MINOR component.
"""

__all__ = ["__version__"]
