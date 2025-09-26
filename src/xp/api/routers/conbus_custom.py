"""FastAPI router for Conbus operations."""

import logging
from typing import Union

from fastapi.responses import JSONResponse

from .conbus import router
from .errors import handle_service_error
from ..models.api import ApiResponse, ApiErrorResponse
from ...services.conbus_custom_service import ConbusCustomService

logger = logging.getLogger(__name__)


@router.get(
    "/custom/{serial_number}/{function_code}/{data}",
    response_model=Union[ApiResponse, ApiErrorResponse],
    responses={
        200: {"model": ApiResponse, "description": "Datapoint completed successfully"},
        400: {"model": ApiErrorResponse, "description": "Connection or request error"},
        408: {"model": ApiErrorResponse, "description": "Request timeout"},
        500: {"model": ApiErrorResponse, "description": "Internal server error"},
    },
)
async def custom_function(
    serial_number: str = "1702033007", function_code: str = "02", data: str = "00"
) -> Union[ApiResponse, ApiErrorResponse, JSONResponse]:
    """
    Initiate a Datapoint operation to find devices on the network.

    Sends a broadcastDatapoint telegram and collects responses from all connected devices.
    """
    service = ConbusCustomService()
    # SendDatapoint telegram and receive responses
    with service:
        response = service.send_custom_telegram(serial_number, function_code, data)

    if not response.success:
        return handle_service_error(response.error or "Unknown error")

    if response.reply_telegram is None:
        return ApiErrorResponse(
            success=False,
            error=response.error or "Unknown error",
        )

    # Build successful response
    if response.reply_telegram and response.reply_telegram.datapoint_type:
        return ApiResponse(
            success=True,
            result=response.reply_telegram.data_value,
            description=response.reply_telegram.datapoint_type.name,
        )
    return ApiResponse(
        success=True,
        result=response.reply_telegram.data_value,
        description="Custom command executed successfully",
    )
