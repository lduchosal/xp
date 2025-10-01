"""API routers for FastAPI endpoints."""

from xp.api.routers import (
    conbus_blink,
    conbus_custom,
    conbus_datapoint,
    conbus_discover,
    conbus_output,
)
from xp.api.routers.conbus import router

__all__ = [
    "router",
    "conbus_blink",
    "conbus_custom",
    "conbus_datapoint",
    "conbus_discover",
    "conbus_output",
]
