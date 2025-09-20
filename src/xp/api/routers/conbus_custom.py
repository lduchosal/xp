"""FastAPI router for Conbus operations."""

import logging
from typing import Union

from fastapi.responses import JSONResponse

from .conbus import router
from .errors import handle_service_error
from ..models.custom import CustomResponse, CustomErrorResponse
from ...services.conbus_custom_service import ConbusCustomService

logger = logging.getLogger(__name__)

@router.get(
    "/custom/{serial_number}/{function_code}/{data}",
    response_model=Union[CustomResponse, CustomErrorResponse],
    responses={
        200: {"model": CustomResponse, "description": "Datapoint completed successfully"},
        400: {"model": CustomErrorResponse, "description": "Connection or request error"},
        408: {"model": CustomErrorResponse, "description": "Request timeout"},
        500: {"model": CustomErrorResponse, "description": "Internal server error"},
    },
)
async def custom_function(
        serial_number: str = "1702033007",
        function_code: str = "02",
        data = "00"
    ) -> Union[CustomResponse, CustomErrorResponse, JSONResponse]:
    """
    Initiate a Datapoint operation to find devices on the network.

    Sends a broadcastDatapoint telegram and collects responses from all connected devices.
    """
    service = ConbusCustomService()
    # SendDatapoint telegram and receive responses
    with service:
        response = service.send_custom_telegram(serial_number, function_code, data)

    if not response.success:
        return handle_service_error(response.error)

    if response.reply_telegram is None:
        return CustomErrorResponse(
            success=False,
            error=response.error,
        )

    # Build successful response
    return CustomResponse(
        success = True,
        result = response.reply_telegram.data_value,
        description = response.reply_telegram.datapoint_type.name,
    )
