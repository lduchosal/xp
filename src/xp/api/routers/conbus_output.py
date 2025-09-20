"""FastAPI router for Conbus operations."""
import json
import logging
from typing import Union

from fastapi.responses import JSONResponse

from .conbus import router
from .errors import handle_service_error
from ..models.datapoint import DatapointResponse
from ..models.input import OutputResponse, OutputErrorResponse
from ...models.action_type import ActionType
from ...services.conbus_output_service import ConbusOutputService

logger = logging.getLogger(__name__)

@router.get(
    "/output/{action}/{serial}/{device_input}",
    response_model=Union[OutputResponse, OutputErrorResponse],
    responses={
        200: {"model": OutputResponse, "description": "Input completed successfully"},
        400: {"model": OutputErrorResponse, "description": "Connection or request error"},
        408: {"model": OutputErrorResponse, "description": "Request timeout"},
        500: {"model": OutputErrorResponse, "description": "Internal server error"},
    },
)
async def input_action(
        action: ActionType = ActionType.PRESS,
        serial: str = "1702033007",
        device_input: int = 0
) -> Union[OutputResponse, OutputErrorResponse, JSONResponse]:
    """
    Initiate Input operation to find devices on the network.

    Sends a broadcastInput telegram and collects responses from all connected devices.
    """
    service = ConbusOutputService()

    # SendInput telegram and receive responses
    with service:
        response = service.send_action(serial, device_input, action)

    if not response.success:
        return handle_service_error(response.error)

    logger.debug(json.dumps(response.to_dict(), indent=2))

    # Build successful response
    return OutputResponse(
        success = True,
        result = response.output_telegram.system_function.name,
        description = response.output_telegram.system_function.get_description(),
        # raw_telegram = response.input_telegram.raw_telegram,
    )


@router.get(
    "/output/status/{serial_number}",
    response_model=Union[OutputResponse, OutputErrorResponse],
    responses={
        200: {"model": OutputResponse, "description": "Query completed successfully"},
        400: {"model": OutputErrorResponse, "description": "Connection or request error"},
        408: {"model": OutputErrorResponse, "description": "Request timeout"},
        500: {"model": OutputErrorResponse, "description": "Internal server error"},
    },
)
async def output_status(serial_number: str) -> Union[DatapointResponse, OutputErrorResponse, JSONResponse]:
    """
    Initiate Input operation to find devices on the network.

    Sends a broadcastInput telegram and collects responses from all connected devices.
    """
    service = ConbusOutputService()

    # SendInput telegram and receive responses
    with service:
        response = service.send_status(serial_number)

    if not response.success:
        return handle_service_error(response.error)

    # Build successful response
    return DatapointResponse(
        success = True,
        result = response.datapoint_telegram.data_value,
        description = response.datapoint_telegram.datapoint_type.name,
    )
