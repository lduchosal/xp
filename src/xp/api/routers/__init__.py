"""API routers for FastAPI endpoints."""

from xp.api.routers.conbus import router
from xp.api.routers import conbus_discover
from xp.api.routers import conbus_output
from xp.api.routers import conbus_datapoint
from xp.api.routers import conbus_blink
from xp.api.routers import conbus_custom

__all__ = [
    "router",
    "conbus_blink",
    "conbus_custom",
    "conbus_datapoint",
    "conbus_discover",
    "conbus_output",
]
