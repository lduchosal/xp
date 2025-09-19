"""FastAPI router for Conbus operations."""
import json
import logging
from typing import Union

from fastapi.responses import JSONResponse

from .conbus import router
from .errors import handle_service_error
from ..models.datapoint import DatapointResponse
from ..models.input import InputResponse, InputErrorResponse
from ...models.action_type import ActionType
from ...services.conbus_input_service import ConbusInputService

logger = logging.getLogger(__name__)

@router.get(
    "/input/{action}/{serial}/{input}",
    response_model=Union[InputResponse, InputErrorResponse],
    responses={
        200: {"model": InputResponse, "description": "Input completed successfully"},
        400: {"model": InputErrorResponse, "description": "Connection or request error"},
        408: {"model": InputErrorResponse, "description": "Request timeout"},
        500: {"model": InputErrorResponse, "description": "Internal server error"},
    },
)
async def input_action(
        action: str = "on",
        serial: str = "1702033007",
        device_input: int = 0
) -> Union[InputResponse, InputErrorResponse, JSONResponse]:
    """
    Initiate Input operation to find devices on the network.

    Sends a broadcastInput telegram and collects responses from all connected devices.
    """
    service = ConbusInputService()
    action_type = ActionType.PRESS
    if action.lower() == "on" : action_type = ActionType.RELEASE

    # SendInput telegram and receive responses
    with service:
        response = service.send_action(serial, device_input, action_type)

    if not response.success:
        return handle_service_error(response.error)

    logger.debug(json.dumps(response.to_dict(), indent=2))

    # Build successful response
    return InputResponse(
        success = True,
        result = response.input_telegram.raw_telegram,
        description = response.input_telegram.input_description,
    )


@router.get(
    "/input/status/{serial}",
    response_model=Union[InputResponse, InputErrorResponse],
    responses={
        200: {"model": InputResponse, "description": "Input completed successfully"},
        400: {"model": InputErrorResponse, "description": "Connection or request error"},
        408: {"model": InputErrorResponse, "description": "Request timeout"},
        500: {"model": InputErrorResponse, "description": "Internal server error"},
    },
)
async def input_status(serial: str) -> Union[DatapointResponse, InputErrorResponse, JSONResponse]:
    """
    Initiate Input operation to find devices on the network.

    Sends a broadcastInput telegram and collects responses from all connected devices.
    """
    service = ConbusInputService()

    # SendInput telegram and receive responses
    with service:
        response = service.send_status(serial)

    if not response.success:
        return handle_service_error(response.error)

    # Build successful response
    return DatapointResponse(
        success = True,
        result = response.datapoint_telegram.data_value,
        description = response.datapoint_telegram.data_point_description,
    )
