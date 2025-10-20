"""Reply telegram model for console bus communication.

Reply telegrams are responses to system telegrams, containing the requested data
like temperature readings, status information, etc.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

from xp.models.telegram.datapoint_type import DataPointType
from xp.models.telegram.system_function import SystemFunction
from xp.models.telegram.telegram import Telegram
from xp.models.telegram.telegram_type import TelegramType


@dataclass
class ReplyTelegram(Telegram):
    """Represents a parsed reply telegram from the console bus.

    Format: <R{serial_number}F{function_code}D{data}{checksum}>
    Format: <R{serial_number}F{function_code}D{datapoint_type}{data_value}{checksum}>

    Examples:
        - raw_telegram: <R0020012521F02D18+26,0§CIL>
        - telegram_type : ReplyTelegram (R)
        - serial_number: 0020012521
        - function_code: 02
        - data: 18+26,0§C
        - datapoint_type: 18
        - data_value: +26,0§C
        - checksum: IL

    Attributes:
        serial_number: Serial number of the device.
        system_function: System function code.
        data: Raw data payload.
        datapoint_type: Type of datapoint.
        data_value: Parsed data value.
        parse_datapoint_value: Parsed value based on datapoint type.
    """

    serial_number: str = ""
    system_function: SystemFunction = SystemFunction.NONE
    data: str = ""
    datapoint_type: Optional[DataPointType] = None
    data_value: str = ""

    def __post_init__(self) -> None:
        """Initialize timestamp and telegram type."""
        if self.timestamp is None:
            self.timestamp = datetime.now()
        self.telegram_type = TelegramType.REPLY

    @property
    def parse_datapoint_value(self) -> dict[str, Any]:
        """Parse the data value based on data point type.

        Returns:
            Dictionary containing parsed value and metadata.
        """
        if self.datapoint_type == DataPointType.TEMPERATURE:
            return self._parse_temperature_value()
        elif self.datapoint_type == DataPointType.SW_TOP_VERSION:
            return self._parse_humidity_value()
        elif self.datapoint_type == DataPointType.VOLTAGE:
            return self._parse_voltage_value()
        elif self.datapoint_type == DataPointType.MODULE_ENERGY_LEVEL:
            return self._parse_current_value()
        elif self.datapoint_type == DataPointType.MODULE_TYPE:
            return self._parse_module_type_value()
        elif self.datapoint_type == DataPointType.SW_VERSION:
            return self._parse_sw_version_value()
        return {"raw_value": self.data_value, "parsed": False}

    def _parse_temperature_value(self) -> dict:
        """Parse temperature value like '+26,0§C'.

        Returns:
            Dictionary containing parsed temperature value and metadata.
        """
        try:
            # Remove unit indicator (§C)
            value_part = self.data_value.replace("§C", "")
            # Replace comma with dot for decimal
            value_str = value_part.replace(",", ".")
            temperature = float(value_str)

            return {
                "value": temperature,
                "unit": "°C",
                "formatted": f"{temperature:.1f}°C",
                "raw_value": self.data_value,
                "parsed": True,
            }
        except (ValueError, AttributeError):
            return {
                "raw_value": self.data_value,
                "parsed": False,
                "error": "Failed to parse temperature",
            }

    def _parse_humidity_value(self) -> dict:
        """Parse humidity value like '+65,5§H'.

        Returns:
            Dictionary containing parsed humidity value and metadata.
        """
        try:
            # Remove unit indicator (§H)
            value_part = self.data_value.replace("§RH", "")
            # Replace comma with dot for decimal
            value_str = value_part.replace(",", ".")
            humidity = float(value_str)

            return {
                "value": humidity,
                "unit": "%RH",
                "formatted": f"{humidity:.1f}%RH",
                "raw_value": self.data_value,
                "parsed": True,
            }
        except (ValueError, AttributeError):
            return {
                "raw_value": self.data_value,
                "parsed": False,
                "error": "Failed to parse humidity",
            }

    def _parse_voltage_value(self) -> dict:
        """Parse voltage value like '+12,5§V'.

        Returns:
            Dictionary containing parsed voltage value and metadata.
        """
        try:
            # Remove unit indicator (§V)
            value_part = self.data_value.replace("§V", "")
            # Replace comma with dot for decimal
            value_str = value_part.replace(",", ".")
            voltage = float(value_str)

            return {
                "value": voltage,
                "unit": "V",
                "formatted": f"{voltage:.1f}V",
                "raw_value": self.data_value,
                "parsed": True,
            }
        except (ValueError, AttributeError):
            return {
                "raw_value": self.data_value,
                "parsed": False,
                "error": "Failed to parse voltage",
            }

    def _parse_current_value(self) -> dict:
        """Parse current value like '+0,25§A'.

        Returns:
            Dictionary containing parsed current value and metadata.
        """
        try:
            # Remove unit indicator (§A)
            value_part = self.data_value.replace("§A", "")
            # Replace comma with dot for decimal
            value_str = value_part.replace(",", ".")
            current = float(value_str)

            return {
                "value": current,
                "unit": "A",
                "formatted": f"{current:.2f}A",
                "raw_value": self.data_value,
                "parsed": True,
            }
        except (ValueError, AttributeError):
            return {
                "raw_value": self.data_value,
                "parsed": False,
                "error": "Failed to parse current",
            }

    def _parse_module_type_value(self) -> dict:
        """Parse status value.

        Returns:
            Dictionary containing parsed module type value.
        """
        # Status values are typically alphanumeric codes
        return {
            "module_type": self.data_value,
            "raw_value": self.data_value,
            "parsed": True,
        }

    def _parse_sw_version_value(self) -> dict:
        """Parse version value like 'XP230_V1.00.04'.

        Returns:
            Dictionary containing parsed version information.
        """
        try:
            # Version format: {PRODUCT}_{VERSION}
            # Examples: XP230_V1.00.04, XP20_V0.01.05, XP33LR_V0.04.02, XP24_V0.34.03
            if "_V" in self.data_value:
                parts = self.data_value.split("_V", 1)
                if len(parts) == 2:
                    product = parts[0]
                    version = parts[1]

                    return {
                        "product": product,
                        "version": version,
                        "full_version": self.data_value,
                        "formatted": f"{product} v{version}",
                        "raw_value": self.data_value,
                        "parsed": True,
                    }

            # If format doesn't match expected pattern, treat as raw
            return {
                "full_version": self.data_value,
                "formatted": self.data_value,
                "raw_value": self.data_value,
                "parsed": False,
                "error": "Version format not recognized",
            }

        except (ValueError, AttributeError):
            return {
                "raw_value": self.data_value,
                "parsed": False,
                "error": "Failed to parse version",
            }

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization.

        Returns:
            Dictionary representation of the reply telegram.
        """
        parsed_data = self.parse_datapoint_value

        return {
            "serial_number": self.serial_number,
            "system_function": (
                {
                    "code": (
                        self.system_function.value if self.system_function else None
                    ),
                    "description": (
                        self.system_function.name if self.system_function else None
                    ),
                }
                if self.system_function
                else None
            ),
            "datapoint_type": (
                {
                    "code": self.datapoint_type.value if self.datapoint_type else None,
                    "description": (
                        self.datapoint_type.name if self.datapoint_type else None
                    ),
                }
                if self.datapoint_type
                else None
            ),
            "data_value": {"raw": self.data_value, "parsed": parsed_data},
            "checksum": self.checksum,
            "checksum_validated": self.checksum_validated,
            "raw_telegram": self.raw_telegram,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "telegram_type": self.telegram_type.value,
        }

    def __str__(self) -> str:
        """Human-readable string representation.

        Returns:
            Formatted string representation.
        """
        parsed = self.parse_datapoint_value
        if parsed.get("parsed", False) and "formatted" in parsed:
            value_display = parsed["formatted"]
        else:
            value_display = self.data_value

        system_func_name = (
            self.system_function.name if self.system_function else "Unknown"
        )
        datapoint_name = self.datapoint_type.name if self.datapoint_type else "Unknown"
        return (
            f"Reply Telegram: {system_func_name}\n "
            f"for {datapoint_name} = {value_display} "
            f"from device {self.serial_number}"
        )
