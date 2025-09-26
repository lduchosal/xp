"""API routers for FastAPI endpoints."""

from .conbus import router
from . import conbus_discover
from . import conbus_output
from . import conbus_datapoint
from . import conbus_blink
from . import conbus_custom

__all__ = [
    "router",
    "conbus_blink",
    "conbus_custom",
    "conbus_datapoint",
    "conbus_discover",
    "conbus_output",
]
