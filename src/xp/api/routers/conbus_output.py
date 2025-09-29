"""FastAPI router for Conbus operations."""

import json
import logging
from typing import Union

from fastapi.responses import JSONResponse

from .conbus import router
from .errors import handle_service_error
from ..models.api import ApiResponse, ApiErrorResponse
from ...models.action_type import ActionType
from ...services.conbus_output_service import ConbusOutputService

logger = logging.getLogger(__name__)


@router.get(
    "/output/{action}/{serial}/{device_input}",
    response_model=Union[ApiResponse, ApiErrorResponse],
    responses={
        200: {"model": ApiResponse, "description": "Input completed successfully"},
        400: {"model": ApiErrorResponse, "description": "Connection or request error"},
        408: {"model": ApiErrorResponse, "description": "Request timeout"},
        500: {"model": ApiErrorResponse, "description": "Internal server error"},
    },
)
async def input_action(
    action: ActionType = ActionType.OFF_PRESS,
    serial: str = "1702033007",
    device_input: int = 0,
) -> Union[ApiResponse, ApiErrorResponse, JSONResponse]:
    """
    Initiate Input operation to find devices on the network.

    Sends a broadcastInput telegram and collects responses from all connected devices.
    """
    service = ConbusOutputService()

    # SendInput telegram and receive responses
    with service:
        response = service.send_action(serial, device_input, action)

    if not response.success:
        return handle_service_error(response.error or "Unknown error")

    logger.debug(json.dumps(response.to_dict(), indent=2))

    # Build successful response
    if response.output_telegram and response.output_telegram.system_function:
        return ApiResponse(
            success=True,
            result=response.output_telegram.system_function.name,
            description=response.output_telegram.system_function.get_description(),
            # raw_telegram = response.output_telegram.raw_telegram,
        )
    return ApiResponse(
        success=True,
        result="Output command sent",
        description="Output command was sent successfully",
    )


@router.get(
    "/output/status/{serial_number}",
    response_model=Union[ApiResponse, ApiErrorResponse],
    responses={
        200: {"model": ApiResponse, "description": "Query completed successfully"},
        400: {"model": ApiErrorResponse, "description": "Connection or request error"},
        408: {"model": ApiErrorResponse, "description": "Request timeout"},
        500: {"model": ApiErrorResponse, "description": "Internal server error"},
    },
)
async def output_status(
    serial_number: str,
) -> Union[ApiResponse, ApiErrorResponse, JSONResponse]:
    """
    Initiate Input operation to find devices on the network.

    Sends a broadcastInput telegram and collects responses from all connected devices.
    """
    service = ConbusOutputService()

    # SendInput telegram and receive responses
    with service:
        response = service.get_output_state(serial_number)

    if not response.success:
        return handle_service_error(response.error or "Unknown error")

    # Build successful response
    if response.datapoint_telegram and response.datapoint_telegram.datapoint_type:
        return ApiResponse(
            success=True,
            result=response.datapoint_telegram.data_value,
            description=response.datapoint_telegram.datapoint_type.name,
        )
    return ApiResponse(
        success=True,
        result="No data available",
        description="Output status retrieved but no data available",
    )


@router.get(
    "/output/state/{serial_number}",
    response_model=Union[ApiResponse, ApiErrorResponse],
    responses={
        200: {"model": ApiResponse, "description": "Query completed successfully"},
        400: {"model": ApiErrorResponse, "description": "Connection or request error"},
        408: {"model": ApiErrorResponse, "description": "Request timeout"},
        500: {"model": ApiErrorResponse, "description": "Internal server error"},
    },
)
async def output_state(
    serial_number: str,
) -> Union[ApiResponse, ApiErrorResponse, JSONResponse]:
    """
    Initiate Input operation to find devices on the network.

    Sends a broadcastInput telegram and collects responses from all connected devices.
    """
    service = ConbusOutputService()

    # SendInput telegram and receive responses
    with service:
        response = service.get_module_state(serial_number)

    if not response.success:
        return handle_service_error(response.error or "Unknown error")

    # Build successful response
    if response.datapoint_telegram and response.datapoint_telegram.datapoint_type:
        return ApiResponse(
            success=True,
            result=response.datapoint_telegram.data_value,
            description=response.datapoint_telegram.datapoint_type.name,
        )
    return ApiResponse(
        success=True,
        result="No data available",
        description="Module state retrieved but no data available",
    )
