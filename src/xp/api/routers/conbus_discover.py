"""FastAPI router for Conbus operations."""

import logging
from typing import Union
from fastapi.responses import JSONResponse

from .conbus import router
from .errors import handle_service_error
from ..models.discover import (
    DiscoverResponse,
    DiscoverErrorResponse,
)
from ...services.conbus_discover_service import ConbusDiscoverService

logger = logging.getLogger(__name__)


@router.post(
    "/discover",
    response_model=Union[DiscoverResponse, DiscoverErrorResponse],
    responses={
        200: {
            "model": DiscoverResponse,
            "description": "Discover completed successfully",
        },
        400: {
            "model": DiscoverErrorResponse,
            "description": "Connection or request error",
        },
        408: {"model": DiscoverErrorResponse, "description": "Request timeout"},
        500: {"model": DiscoverErrorResponse, "description": "Internal server error"},
    },
)
async def discover_devices() -> Union[DiscoverResponse, JSONResponse]:
    """
    Initiate a Conbus discover operation to find devices on the network.

    Sends a broadcast discover telegram and collects responses from all connected devices.
    """
    service = ConbusDiscoverService()

    # Send discover telegram and receive responses
    with service:
        response = service.send_discover_telegram()

    if not response.success:
        return handle_service_error(response.error or "Unknown error")

    # Build successful response
    return DiscoverResponse(
        devices=response.discovered_devices or [],
    )
