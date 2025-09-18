"""FastAPI router for Conbus operations."""

import logging
from typing import Union
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from ...services.conbus_client_send_service import ConbusClientSendService, ConbusClientSendError
from ...services.telegram_service import TelegramService
from ...models import ConbusSendRequest, TelegramType
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
    telegram_service = TelegramService()

    try:
        # Create discovery request
        conbus_request = ConbusSendRequest(
            telegram_type=TelegramType.DISCOVERY,
            target_serial=None
        )

        # Send discovery telegram and receive responses
        with service:
            response = service.send_telegram(conbus_request)

        if not response.success:
            # Handle service errors
            error_msg = response.error or "Unknown service error"
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            return JSONResponse(
                status_code=status_code,
                content=DiscoveryErrorResponse(error=error_msg).model_dump()
            )

        # Parse received telegrams to extract device information
        discovered_devices = []
        received_telegrams = response.received_telegrams or []

        for telegrams_str in received_telegrams:
            for telegram_str in telegrams_str.split("\n"):
                try:
                    # Parse telegram using TelegramService
                    telegram_result = telegram_service.parse_telegram(telegram_str)
                    discovered_devices.append(telegram_result.serial_number)

                except Exception as e:
                    logger.warning(f"Failed to parse telegram '{telegram_str}': {e}")
                    continue

        # Build successful response
        return DiscoveryResponse(
            devices=discovered_devices,
        )

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except ConbusClientSendError as e:
        error_msg = str(e)
        logger.error(f"Conbus client error: {error_msg}")

        # Map specific errors to appropriate HTTP status codes
        if "Connection timeout" in error_msg or "timeout" in error_msg.lower():
            status_code = status.HTTP_408_REQUEST_TIMEOUT
        elif "Unable to connect" in error_msg or "Connection refused" in error_msg:
            status_code = status.HTTP_400_BAD_REQUEST
        else:
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

        return JSONResponse(
            status_code=status_code,
            content=DiscoveryErrorResponse(error=error_msg).model_dump()
        )
    except Exception as e:
        error_msg = f"Internal server error: {e}"
        logger.error(f"Unexpected error in discovery endpoint: {error_msg}")

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=DiscoveryErrorResponse(error=error_msg).model_dump()
        )