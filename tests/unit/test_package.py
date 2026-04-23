"""Sanity tests that verify the package can be imported and exposes a version.

These are the canonical "scaffolding exists" tests. They run first in
CI and protect against gross packaging regressions.

Imports are intentionally local (inside each test function) rather
than at module scope. If the import were at module scope and the
package were broken, pytest collection itself would fail, which
produces worse diagnostic output than a failed assertion. By deferring
the import into the test, we get a clean failure message naming the
failing scenario.
"""

from __future__ import annotations

import re

import pytest


@pytest.mark.unit
def test_package_imports() -> None:
    """The package MUST import without error."""
    import i3cex  # noqa: F401 -- imported for side effect of verifying import


@pytest.mark.unit
def test_package_exposes_version() -> None:
    """The package MUST expose a ``__version__`` string attribute."""
    import i3cex

    assert hasattr(i3cex, "__version__")
    assert isinstance(i3cex.__version__, str)
    assert i3cex.__version__  # non-empty


@pytest.mark.unit
def test_version_is_pep440_compatible() -> None:
    """``__version__`` MUST be a valid PEP 440 version string.

    Pre-release segments such as ``.dev0`` are permitted.
    """
    import i3cex

    # PEP 440 public version identifier (simplified but sufficient).
    pep440_pattern = (
        r"^([1-9][0-9]*!)?"  # optional epoch
        r"(0|[1-9][0-9]*)"  # release major
        r"(\.(0|[1-9][0-9]*))*"  # release minor/patch/...
        r"((a|b|rc)(0|[1-9][0-9]*))?"  # optional pre-release
        r"(\.post(0|[1-9][0-9]*))?"  # optional post-release
        r"(\.dev(0|[1-9][0-9]*))?$"  # optional dev-release
    )
    assert re.match(pep440_pattern, i3cex.__version__), (
        f"Version {i3cex.__version__!r} is not PEP 440 compatible."
    )
