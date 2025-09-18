"""FastAPI router for Conbus operations."""

import logging
from typing import Union
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from .errors import handle_service_error
from ...services.conbus_client_send_service import ConbusClientSendService
from ...models import ConbusSendRequest, DatapointTypeName
from ..models.discovery import (
    DiscoveryRequest,
    DiscoveryResponse,
    DiscoveryErrorResponse,
)

router = APIRouter(prefix="/api/xp/conbus", tags=["conbus"])
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
async def discover_devices(request: DiscoveryRequest) -> Union[DiscoveryResponse, JSONResponse]:
    """
    Initiate a Conbus discovery operation to find devices on the network.

    Sends a broadcast discovery telegram and collects responses from all connected devices.
    """
    service = ConbusClientSendService()

    # Create discovery request
    conbus_request = ConbusSendRequest(
        telegram_type=DatapointTypeName.DISCOVERY,
        target_serial=None
    )

    # Send discovery telegram and receive responses
    with service:
        response = service.send_telegram(conbus_request)

    if not response.success:
        return handle_service_error(response)

    # Build successful response
    return DiscoveryResponse(
        devices=response.discovered_devices,
    )
