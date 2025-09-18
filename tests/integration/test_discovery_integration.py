"""Integration tests for device discovery functionality"""

import pytest
from src.xp.services.telegram_discovery_service import (
    TelegramDiscoveryService,
)
from src.xp.services.telegram_service import TelegramService, TelegramParsingError
from src.xp.models.system_telegram import SystemTelegram
from src.xp.models.datapoint_type import DataPointType
from src.xp.models.system_function import SystemFunction
from src.xp.models.reply_telegram import ReplyTelegram


class TestDiscoveryIntegration:
    """Integration test cases for discovery operations"""

    def test_complete_discovery_workflow(self):
        """Test complete workflow: generate -> parse -> analyze"""
        discovery_service = TelegramDiscoveryService()
        telegram_service = TelegramService()

        # Generate discovery telegram
        discovery_telegram = discovery_service.generate_discovery_telegram()
        assert discovery_telegram == "<S0000000000F01D00FA>"

        # Parse the generated telegram
        parsed_system = telegram_service.parse_system_telegram(discovery_telegram)

        assert isinstance(parsed_system, SystemTelegram)
        assert parsed_system.serial_number == "0000000000"
        assert parsed_system.system_function == SystemFunction.DISCOVERY
        assert parsed_system.data_point_id == DataPointType.NONE
        assert parsed_system.checksum == "FA"
        assert parsed_system.checksum_validated is True

    def test_discovery_telegram_object_creation_and_parsing_consistency(self):
        """Test that created telegram objects match parsed ones"""
        discovery_service = TelegramDiscoveryService()
        telegram_service = TelegramService()

        # Create telegram object
        created_telegram = discovery_service.create_discovery_telegram_object()

        # Parse the raw telegram from the created object
        parsed_telegram = telegram_service.parse_system_telegram(
            created_telegram.raw_telegram
        )

        # They should match
        assert created_telegram.serial_number == parsed_telegram.serial_number
        assert created_telegram.system_function == parsed_telegram.system_function
        assert created_telegram.data_point_id == parsed_telegram.data_point_id
        assert created_telegram.checksum == parsed_telegram.checksum
        assert created_telegram.raw_telegram == parsed_telegram.raw_telegram

    def test_checksum_validation_integration(self):
        """Test that checksum validation works for discovery telegrams"""
        discovery_service = TelegramDiscoveryService()
        telegram_service = TelegramService()

        # Test discovery request
        discovery_telegram = discovery_service.generate_discovery_telegram()
        parsed_request = telegram_service.parse_system_telegram(discovery_telegram)

        # Checksum should be valid
        assert parsed_request.checksum_validated is True

        # Verify checksum manually
        is_valid = telegram_service.validate_checksum(parsed_request)
        assert is_valid is True

        # Test discovery responses
        test_responses = [
            "<R0020030837F01DFM>",
            "<R0020044966F01DFK>",
            "<R0020042796F01DFN>",
        ]

        for response_str in test_responses:
            parsed_response = telegram_service.parse_reply_telegram(response_str)

            # Checksum should be valid
            assert parsed_response.checksum_validated is True

            # Verify checksum manually
            is_valid = telegram_service.validate_checksum(parsed_response)
            assert is_valid is True

    def test_error_handling_integration(self):
        """Test error handling across services"""
        discovery_service = TelegramDiscoveryService()
        telegram_service = TelegramService()

        # Test parsing invalid telegram
        with pytest.raises(TelegramParsingError):
            telegram_service.parse_reply_telegram("<INVALID>")

        # Test that error doesn't occur for valid input
        valid_telegram = discovery_service.generate_discovery_telegram()
        parsed = telegram_service.parse_system_telegram(valid_telegram)
        assert parsed is not None

    def test_discovery_response_format_validation_integration(self):
        """Test discovery response format validation with real telegrams"""
        telegram_service = TelegramService()
        discovery_service = TelegramDiscoveryService()

        # Valid discovery responses
        valid_responses = [
            "<R0020030837F01DFM>",
            "<R0020044966F01DFK>",
            "<R0020042796F01DFN>",
        ]

        for response in valid_responses:
            # Should validate format correctly
            assert (
                discovery_service.validate_discovery_response_format(response) is True
            )

            # Should parse correctly
            parsed = telegram_service.parse_reply_telegram(response)
            assert parsed.system_function == SystemFunction.DISCOVERY

            # Should be identified as discovery response
            assert discovery_service.is_discovery_response(parsed) is True

        # Invalid formats
        invalid_responses = [
            "<R0020030837F02DFM>",  # Wrong function
            "<R002003083F01DFM>",  # Wrong serial length
            "<S0020030837F01DFM>",  # System telegram, not reply
        ]

        for response in invalid_responses:
            assert (
                discovery_service.validate_discovery_response_format(response) is False
            )

