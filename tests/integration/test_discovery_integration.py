"""Integration tests for device discover functionality."""

import pytest

from xp.models.telegram.system_function import SystemFunction
from xp.models.telegram.system_telegram import SystemTelegram
from xp.services.telegram.telegram_discover_service import (
    TelegramDiscoverService,
)
from xp.services.telegram.telegram_service import TelegramParsingError, TelegramService


class TestDiscoverIntegration:
    """Integration test cases for discover operations."""

    def test_complete_discover_workflow(self):
        """Test complete workflow: generate -> parse -> analyze."""
        discover_service = TelegramDiscoverService()
        telegram_service = TelegramService()

        # Generate discover telegram
        discover_telegram = discover_service.generate_discover_telegram()
        assert discover_telegram == "<S0000000000F01D00FA>"

        # Parse the generated telegram
        parsed_system = telegram_service.parse_system_telegram(discover_telegram)

        assert isinstance(parsed_system, SystemTelegram)
        assert parsed_system.serial_number == "0000000000"
        assert parsed_system.system_function == SystemFunction.DISCOVERY
        assert parsed_system.datapoint_type is None
        assert parsed_system.checksum == "FA"
        assert parsed_system.checksum_validated is True

    def test_discover_telegram_object_creation_and_parsing_consistency(self):
        """Test that created telegram objects match parsed ones."""
        discover_service = TelegramDiscoverService()
        telegram_service = TelegramService()

        # Create telegram object
        created_telegram = discover_service.create_discover_telegram_object()

        # Parse the raw telegram from the created object
        parsed_telegram = telegram_service.parse_system_telegram(
            created_telegram.raw_telegram
        )

        # They should match
        assert created_telegram.serial_number == parsed_telegram.serial_number
        assert created_telegram.system_function == parsed_telegram.system_function
        assert created_telegram.datapoint_type is None
        assert created_telegram.checksum == parsed_telegram.checksum
        assert created_telegram.raw_telegram == parsed_telegram.raw_telegram

    def test_checksum_validation_integration(self):
        """Test that checksum validation works for discover telegrams."""
        discover_service = TelegramDiscoverService()
        telegram_service = TelegramService()

        # Test discover request
        discover_telegram = discover_service.generate_discover_telegram()
        parsed_request = telegram_service.parse_system_telegram(discover_telegram)

        # Checksum should be valid
        assert parsed_request.checksum_validated is True

        # Verify checksum manually
        is_valid = telegram_service.validate_checksum(parsed_request)
        assert is_valid is True

        # Test discover responses
        test_responses = [
            "<R0012345011F01DFA>",
            "<R0012345006F01DFG>",
            "<R0012345003F01DFD>",
            "<R0012345003F18DFL>",
        ]

        for response_str in test_responses:
            parsed_response = telegram_service.parse_reply_telegram(response_str)

            # Checksum should be valid
            assert parsed_response.checksum_validated is True

            # Verify checksum manually
            is_valid = telegram_service.validate_checksum(parsed_response)
            assert is_valid is True

    def test_error_handling_integration(self):
        """Test error handling across services."""
        discover_service = TelegramDiscoverService()
        telegram_service = TelegramService()

        # Test parsing invalid telegram
        with pytest.raises(TelegramParsingError):
            telegram_service.parse_reply_telegram("<INVALID>")

        # Test that error doesn't occur for valid input
        valid_telegram = discover_service.generate_discover_telegram()
        parsed = telegram_service.parse_system_telegram(valid_telegram)
        assert parsed is not None

    def test_discover_response_format_validation_integration(self):
        """Test discover response format validation with real telegrams."""
        telegram_service = TelegramService()
        discover_service = TelegramDiscoverService()

        # Valid discover responses
        valid_responses = [
            "<R0012345011F01DFA>",
            "<R0012345006F01DFG>",
            "<R0012345003F01DFD>",
        ]

        for response in valid_responses:
            # Should validate format correctly
            assert discover_service.validate_discover_response_format(response) is True

            # Should parse correctly
            parsed = telegram_service.parse_reply_telegram(response)
            assert parsed.system_function == SystemFunction.DISCOVERY

            # Should be identified as discover response
            assert discover_service.is_discover_response(parsed) is True

        # Invalid formats
        invalid_responses = [
            "<R0012345011F02DFM>",  # Wrong function
            "<R002003083F01DFM>",  # Wrong serial length
            "<S0012345011F01DFM>",  # System telegram, not reply
        ]

        for response in invalid_responses:
            assert discover_service.validate_discover_response_format(response) is False
