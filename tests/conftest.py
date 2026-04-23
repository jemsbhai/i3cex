"""Shared pytest fixtures and configuration for the i3cex test suite.

Fixtures declared here are available across all test layers (unit,
property, integration, cosim). Layer-specific fixtures live in each
layer's own conftest.
"""

from __future__ import annotations

import pytest


@pytest.fixture
def anyio_backend() -> str:
    """Default async backend for any future async tests.

    Declared here as a placeholder so that async tests added later do
    not require immediate conftest changes.
    """
    return "asyncio"
