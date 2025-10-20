"""Version service for handling version information parsing and validation.

This service provides business logic for version operations,
following the layered architecture pattern.
"""

import re

from xp.models.response import Response
from xp.models.telegram.datapoint_type import DataPointType
from xp.models.telegram.reply_telegram import ReplyTelegram
from xp.models.telegram.system_function import SystemFunction
from xp.models.telegram.system_telegram import SystemTelegram
from xp.utils.checksum import calculate_checksum


class VersionParsingError(Exception):
    """Raised when version parsing fails."""

    pass


class VersionService:
    """Service class for version-related operations."""

    def __init__(self) -> None:
        """Initialize the version service."""
        pass

    @staticmethod
    def parse_version_string(version_string: str) -> Response:
        """Parse a version string into its components.

        Args:
            version_string: Version string in format 'XP230_V1.00.04'

        Returns:
            Response object with parsed version information
        """
        try:
            # Version format: {PRODUCT}_{VERSION}
            # Examples: XP230_V1.00.04, XP20_V0.01.05, XP33LR_V0.04.02, XP24_V0.34.03
            if "_V" in version_string:
                parts = version_string.split("_V", 1)
                if len(parts) == 2:
                    product = parts[0]
                    version = parts[1]

                    # Validate version format (should be like 1.00.04)
                    version_pattern = re.compile(r"^\d+\.\d+\.\d+$")
                    if version_pattern.match(version):
                        return Response(
                            success=True,
                            data={
                                "product": product,
                                "version": version,
                                "full_version": version_string,
                                "formatted": f"{product} v{version}",
                                "raw_value": version_string,
                                "valid_format": True,
                            },
                            error=None,
                        )
                    else:
                        return Response(
                            success=True,
                            data={
                                "product": product,
                                "version": version,
                                "full_version": version_string,
                                "formatted": f"{product} v{version}",
                                "raw_value": version_string,
                                "valid_format": False,
                                "warning": "Version format doesn't match expected pattern x.xx.xx",
                            },
                            error=None,
                        )

            # If format doesn't match expected pattern
            return Response(
                success=False,
                data={"raw_value": version_string, "valid_format": False},
                error="Version format not recognized. Expected format: PRODUCT_Vx.xx.xx",
            )

        except Exception as e:
            return Response(
                success=False, data=None, error=f"Version parsing failed: {e}"
            )

    @staticmethod
    def generate_version_request_telegram(serial_number: str) -> Response:
        """Generate a system telegram to request version information.

        Args:
            serial_number: 10-digit serial number of the device

        Returns:
            Response object with generated telegram
        """
        try:
            if len(serial_number) != 10 or not serial_number.isdigit():
                return Response(
                    success=False,
                    data=None,
                    error="Serial number must be exactly 10 digits",
                )

            # Build telegram: S{serial_number}F{function}D{data_point}
            # Function 02 = Read Data point, Data Point 02 = Version
            data_part = f"S{serial_number}F02D02"

            # Calculate checksum
            checksum = calculate_checksum(data_part)

            # Complete telegram
            telegram = f"<{data_part}{checksum}>"

            return Response(
                success=True,
                data={
                    "telegram": telegram,
                    "serial_number": serial_number,
                    "function_code": "02",
                    "datapoint_code": "02",
                    "checksum": checksum,
                    "operation": "version_request",
                },
                error=None,
            )

        except Exception as e:
            return Response(
                success=False,
                data=None,
                error=f"Version request telegram generation failed: {e}",
            )

    @staticmethod
    def validate_version_telegram(telegram: SystemTelegram) -> Response:
        """Validate if a system telegram is a valid version request.

        Args:
            telegram: Parsed system telegram

        Returns:
            Response object with validation result
        """
        try:
            is_version_request = (
                telegram.system_function == SystemFunction.READ_DATAPOINT
                and telegram.datapoint_type == DataPointType.SW_VERSION
            )

            return Response(
                success=True,
                data={
                    "is_version_request": is_version_request,
                    "serial_number": telegram.serial_number,
                    "function": (
                        telegram.system_function.value
                        if telegram.system_function
                        else None
                    ),
                    "data_point": (
                        telegram.datapoint_type.value
                        if telegram.datapoint_type
                        else None
                    ),
                    "function_description": (
                        telegram.system_function.name
                        if telegram.system_function
                        else None
                    ),
                    "data_point_description": (
                        telegram.datapoint_type.name
                        if telegram.datapoint_type
                        else None
                    ),
                },
                error=None,
            )

        except Exception as e:
            return Response(
                success=False,
                data=None,
                error=f"Version telegram validation failed: {e}",
            )

    @staticmethod
    def parse_version_reply(telegram: ReplyTelegram) -> Response:
        """Parse version information from a reply telegram.

        Args:
            telegram: Parsed reply telegram containing version data

        Returns:
            Response object with version information
        """
        try:
            # Check if this is a version reply
            if telegram.datapoint_type != DataPointType.SW_VERSION:
                return Response(
                    success=False,
                    data=None,
                    error=f"Not a version reply telegram. "
                    f"Data point: "
                    f"{telegram.datapoint_type.name if telegram.datapoint_type else 'Unknown'}",
                )

            # Parse the version using the telegram's built-in parser
            parsed_data = telegram.parse_datapoint_value

            if parsed_data.get("parsed", False):
                return Response(
                    success=True,
                    data={
                        "serial_number": telegram.serial_number,
                        "version_info": parsed_data,
                        "checksum_valid": telegram.checksum_validated,
                        "raw_telegram": telegram.raw_telegram,
                    },
                    error=None,
                )
            else:
                return Response(
                    success=False,
                    data={
                        "serial_number": telegram.serial_number,
                        "raw_value": telegram.data_value,
                        "checksum_valid": telegram.checksum_validated,
                        "raw_telegram": telegram.raw_telegram,
                    },
                    error=parsed_data.get(
                        "error", "Failed to parse version information"
                    ),
                )

        except Exception as e:
            return Response(
                success=False,
                data=None,
                error=f"Version reply parsing failed: {e}",
            )

    @staticmethod
    def format_version_summary(version_data: dict) -> str:
        """Format version information for human-readable output.

        Args:
            version_data: Version information dictionary

        Returns:
            Formatted string summary
        """
        try:
            if "version_info" in version_data:
                version_info = version_data["version_info"]
                serial = version_data.get("serial_number", "Unknown")

                if version_info.get("parsed", False):
                    product = version_info.get("product", "Unknown")
                    version = version_info.get("version", "Unknown")

                    summary = "Device Version Information:\n"
                    summary += f"Serial Number: {serial}\n"
                    summary += f"Product: {product}\n"
                    summary += f"Version: {version}\n"
                    summary += (
                        f"Full Version: {version_info.get('full_version', 'Unknown')}\n"
                    )

                    checksum_status = ""
                    if "checksum_valid" in version_data:
                        status = "✓" if version_data["checksum_valid"] else "✗"
                        checksum_status = f" ({status})"

                    summary += f"Checksum: Valid{checksum_status}"

                    return summary
                else:
                    return f"Version parsing failed for device {serial}: {version_info.get('error', 'Unknown error')}"
            else:
                return "No version information available"

        except Exception as e:
            return f"Error formatting version summary: {e}"
