"""Conbus datapoint response model."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from xp.models.telegram.datapoint_type import DataPointType
from xp.models.telegram.reply_telegram import ReplyTelegram
from xp.models.telegram.system_function import SystemFunction


@dataclass
class ConbusDatapointResponse:
    """Represents a response from Conbus send operation.

    Attributes:
        success: Whether the operation was successful.
        serial_number: Serial number of the device.
        system_function: System function used for query.
        datapoint_type: Type of datapoint queried.
        sent_telegram: Telegram sent to device.
        received_telegrams: List of telegrams received.
        datapoint_telegram: Parsed datapoint telegram.
        data_value: Value of the datapoint telegram.
        datapoints: List of datapoint values.
        error: Error message if operation failed.
        timestamp: Timestamp of the response.
    """

    success: bool
    serial_number: Optional[str] = None
    system_function: Optional[SystemFunction] = None
    datapoint_type: Optional[DataPointType] = None
    sent_telegram: Optional[str] = None
    received_telegrams: Optional[list] = None
    datapoint_telegram: Optional[ReplyTelegram] = None
    data_value: str = ""
    datapoints: Optional[List[Dict[str, str]]] = None
    error: Optional[str] = None
    timestamp: Optional[datetime] = None

    def __post_init__(self) -> None:
        """Initialize timestamp, received_telegrams, and datapoints if not provided."""
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.received_telegrams is None:
            self.received_telegrams = []
        if self.datapoints is None:
            self.datapoints = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization.

        Returns:
            Dictionary representation of the response.
        """
        result: Dict[str, Any] = {
            "success": self.success,
            "serial_number": self.serial_number,
            "data_value": self.data_value,
            "error": self.error,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }

        # Include system_function for single datapoint queries
        if self.system_function is not None:
            result["system_function"] = str(self.system_function)

        # Include datapoint_type for single datapoint queries
        if self.datapoint_type is not None:
            result["datapoint_type"] = str(self.datapoint_type)

        # Include sent_telegram for single datapoint queries
        if self.sent_telegram is not None:
            result["sent_telegram"] = self.sent_telegram

        # Include received_telegrams for single datapoint queries
        if self.received_telegrams is not None:
            result["received_telegrams"] = self.received_telegrams

        # Include datapoint_telegram for single datapoint queries
        if self.datapoint_telegram is not None:
            result["datapoint_telegram"] = self.datapoint_telegram.to_dict()

        # Include datapoints for all datapoints queries
        if self.datapoints is not None and len(self.datapoints) > 0:
            result["datapoints"] = self.datapoints

        return result
