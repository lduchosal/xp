"""FastAPI router for Conbus operations."""

import logging
from typing import Union

from fastapi.responses import JSONResponse

from .conbus import router
from .errors import handle_service_error
from ..models.datapoint import DatapointResponse, DatapointErrorResponse
from ...models import ConbusDatapointRequest
from ...models.datapoint_type import DatapointTypeName
from ...services.conbus_datapoint_service import ConbusDatapointService

logger = logging.getLogger(__name__)

@router.get(
    "/datapoint/{sensor}/{serial}",
    response_model=Union[DatapointResponse, DatapointErrorResponse],
    responses={
        200: {"model": DatapointResponse, "description": "Datapoint completed successfully"},
        400: {"model": DatapointErrorResponse, "description": "Connection or request error"},
        408: {"model": DatapointErrorResponse, "description": "Request timeout"},
        500: {"model": DatapointErrorResponse, "description": "Internal server error"},
    },
)
async def datapoint_devices(sensor: str, serial: str) -> Union[DatapointResponse, DatapointErrorResponse, JSONResponse]:
    """
    Initiate a Datapoint operation to find devices on the network.

    Sends a broadcastDatapoint telegram and collects responses from all connected devices.
    """
    service = ConbusDatapointService()

    # CreateDatapoint request
    conbus_request = ConbusDatapointRequest(
        serial_number=serial,
        datapoint_type=DatapointTypeName(sensor)
    )

    # SendDatapoint telegram and receive responses
    with service:
        response = service.send_telegram(conbus_request)

    if not response.success:
        return handle_service_error(response)

    # Build successful response
    return DatapointResponse(
        success = True,
        result = response.received_telegrams[0]
    )
