"""FastAPI router for Conbus operations."""

import logging
from typing import Union

from fastapi.responses import JSONResponse

from .conbus import router
from .errors import handle_service_error
from ..models.datapoint import DatapointResponse, DatapointErrorResponse
from ...models.datapoint_type import DatapointTypeName
from ...services.conbus_datapoint_service import ConbusDatapointService

logger = logging.getLogger(__name__)

@router.get(
    "/datapoint/{datapoint}/{serial_number}",
    response_model=Union[DatapointResponse, DatapointErrorResponse],
    responses={
        200: {"model": DatapointResponse, "description": "Datapoint completed successfully"},
        400: {"model": DatapointErrorResponse, "description": "Connection or request error"},
        408: {"model": DatapointErrorResponse, "description": "Request timeout"},
        500: {"model": DatapointErrorResponse, "description": "Internal server error"},
    },
)
async def datapoint_devices(
        datapoint: DatapointTypeName = DatapointTypeName.VERSION,
        serial_number: str = "1702033007"
    ) -> Union[DatapointResponse, DatapointErrorResponse, JSONResponse]:
    """
    Initiate a Datapoint operation to find devices on the network.

    Sends a broadcastDatapoint telegram and collects responses from all connected devices.
    """
    service = ConbusDatapointService()

    # SendDatapoint telegram and receive responses
    with service:
        response = service.send_telegram(
            datapoint_type=DatapointTypeName(datapoint),
            serial_number=serial_number)

    if not response.success:
        return handle_service_error(response.error)

    if response.datapoint_telegram is None:
        return DatapointErrorResponse(
            success=False,
            error=response.error,
        )

    # Build successful response
    return DatapointResponse(
        success = True,
        result = response.datapoint_telegram.data_value,
        description = response.datapoint_telegram.data_point_description,
    )
