"""Conbus Client Send Service for TCP communication with Conbus servers.

This service implements a TCP client that connects to Conbus servers and sends
various types of telegrams including discovery, version, and sensor data requests.
"""

import logging

from .conbus_service import ConbusService
from ..models import (
    ConbusDatapointResponse,
    DatapointTypeName,
)
from ..models.datapoint_type import DataPointType
from ..models.system_function import SystemFunction
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
        self.conbus_service = ConbusService(config_path)

        # Set up logging
        self.logger = logging.getLogger(__name__)

    def send_telegram(self, datapoint_type: DatapointTypeName, serial_number: str) -> ConbusDatapointResponse:
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

        function_code = SystemFunction.READ_DATAPOINT
        datapoint = sensor_data_points.get(datapoint_type)

        # Send telegram
        response = self.conbus_service.send_telegram(serial_number, function_code, datapoint)
        datapoint_telegram = None
        if len(response.received_telegrams) > 0:
            telegram = response.received_telegrams[0]
            datapoint_telegram = self.telegram_service.parse_telegram(telegram)

        return ConbusDatapointResponse(
            success=True,
            serial_number=serial_number,
            datapoint_type=datapoint_type,
            datapoint=datapoint,
            sent_telegram=response.sent_telegram,
            received_telegrams=response.received_telegrams,
            datapoint_telegram=datapoint_telegram,
        )

    def send_datapoint_request(
        self, serial_number: str, sensor_type: DatapointTypeName
    ) -> ConbusDatapointResponse:

        """Send sensor data request telegram"""
        if sensor_type.value not in [
            DatapointTypeName.VOLTAGE.value,
            DatapointTypeName.TEMPERATURE.value,
            DatapointTypeName.CURRENT.value,
            DatapointTypeName.HUMIDITY.value,
            DatapointTypeName.CHANNEL_STATES.value,
        ]:
            raise ConbusDatapointError(f"Invalid sensor type: {sensor_type.value}")

        return self.send_telegram(datapoint_type=sensor_type, serial_number=serial_number)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
      # Cleanup logic if needed
        pass

