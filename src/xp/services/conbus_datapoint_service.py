"""Conbus Client Send Service for TCP communication with Conbus servers.

This service implements a TCP client that connects to Conbus servers and sends
various types of telegrams including discovery, version, and sensor data requests.
"""

import logging

from .conbus_service import ConbusService
from ..models import (
    ConbusDatapointRequest,
    ConbusDatapointResponse,
    DatapointTypeName,
)
from ..models.datapoint_type import DataPointType
from ..services.telegram_service import TelegramService


class ConbusDatapointError(Exception):
    """Raised when Conbus client send operations fail"""

    pass


class ConbusDatapointService:
    """
    TCP client service for sending telegrams to Conbus servers.

    Manages TCP socket connections, handles telegram generation and transmission,
    and processes server responses.
    """

    def __init__(self, config_path: str = "cli.yml"):
        """Initialize the Conbus client send service"""

        # Service dependencies
        self.telegram_service = TelegramService()
        self.conbus_service = ConbusService()

        # Set up logging
        self.logger = logging.getLogger(__name__)

    def send_telegram(self, request: ConbusDatapointRequest) -> ConbusDatapointResponse:
        """Send a telegram to the Conbus server"""

        # Generate telegram based on type
        # Map telegram types to data point codes
        sensor_data_points = {
            DatapointTypeName.VERSION: DataPointType.VERSION.value,  # Version data point
            DatapointTypeName.VOLTAGE: DataPointType.VOLTAGE.value,  # Voltage data point
            DatapointTypeName.TEMPERATURE: DataPointType.TEMPERATURE.value,  # Temperature data point
            DatapointTypeName.CURRENT: DataPointType.CURRENT.value,  # Current data point
            DatapointTypeName.HUMIDITY: DataPointType.HUMIDITY.value,  # Humidity data point
        }

        data_point = sensor_data_points.get(request.datapoint_type)

        # Send telegram
        responses = self.conbus_service.send_telegram(request.serial_number, "02", data_point)

        return ConbusDatapointResponse(
            success=True,
            request=request,
            sent_telegram=responses.sent_telegram,
            received_telegrams=responses.received_telegrams,
        )

    def datapoint_request(
        self, serial_number: str, sensor_type: DatapointTypeName
    ) -> ConbusDatapointResponse:
        print(f"sensor_type.__class__.__module__: {sensor_type.__class__.__module__}")
        print(f"DatapointTypeName.__module__: {DatapointTypeName.__module__}")

        """Send sensor data request telegram"""
        if sensor_type.value not in [
            DatapointTypeName.VOLTAGE.value,
            DatapointTypeName.TEMPERATURE.value,
            DatapointTypeName.CURRENT.value,
            DatapointTypeName.HUMIDITY.value,
        ]:
            raise ConbusDatapointError(f"Invalid sensor type: {sensor_type.value}")

        request = ConbusDatapointRequest(
            datapoint_type=sensor_type, serial_number=serial_number
        )
        return self.send_telegram(request)

