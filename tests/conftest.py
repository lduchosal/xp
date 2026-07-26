# Copyright (c) 2025 ldvchosal
"""Pytest configuration for the XP project."""

import pytest


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    """Configure anyio to only use asyncio backend.

    Returns:
        The anyio backend name, always "asyncio".

    """
    return "asyncio"
