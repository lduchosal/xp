"""FastAPI router for Conbus operations."""

import json
import logging
from typing import Union

from fastapi.responses import JSONResponse

from .conbus import router
from .errors import handle_service_error
from ..models.api import ApiResponse, ApiErrorResponse
from ...services.conbus_blink_service import ConbusBlinkService

logger = logging.getLogger(__name__)


@router.get(
    "/blink/on/{serial_number}",
    response_model=Union[ApiResponse, ApiErrorResponse],
    responses={
        200: {"model": ApiResponse, "description": "Input completed successfully"},
        400: {"model": ApiErrorResponse, "description": "Connection or request error"},
        408: {"model": ApiErrorResponse, "description": "Request timeout"},
        500: {"model": ApiErrorResponse, "description": "Internal server error"},
    },
)
async def blink_on(
    serial_number: str = "1702033007",
) -> Union[ApiResponse, ApiErrorResponse, JSONResponse]:
    """
    Initiate Input operation to find devices on the network.

    Sends a broadcastInput telegram and collects responses from all connected devices.
    """
    service = ConbusBlinkService()

    # SendInput telegram and receive responses
    with service:
        response = service.send_blink_telegram(
            serial_number=serial_number, on_or_off="on"
        )

    if not response.success:
        return handle_service_error(response.error or "Unknown error")

    logger.debug(json.dumps(response.to_dict(), indent=2))

    # Build successful response
    return ApiResponse(
        success=True,
        result=response.system_function.name,
        description=(
            response.reply_telegram.system_function.get_description()
            if response.reply_telegram and response.reply_telegram.system_function
            else None
        ),
        # raw_telegram = response.output_telegram.raw_telegram,
    )


@router.get(
    "/blink/off/{serial_number}",
    response_model=Union[ApiResponse, ApiErrorResponse],
    responses={
        200: {"model": ApiResponse, "description": "Input completed successfully"},
        400: {"model": ApiErrorResponse, "description": "Connection or request error"},
        408: {"model": ApiErrorResponse, "description": "Request timeout"},
        500: {"model": ApiErrorResponse, "description": "Internal server error"},
    },
)
async def blink_off(
    serial_number: str = "1702033007",
) -> Union[ApiResponse, ApiErrorResponse, JSONResponse]:
    """
    Initiate Input operation to find devices on the network.

    Sends a broadcastInput telegram and collects responses from all connected devices.
    """
    service = ConbusBlinkService()

    # SendInput telegram and receive responses
    with service:
        response = service.send_blink_telegram(
            serial_number=serial_number, on_or_off="off"
        )

    if not response.success:
        return handle_service_error(response.error or "Unknown error")

    logger.debug(json.dumps(response.to_dict(), indent=2))

    # Build successful response
    return ApiResponse(
        success=True,
        result=response.system_function.name,
        description=(
            response.reply_telegram.system_function.get_description()
            if response.reply_telegram and response.reply_telegram.system_function
            else None
        ),
        # raw_telegram = response.output_telegram.raw_telegram,
    )
