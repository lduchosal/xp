from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any


@dataclass
class ConbusAutoreportResponse:
    """Represents a response from Conbus auto report operations (get/set)"""

    success: bool
    serial_number: str
    auto_report_status: Optional[str] = None
    result: Optional[str] = None
    sent_telegram: Optional[str] = None
    received_telegrams: Optional[list[str]] = None
    error: Optional[str] = None
    timestamp: Optional[datetime] = None

    def __post_init__(self) -> None:
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.received_telegrams is None:
            self.received_telegrams = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result_dict: Dict[str, Any] = {
            "success": self.success,
            "serial_number": self.serial_number,
            "error": self.error,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }

        # Include auto_report_status if available
        if self.auto_report_status is not None:
            result_dict["auto_report_status"] = self.auto_report_status

        # Include result for set operations
        if self.result is not None:
            result_dict["result"] = self.result

        # Include telegram details
        if self.sent_telegram is not None:
            result_dict["sent_telegram"] = self.sent_telegram

        if self.received_telegrams is not None:
            result_dict["received_telegrams"] = self.received_telegrams

        return result_dict
