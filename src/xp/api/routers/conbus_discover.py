"""FastAPI router for Conbus operations."""

import logging
from typing import Union

from fastapi import Request
from fastapi.responses import JSONResponse

from xp.api.models.discover import (
    DiscoverErrorResponse,
    DiscoverResponse,
)
from xp.api.routers.conbus import router
from xp.api.routers.errors import handle_service_error
from xp.services.conbus.conbus_discover_service import ConbusDiscoverService

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
async def discover_devices(request: Request) -> Union[DiscoverResponse, JSONResponse]:
    """
    Initiate a Conbus discover operation to find devices on the network.

    Sends a broadcast discover telegram and collects responses from all connected devices.
    """
    service = request.app.state.container.get_container().resolve(ConbusDiscoverService)

    # Send discover telegram and receive responses
    with service:
        response = service.send_discover_telegram()

    if not response.success:
        return handle_service_error(response.error or "Unknown error")

    # Build successful response
    return DiscoverResponse(
        devices=response.discovered_devices or [],
    )
