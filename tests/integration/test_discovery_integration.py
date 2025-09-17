"""Integration tests for device discovery functionality"""

import pytest
from src.xp.services.discovery_service import (
    DiscoveryService,
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
        discovery_service = DiscoveryService()
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
        discovery_service = DiscoveryService()
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

    def test_parse_specification_examples(self):
        """Test parsing the examples from the specification"""
        telegram_service = TelegramService()
        discovery_service = DiscoveryService()

        # Test discovery request
        discovery_request = "<S0000000000F01D00FA>"
        parsed_request = telegram_service.parse_system_telegram(discovery_request)

        assert parsed_request.system_function == SystemFunction.DISCOVERY
        assert parsed_request.serial_number == "0000000000"
        assert parsed_request.checksum_validated is True

        # Test discovery responses from the specification
        test_responses = [
            "<R0020030837F01DFM>",
            "<R0020044966F01DFK>",
            "<R0020042796F01DFN>",
        ]

        devices = []
        for response_str in test_responses:
            parsed_response = telegram_service.parse_reply_telegram(response_str)

            # Verify it's properly parsed
            assert isinstance(parsed_response, ReplyTelegram)
            assert parsed_response.system_function == SystemFunction.DISCOVERY
            assert parsed_response.checksum_validated is True

            # Verify it's identified as discovery response
            assert discovery_service.is_discovery_response(parsed_response) is True

            # Extract device info
            device_info = discovery_service.parse_discovery_response(parsed_response)
            assert device_info is not None
            devices.append(device_info)

        # Verify devices
        assert len(devices) == 3
        serials = [device.serial_number for device in devices]
        assert "0020030837" in serials
        assert "0020044966" in serials
        assert "0020042796" in serials

    def test_checksum_validation_integration(self):
        """Test that checksum validation works for discovery telegrams"""
        discovery_service = DiscoveryService()
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
        discovery_service = DiscoveryService()
        telegram_service = TelegramService()

        # Test parsing invalid telegram
        with pytest.raises(TelegramParsingError):
            telegram_service.parse_reply_telegram("<INVALID>")

        # Test that error doesn't occur for valid input
        valid_telegram = discovery_service.generate_discovery_telegram()
        parsed = telegram_service.parse_system_telegram(valid_telegram)
        assert parsed is not None

    def test_multiple_response_parsing_integration(self):
        """Test parsing multiple discovery responses"""
        telegram_service = TelegramService()
        discovery_service = DiscoveryService()

        # Mix of discovery and non-discovery responses
        test_telegrams = [
            "<R0020030837F01DFM>",  # Discovery response
            "<R0020044966F02D18+26,0§CIL>",  # Temperature response
            "<R0020042796F01DFN>",  # Discovery response
            "<R0020044991F01DFC>",  # Discovery response
        ]

        all_replies = []
        for telegram_str in test_telegrams:
            parsed = telegram_service.parse_reply_telegram(telegram_str)
            all_replies.append(parsed)

        # Extract discovery responses
        devices = discovery_service.parse_multiple_discovery_responses(all_replies)

        assert len(devices) == 3  # Only discovery responses

        serials = [device.serial_number for device in devices]
        assert "0020030837" in serials
        assert "0020042796" in serials
        assert "0020044991" in serials
        assert "0020044966" not in serials  # This was not a discovery response

    def test_discovery_summary_integration(self):
        """Test discovery summary generation with real parsing"""
        telegram_service = TelegramService()
        discovery_service = DiscoveryService()

        # Parse multiple responses including duplicates
        test_responses = [
            "<R0020030837F01DFM>",
            "<R0020044966F01DFK>",
            "<R0020030837F01DFM>",  # Duplicate
            "<R0020042796F01DFN>",
            "<R0021044966F01DFL>",  # Different prefix
        ]

        devices = []
        for response_str in test_responses:
            parsed_response = telegram_service.parse_reply_telegram(response_str)
            device_info = discovery_service.parse_discovery_response(parsed_response)
            if device_info:
                devices.append(device_info)

        summary = discovery_service.generate_discovery_summary(devices)

        assert summary["total_responses"] == 5
        assert summary["unique_devices"] == 4
        assert summary["valid_checksums"] == 4  # All should have valid checksums
        assert summary["duplicate_responses"] == 1
        assert summary["success_rate"] == 100.0

        # Check serial prefixes
        assert summary["serial_prefixes"]["0020"] == 3
        assert summary["serial_prefixes"]["0021"] == 1

    def test_discovery_format_integration(self):
        """Test discovery result formatting with real data"""
        telegram_service = TelegramService()
        discovery_service = DiscoveryService()

        test_responses = [
            "<R0020030837F01DFM>",
            "<R0020044966F01DFK>",
            "<R0020042796F01DFN>",
        ]

        devices = []
        for response_str in test_responses:
            parsed_response = telegram_service.parse_reply_telegram(response_str)
            device_info = discovery_service.parse_discovery_response(parsed_response)
            if device_info:
                devices.append(device_info)

        formatted_results = discovery_service.format_discovery_results(devices)

        assert "=== Device Discovery Results ===" in formatted_results
        assert "Total Responses: 3" in formatted_results
        assert "Valid Checksums: 3/3 (100.0%)" in formatted_results
        assert "✓ 0020030837" in formatted_results
        assert "✓ 0020044966" in formatted_results
        assert "✓ 0020042796" in formatted_results
        assert "0020xxxx: 3 device(s)" in formatted_results

    def test_discovery_response_format_validation_integration(self):
        """Test discovery response format validation with real telegrams"""
        telegram_service = TelegramService()
        discovery_service = DiscoveryService()

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

    def test_end_to_end_discovery_session(self):
        """Test complete end-to-end discovery session"""
        telegram_service = TelegramService()
        discovery_service = DiscoveryService()

        # 1. Generate discovery broadcast
        discovery_request = discovery_service.generate_discovery_telegram()
        assert discovery_request == "<S0000000000F01D00FA>"

        # 2. Parse discovery request
        parsed_request = telegram_service.parse_system_telegram(discovery_request)
        assert parsed_request.system_function == SystemFunction.DISCOVERY

        # 3. Simulate device responses (from specification log file)
        device_responses = [
            "<R0020030837F01DFM>",
            "<R0020044966F01DFK>",
            "<R0020042796F01DFN>",
            "<R0020044991F01DFC>",
            "<R0020044964F01DFI>",
            "<R0020044986F01DFE>",
            "<R0020037487F01DFM>",
            "<R0020044989F01DFL>",
            "<R0020044974F01DFJ>",
            "<R0020041824F01DFI>",
        ]

        # 4. Parse all responses
        devices = []
        for response_str in device_responses:
            parsed_response = telegram_service.parse_reply_telegram(response_str)
            device_info = discovery_service.parse_discovery_response(parsed_response)
            if device_info:
                devices.append(device_info)

        # 5. Analyze results
        assert len(devices) == 10

        # All should have valid checksums
        valid_devices = [d for d in devices if d.checksum_valid]
        assert len(valid_devices) == 10

        # Check unique serial numbers
        serials = {device.serial_number for device in devices}
        assert len(serials) == 10

        # Generate summary
        summary = discovery_service.generate_discovery_summary(devices)
        assert summary["success_rate"] == 100.0
        assert summary["unique_devices"] == 10
        assert len(summary["device_list"]) == 10

        # Format results
        formatted = discovery_service.format_discovery_results(devices)
        assert "10" in formatted  # Should mention 10 devices
        assert "100.0%" in formatted  # Should show 100% success rate
