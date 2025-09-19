"""FastAPI router for Conbus operations."""

import logging
from typing import Union
from fastapi.responses import JSONResponse

from .conbus import router
from .errors import handle_service_error
from ..models.discovery import (
    DiscoveryResponse,
    DiscoveryErrorResponse,
)
from ...services.conbus_discover_service import ConbusDiscoverService

logger = logging.getLogger(__name__)

@router.post(
    "/discover",
    response_model=Union[DiscoveryResponse, DiscoveryErrorResponse],
    responses={
        200: {"model": DiscoveryResponse, "description": "Discovery completed successfully"},
        400: {"model": DiscoveryErrorResponse, "description": "Connection or request error"},
        408: {"model": DiscoveryErrorResponse, "description": "Request timeout"},
        500: {"model": DiscoveryErrorResponse, "description": "Internal server error"},
    },
)
async def discover_devices() -> Union[DiscoveryResponse, JSONResponse]:
    """
    Initiate a Conbus discovery operation to find devices on the network.

    Sends a broadcast discovery telegram and collects responses from all connected devices.
    """
    service = ConbusDiscoverService()

    # Send discovery telegram and receive responses
    with service:
        response = service.send_telegram()

    if not response.success:
        return handle_service_error(response.error)

    # Build successful response
    return DiscoveryResponse(
        devices=response.discovered_devices,
    )

