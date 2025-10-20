"""Checksum service for telegram protocol validation and generation.

This service provides business logic for checksum operations,
following the layered architecture pattern.
"""

from typing import Union

from xp.models.response import Response
from xp.utils.checksum import calculate_checksum, calculate_checksum32


class TelegramChecksumService:
    """Service class for checksum operations."""

    def __init__(self) -> None:
        """Initialize the checksum service."""
        pass

    @staticmethod
    def calculate_simple_checksum(data: str) -> Response:
        """Calculate simple XOR checksum for string data.

        Args:
            data: String data to calculate checksum for.

        Returns:
            Response object with checksum result.
        """
        try:
            checksum = calculate_checksum(data)

            return Response(
                success=True,
                data={"input": data, "checksum": checksum, "algorithm": "simple_xor"},
                error=None,
            )
        except Exception as e:
            return Response(
                success=False, data=None, error=f"Checksum calculation failed: {e}"
            )

    @staticmethod
    def calculate_crc32_checksum(data: Union[str, bytes]) -> Response:
        """Calculate CRC32 checksum for data.

        Args:
            data: String or bytes data to calculate checksum for.

        Returns:
            Response object with checksum result.
        """
        try:
            # Convert string to bytes if needed
            if isinstance(data, str):
                byte_data = data.encode("utf-8")
            else:  # isinstance(data, bytes)
                byte_data = data

            checksum = calculate_checksum32(byte_data)

            return Response(
                success=True,
                data={
                    "input": data,
                    "input_type": "string" if isinstance(data, str) else "bytes",
                    "input_length": len(byte_data),
                    "checksum": checksum,
                    "algorithm": "crc32",
                },
                error=None,
            )
        except Exception as e:
            return Response(
                success=False,
                data=None,
                error=f"CRC32 checksum calculation failed: {e}",
            )

    @staticmethod
    def validate_checksum(data: str, expected_checksum: str) -> Response:
        """Validate data against expected simple checksum.

        Args:
            data: Original data.
            expected_checksum: Expected checksum value.

        Returns:
            Response object with validation result.
        """
        try:
            calculated_checksum = calculate_checksum(data)
            is_valid = calculated_checksum == expected_checksum

            return Response(
                success=True,
                data={
                    "input": data,
                    "calculated_checksum": calculated_checksum,
                    "expected_checksum": expected_checksum,
                    "is_valid": is_valid,
                },
                error=None,
            )
        except Exception as e:
            return Response(
                success=False, data=None, error=f"Checksum validation failed: {e}"
            )

    @staticmethod
    def validate_crc32_checksum(
        data: Union[str, bytes], expected_checksum: str
    ) -> Response:
        """Validate data against expected CRC32 checksum.

        Args:
            data: Original data (string or bytes).
            expected_checksum: Expected CRC32 checksum value.

        Returns:
            Response object with validation result.
        """
        try:
            # Convert string to bytes if needed
            if isinstance(data, str):
                byte_data = data.encode("utf-8")
            else:  # isinstance(data, bytes)
                byte_data = data

            calculated_checksum = calculate_checksum32(byte_data)
            is_valid = calculated_checksum == expected_checksum

            return Response(
                success=True,
                data={
                    "input_type": "string" if isinstance(data, str) else "bytes",
                    "input_length": len(byte_data),
                    "calculated_checksum": calculated_checksum,
                    "expected_checksum": expected_checksum,
                    "is_valid": is_valid,
                },
                error=None,
            )
        except Exception as e:
            return Response(
                success=False,
                data=None,
                error=f"CRC32 checksum validation failed: {e}",
            )
