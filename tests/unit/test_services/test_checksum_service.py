"""Unit tests for ChecksumService.

Tests the checksum service business logic layer,
following the architecture pattern for service testing.
"""

import pytest

from xp.models.response import Response
from xp.services.telegram.telegram_checksum_service import TelegramChecksumService


class TestChecksumService:
    """Test class for ChecksumService."""

    def setup_method(self):
        """Set up test instance."""
        self.service = TelegramChecksumService()

    def test_service_initialization(self):
        """Test that service initializes properly."""
        assert isinstance(self.service, TelegramChecksumService)

    def test_calculate_simple_checksum_success(self):
        """Test successful simple checksum calculation."""
        result = self.service.calculate_simple_checksum("test")

        assert isinstance(result, Response)
        assert result.success is True
        assert result.error is None
        assert "input" in result.data
        assert "checksum" in result.data
        assert "algorithm" in result.data

        assert result.data["input"] == "test"
        assert result.data["algorithm"] == "simple_xor"
        assert isinstance(result.data["checksum"], str)
        assert len(result.data["checksum"]) == 2

    def test_calculate_simple_checksum_empty_string(self):
        """Test simple checksum with empty string."""
        result = self.service.calculate_simple_checksum("")

        assert isinstance(result, Response)
        assert result.success is True
        assert result.data["input"] == ""
        assert result.data["checksum"] == "AA"  # XOR of nothing is 0

    def test_calculate_crc32_checksum_string_input(self):
        """Test CRC32 checksum with string input."""
        result = self.service.calculate_crc32_checksum("test")

        assert isinstance(result, Response)
        assert result.success is True
        assert result.error is None

        assert "input_type" in result.data
        assert "input_length" in result.data
        assert "checksum" in result.data
        assert "algorithm" in result.data

        assert result.data["input_type"] == "string"
        assert result.data["input_length"] == 4
        assert result.data["algorithm"] == "crc32"
        assert isinstance(result.data["checksum"], str)
        assert len(result.data["checksum"]) == 8

    def test_calculate_crc32_checksum_bytes_input(self):
        """Test CRC32 checksum with bytes input."""
        test_bytes = b"test"
        result = self.service.calculate_crc32_checksum(test_bytes)

        assert isinstance(result, Response)
        assert result.success is True

        assert result.data["input_type"] == "bytes"
        assert result.data["input_length"] == 4
        assert result.data["algorithm"] == "crc32"

    def test_validate_checksum_valid(self):
        """Test checksum validation with valid checksum."""
        data = "test"
        # First calculate the checksum
        calc_result = self.service.calculate_simple_checksum(data)
        expected_checksum = calc_result.data["checksum"]

        # Then validate it
        result = self.service.validate_checksum(data, expected_checksum)

        assert isinstance(result, Response)
        assert result.success is True
        assert result.error is None

        assert "input" in result.data
        assert "calculated_checksum" in result.data
        assert "expected_checksum" in result.data
        assert "is_valid" in result.data

        assert result.data["input"] == data
        assert result.data["calculated_checksum"] == expected_checksum
        assert result.data["expected_checksum"] == expected_checksum
        assert result.data["is_valid"] is True

    def test_validate_checksum_invalid(self):
        """Test checksum validation with invalid checksum."""
        data = "test"
        wrong_checksum = "XX"

        result = self.service.validate_checksum(data, wrong_checksum)

        assert isinstance(result, Response)
        assert result.success is True
        assert result.data["is_valid"] is False
        assert result.data["expected_checksum"] == wrong_checksum
        assert result.data["calculated_checksum"] != wrong_checksum

    def test_validate_crc32_checksum_valid_string(self):
        """Test CRC32 validation with valid checksum (string input)."""
        data = "test"
        # First calculate the checksum
        calc_result = self.service.calculate_crc32_checksum(data)
        expected_checksum = calc_result.data["checksum"]

        # Then validate it
        result = self.service.validate_crc32_checksum(data, expected_checksum)

        assert isinstance(result, Response)
        assert result.success is True
        assert result.data["input_type"] == "string"
        assert result.data["is_valid"] is True

    def test_validate_crc32_checksum_valid_bytes(self):
        """Test CRC32 validation with valid checksum (bytes input)."""
        data = b"test"
        # First calculate the checksum
        calc_result = self.service.calculate_crc32_checksum(data)
        expected_checksum = calc_result.data["checksum"]

        # Then validate it
        result = self.service.validate_crc32_checksum(data, expected_checksum)

        assert isinstance(result, Response)
        assert result.success is True
        assert result.data["input_type"] == "bytes"
        assert result.data["is_valid"] is True

    def test_validate_crc32_checksum_invalid(self):
        """Test CRC32 validation with invalid checksum."""
        data = "test"
        wrong_checksum = "XXXXXXXX"

        result = self.service.validate_crc32_checksum(data, wrong_checksum)

        assert isinstance(result, Response)
        assert result.success is True
        assert result.data["is_valid"] is False

    def test_response_has_timestamp(self):
        """Test that all responses include timestamp."""
        result = self.service.calculate_simple_checksum("test")

        assert hasattr(result, "timestamp")
        assert result.timestamp is not None

    def test_response_to_dict(self):
        """Test that response can be converted to dict."""
        result_dict = self.service.calculate_simple_checksum("test").to_dict()
        assert isinstance(result_dict, dict)
        assert "success" in result_dict
        assert "data" in result_dict
        assert "error" in result_dict
        assert "timestamp" in result_dict

    @pytest.mark.parametrize(
        "test_input",
        [
            "A",
            "ABC",
            "E14L00I02M",
            "Hello World",
            "",
        ],
    )
    def test_calculate_simple_checksum_various_inputs(self, test_input):
        """Test simple checksum calculation with various inputs."""
        result = self.service.calculate_simple_checksum(test_input)

        assert result.success is True
        assert result.data["input"] == test_input
        assert len(result.data["checksum"]) == 2

    @pytest.mark.parametrize(
        "test_input",
        [
            "test",
            b"test",
            "",
            b"",
            "E14L00I02M",
            b"E14L00I02M",
        ],
    )
    def test_calculate_crc32_checksum_various_inputs(self, test_input):
        """Test CRC32 checksum calculation with various inputs."""
        result = self.service.calculate_crc32_checksum(test_input)

        assert result.success is True
        assert len(result.data["checksum"]) == 8

    def test_consistency_across_calls(self):
        """Test that service provides consistent results across multiple calls."""
        data = "E14L00I02M"

        # Simple checksum consistency
        result1 = self.service.calculate_simple_checksum(data)
        result2 = self.service.calculate_simple_checksum(data)

        assert result1.data["checksum"] == result2.data["checksum"]

        # CRC32 checksum consistency
        crc_result1 = self.service.calculate_crc32_checksum(data)
        crc_result2 = self.service.calculate_crc32_checksum(data)

        assert crc_result1.data["checksum"] == crc_result2.data["checksum"]

    def test_telegram_example_integration(self):
        """Test with actual telegram format example."""
        telegram_data = "E14L00I02M"

        # Calculate both types of checksums
        simple_result = self.service.calculate_simple_checksum(telegram_data)
        crc32_result = self.service.calculate_crc32_checksum(telegram_data)

        assert simple_result.success is True
        assert crc32_result.success is True

        # Validate the calculated checksums
        simple_validation = self.service.validate_checksum(
            telegram_data, simple_result.data["checksum"]
        )
        crc32_validation = self.service.validate_crc32_checksum(
            telegram_data, crc32_result.data["checksum"]
        )

        assert simple_validation.success is True
        assert simple_validation.data["is_valid"] is True
        assert crc32_validation.success is True
        assert crc32_validation.data["is_valid"] is True

    def test_telegram_crash1(self):
        """Test with actual telegram format example."""
        telegram_data = (
            "R0012345005F02D1700:00000[NA],01:00000[NA],02:00000[NA],03:00000[NA]"
        )
        # <R0012345005F02D1700:00000[NA],01:00000[NA],02:00000[NA],03:00000[NA]HA>

        # Calculate both types of checksums
        simple_result = self.service.calculate_simple_checksum(telegram_data)

        assert simple_result.success is True

        # Validate the calculated checksums
        simple_validation = self.service.validate_checksum(
            telegram_data, simple_result.data["checksum"]
        )

        assert simple_validation.success is True
        assert simple_validation.data["is_valid"] is True
        assert simple_result.data["checksum"] == "HM"
