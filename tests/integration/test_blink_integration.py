"""Integration tests for blink functionality."""

import pytest

from xp.models.telegram.reply_telegram import ReplyTelegram
from xp.models.telegram.system_function import SystemFunction
from xp.models.telegram.system_telegram import SystemTelegram
from xp.services.telegram.telegram_blink_service import BlinkError, TelegramBlinkService
from xp.services.telegram.telegram_service import TelegramParsingError, TelegramService


class TestBlinkIntegration:
    """Integration test cases for blink operations."""

    def test_complete_blink_workflow(self):
        """Test complete workflow: generate blink -> parse -> validate."""
        blink_service = TelegramBlinkService()
        telegram_service = TelegramService()

        # Generate blink telegram
        serial = "0012345008"

        generated_telegram = blink_service.generate_blink_telegram(serial, "on")
        assert generated_telegram == "<S0012345008F05D00FN>"

        # Parse the generated telegram
        parsed_telegram = telegram_service.parse_system_telegram(generated_telegram)

        assert isinstance(parsed_telegram, SystemTelegram)
        assert parsed_telegram.serial_number == serial
        assert parsed_telegram.system_function == SystemFunction.BLINK
        assert parsed_telegram.datapoint_type is None
        assert parsed_telegram.checksum == "FN"
        assert parsed_telegram.checksum_validated is True  # Should auto-validate

    def test_complete_unblink_workflow(self):
        """Test complete workflow: generate unblink -> parse -> validate."""
        blink_service = TelegramBlinkService()
        telegram_service = TelegramService()

        # Generate unblink telegram
        serial = "0012345011"

        generated_telegram = blink_service.generate_blink_telegram(serial, "off")
        assert generated_telegram == "<S0012345011F06D00FG>"

        # Parse the generated telegram
        parsed_telegram = telegram_service.parse_system_telegram(generated_telegram)

        assert isinstance(parsed_telegram, SystemTelegram)
        assert parsed_telegram.serial_number == serial
        assert parsed_telegram.system_function == SystemFunction.UNBLINK
        assert parsed_telegram.datapoint_type is None
        assert parsed_telegram.checksum == "FG"
        assert parsed_telegram.checksum_validated is True

    def test_parse_specification_examples(self):
        """Test parsing the examples from the specification."""
        telegram_service = TelegramService()
        blink_service = TelegramBlinkService()

        # Test telegrams from the specification
        test_cases = [
            # Blink command and ACK response
            ("<S0012345008F05D00FN>", SystemFunction.BLINK),
            ("<R0012345008F18DFA>", SystemFunction.ACK),
            # Unblink command and ACK response
            ("<S0012345011F06D00FG>", SystemFunction.UNBLINK),
            ("<R0012345011F18DFI>", SystemFunction.ACK),
        ]

        for telegram_str, expected_function in test_cases:
            parsed = telegram_service.parse_telegram(telegram_str)

            # Verify checksum validation
            assert parsed.checksum_validated is not None

            if telegram_str.startswith("<S"):  # System telegram
                assert isinstance(parsed, SystemTelegram)
                assert parsed.datapoint_type is None
                assert parsed.system_function == expected_function
                if expected_function == SystemFunction.BLINK:
                    assert parsed.serial_number == "0012345008"
                elif expected_function == SystemFunction.UNBLINK:
                    assert parsed.serial_number == "0012345011"

            elif telegram_str.startswith("<R"):  # Reply telegram
                assert isinstance(parsed, ReplyTelegram)
                assert parsed.system_function == expected_function

                # Check if it's ACK response
                if expected_function == SystemFunction.ACK:
                    assert blink_service.is_ack_response(parsed) is True
                    assert blink_service.is_nak_response(parsed) is False

    def test_telegram_object_creation_and_parsing_consistency(self):
        """Test that created telegram objects match parsed ones."""
        blink_service = TelegramBlinkService()
        telegram_service = TelegramService()

        # Test blink telegram object
        created_blink_telegram = blink_service.create_blink_telegram_object(
            "0012345008"
        )
        parsed_blink_telegram = telegram_service.parse_system_telegram(
            created_blink_telegram.raw_telegram
        )

        # They should match
        assert (
            created_blink_telegram.serial_number == parsed_blink_telegram.serial_number
        )
        assert (
            created_blink_telegram.system_function
            == parsed_blink_telegram.system_function
        )
        assert created_blink_telegram.datapoint_type is None
        assert created_blink_telegram.checksum == parsed_blink_telegram.checksum
        assert created_blink_telegram.raw_telegram == parsed_blink_telegram.raw_telegram

        # Test unblink telegram object
        created_unblink_telegram = blink_service.create_unblink_telegram_object(
            "0012345011"
        )
        parsed_unblink_telegram = telegram_service.parse_system_telegram(
            created_unblink_telegram.raw_telegram
        )

        # They should match
        assert (
            created_unblink_telegram.serial_number
            == parsed_unblink_telegram.serial_number
        )
        assert (
            created_unblink_telegram.system_function
            == parsed_unblink_telegram.system_function
        )
        assert created_unblink_telegram.datapoint_type is None
        assert created_unblink_telegram.checksum == parsed_unblink_telegram.checksum
        assert (
            created_unblink_telegram.raw_telegram
            == parsed_unblink_telegram.raw_telegram
        )

    def test_checksum_validation_integration(self):
        """Test that checksum validation works for generated telegrams."""
        blink_service = TelegramBlinkService()
        telegram_service = TelegramService()

        # Test multiple serial numbers
        test_serials = [
            "0012345008",
            "0012345011",
            "1234567890",
            "0000000000",
            "9999999999",
        ]

        for serial in test_serials:
            # Test blink telegram
            blink_telegram_str = blink_service.generate_blink_telegram(serial, "on")
            parsed_blink = telegram_service.parse_system_telegram(blink_telegram_str)

            assert (
                parsed_blink.checksum_validated is True
            ), f"Blink checksum failed for serial {serial}"
            is_valid_blink = telegram_service.validate_checksum(parsed_blink)
            assert (
                is_valid_blink is True
            ), f"Manual blink checksum validation failed for serial {serial}"

            # Test unblink telegram
            unblink_telegram_str = blink_service.generate_blink_telegram(serial, "off")
            parsed_unblink = telegram_service.parse_system_telegram(
                unblink_telegram_str
            )

            assert (
                parsed_unblink.checksum_validated is True
            ), f"Unblink checksum failed for serial {serial}"
            is_valid_unblink = telegram_service.validate_checksum(parsed_unblink)
            assert (
                is_valid_unblink is True
            ), f"Manual unblink checksum validation failed for serial {serial}"

    def test_error_handling_integration(self):
        """Test error handling across services."""
        blink_service = TelegramBlinkService()
        telegram_service = TelegramService()

        # Test invalid telegram generation
        with pytest.raises(BlinkError):
            blink_service.generate_blink_telegram("invalid", "on")

        with pytest.raises(BlinkError):
            blink_service.generate_blink_telegram("invalid", "off")

        # Test parsing invalid telegram
        with pytest.raises(TelegramParsingError):
            telegram_service.parse_system_telegram("<INVALID>")

        # Test that error doesn't occur for valid input
        valid_blink_telegram = blink_service.generate_blink_telegram("0012345008", "on")
        parsed_blink = telegram_service.parse_system_telegram(valid_blink_telegram)
        assert parsed_blink is not None

        valid_unblink_telegram = blink_service.generate_blink_telegram(
            "0012345011", "off"
        )
        parsed_unblink = telegram_service.parse_system_telegram(valid_unblink_telegram)
        assert parsed_unblink is not None

    def test_end_to_end_workflow_with_replies(self):
        """Test complete end-to-end workflow including reply handling."""
        blink_service = TelegramBlinkService()
        telegram_service = TelegramService()

        # Generate blink command
        blink_command = blink_service.generate_blink_telegram("0012345008", "on")
        assert blink_command == "<S0012345008F05D00FN>"

        # Parse ACK reply from specification
        ack_reply_str = "<R0012345008F18DFA>"
        ack_reply = telegram_service.parse_reply_telegram(ack_reply_str)

        # Verify it's properly identified as ACK
        assert blink_service.is_ack_response(ack_reply) is True
        assert blink_service.is_nak_response(ack_reply) is False

        # Generate unblink command
        unblink_command = blink_service.generate_blink_telegram("0012345011", "off")
        assert unblink_command == "<S0012345011F06D00FG>"

        # Parse ACK reply from specification
        unblink_ack_reply_str = "<R0012345011F18DFI>"
        unblink_ack_reply = telegram_service.parse_reply_telegram(unblink_ack_reply_str)

        # Verify it's properly identified as ACK
        assert blink_service.is_ack_response(unblink_ack_reply) is True
        assert blink_service.is_nak_response(unblink_ack_reply) is False

        # Both should have valid checksums
        assert ack_reply.checksum_validated is True
        assert unblink_ack_reply.checksum_validated is True

    def test_boundary_values_integration(self):
        """Test boundary values across the entire system."""
        blink_service = TelegramBlinkService()
        telegram_service = TelegramService()

        # Test boundary serial numbers
        boundary_serials = [
            "0000000000",  # Minimum serial
            "9999999999",  # Maximum serial
            "0012345008",  # From spec (blink)
            "0012345011",  # From spec (unblink)
        ]

        for serial in boundary_serials:
            # Test blink
            blink_telegram_str = blink_service.generate_blink_telegram(serial, "on")
            parsed_blink = telegram_service.parse_system_telegram(blink_telegram_str)

            # Verify all properties
            assert parsed_blink.serial_number == serial
            assert parsed_blink.system_function == SystemFunction.BLINK
            assert parsed_blink.datapoint_type is None
            assert parsed_blink.checksum_validated is True

            # Verify telegram format
            assert f"S{serial}F05D00" in blink_telegram_str

            # Test unblink
            unblink_telegram_str = blink_service.generate_blink_telegram(serial, "off")
            parsed_unblink = telegram_service.parse_system_telegram(
                unblink_telegram_str
            )

            # Verify all properties
            assert parsed_unblink.serial_number == serial
            assert parsed_unblink.system_function == SystemFunction.UNBLINK
            assert parsed_unblink.datapoint_type is None
            assert parsed_unblink.checksum_validated is True

            # Verify telegram format
            assert f"S{serial}F06D00" in unblink_telegram_str

    def test_blink_unblink_command_distinction(self):
        """Test that blink and unblink commands are correctly distinguished."""
        blink_service = TelegramBlinkService()
        telegram_service = TelegramService()

        serial = "1234567890"

        # Generate both commands
        blink_telegram = blink_service.generate_blink_telegram(serial, "on")
        unblink_telegram = blink_service.generate_blink_telegram(serial, "off")

        # Parse both commands
        parsed_blink = telegram_service.parse_system_telegram(blink_telegram)
        parsed_unblink = telegram_service.parse_system_telegram(unblink_telegram)

        # They should be different functions
        assert parsed_blink.system_function == SystemFunction.BLINK
        assert parsed_unblink.system_function == SystemFunction.UNBLINK

        # Both should use STATUS data point
        assert parsed_blink.datapoint_type is None
        assert parsed_unblink.datapoint_type is None

        # Both should have same serial but different checksums
        assert parsed_blink.serial_number == parsed_unblink.serial_number == serial
        assert parsed_blink.checksum != parsed_unblink.checksum
