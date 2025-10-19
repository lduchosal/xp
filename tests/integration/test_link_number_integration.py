"""Integration tests for link number functionality."""

import pytest

from xp.models.telegram.datapoint_type import DataPointType
from xp.models.telegram.reply_telegram import ReplyTelegram
from xp.models.telegram.system_function import SystemFunction
from xp.models.telegram.system_telegram import SystemTelegram
from xp.services.telegram.telegram_link_number_service import (
    LinkNumberError,
    LinkNumberService,
)
from xp.services.telegram.telegram_service import TelegramParsingError, TelegramService


class TestLinkNumberIntegration:
    """Integration test cases for link number operations."""

    def test_complete_set_link_number_workflow(self):
        """Test complete workflow: generate -> parse -> validate."""
        link_service = LinkNumberService()
        telegram_service = TelegramService()

        # Generate set link number telegram
        serial = "0012345005"
        link_num = 25

        generated_telegram = link_service.generate_set_link_number_telegram(
            serial, link_num
        )
        assert generated_telegram == "<S0012345005F04D0425FC>"

        # Parse the generated telegram
        parsed_telegram = telegram_service.parse_system_telegram(generated_telegram)

        assert isinstance(parsed_telegram, SystemTelegram)
        assert parsed_telegram.serial_number == serial
        assert parsed_telegram.system_function == SystemFunction.WRITE_CONFIG
        assert parsed_telegram.datapoint_type is None
        assert parsed_telegram.checksum == "FC"
        assert parsed_telegram.checksum_validated is True  # Should auto-validate

    def test_complete_read_link_number_workflow(self):
        """Test complete workflow for reading link number."""
        link_service = LinkNumberService()
        telegram_service = TelegramService()

        serial = "0012345005"

        # Generate read link number telegram
        generated_telegram = link_service.generate_read_link_number_telegram(serial)

        # Parse the generated telegram
        parsed_telegram = telegram_service.parse_system_telegram(generated_telegram)

        assert isinstance(parsed_telegram, SystemTelegram)
        assert parsed_telegram.serial_number == serial
        assert parsed_telegram.system_function == SystemFunction.READ_CONFIG
        assert parsed_telegram.datapoint_type is None
        assert parsed_telegram.checksum_validated is True

    def test_parse_specification_examples(self):
        """Test parsing the examples from the specification."""
        telegram_service = TelegramService()
        link_service = LinkNumberService()

        # Test telegrams from the specification
        test_cases = [
            "<S0012345005F04D0409FA>",
            "<R0012345005F18DFN>" "<R0012345005F19DFM>",
            "<S0012345005F04D0425FC>",
            "<R0012345005F18DFN>" "<R0012345005F19DFM>",
        ]

        for telegram_str in test_cases:
            parsed = telegram_service.parse_telegram(telegram_str)

            # Verify checksum validation
            assert parsed.checksum_validated is not None

            if telegram_str.startswith("<S"):  # System telegram
                assert isinstance(parsed, SystemTelegram)
                assert parsed.serial_number == "0012345005"
                assert parsed.system_function == SystemFunction.WRITE_CONFIG
                assert parsed.datapoint_type is None

            elif telegram_str.startswith("<R"):  # Reply telegram
                assert isinstance(parsed, ReplyTelegram)
                assert parsed.serial_number == "0012345005"

                # Check if it's ACK or NAK
                if "F18D" in telegram_str:  # ACK
                    assert link_service.is_ack_response(parsed) is True
                    assert link_service.is_nak_response(parsed) is False
                elif "F19D" in telegram_str:  # NAK
                    assert link_service.is_nak_response(parsed) is True
                    assert link_service.is_ack_response(parsed) is False

    def test_telegram_object_creation_and_parsing_consistency(self):
        """Test that created telegram objects match parsed ones."""
        link_service = LinkNumberService()
        telegram_service = TelegramService()

        # Create telegram object
        created_telegram = link_service.create_set_link_number_telegram_object(
            "0012345005", 25
        )

        # Parse the raw telegram from the created object
        parsed_telegram = telegram_service.parse_system_telegram(
            created_telegram.raw_telegram
        )

        # They should match
        assert created_telegram.serial_number == parsed_telegram.serial_number
        assert created_telegram.system_function == parsed_telegram.system_function
        assert created_telegram.datapoint_type == DataPointType.LINK_NUMBER
        assert created_telegram.checksum == parsed_telegram.checksum
        assert created_telegram.raw_telegram == parsed_telegram.raw_telegram

    def test_checksum_validation_integration(self):
        """Test that checksum validation works for generated telegrams."""
        link_service = LinkNumberService()
        telegram_service = TelegramService()

        # Test multiple link numbers
        test_link_numbers = [0, 1, 9, 10, 25, 50, 99]

        for link_num in test_link_numbers:
            # Generate telegram
            telegram_str = link_service.generate_set_link_number_telegram(
                "1234567890", link_num
            )

            # Parse telegram
            parsed = telegram_service.parse_system_telegram(telegram_str)

            # Checksum should be valid
            assert (
                parsed.checksum_validated is True
            ), f"Checksum failed for link number {link_num}"

            # Verify checksum manually
            is_valid = telegram_service.validate_checksum(parsed)
            assert (
                is_valid is True
            ), f"Manual checksum validation failed for link number {link_num}"

    def test_error_handling_integration(self):
        """Test error handling across services."""
        link_service = LinkNumberService()
        telegram_service = TelegramService()

        # Test invalid telegram generation
        with pytest.raises(LinkNumberError):
            link_service.generate_set_link_number_telegram("invalid", 25)

        # Test parsing invalid telegram
        with pytest.raises(TelegramParsingError):
            telegram_service.parse_system_telegram("<INVALID>")

        # Test that error doesn't occur for valid input
        valid_telegram = link_service.generate_set_link_number_telegram(
            "0012345005", 25
        )
        parsed = telegram_service.parse_system_telegram(valid_telegram)
        assert parsed is not None

    def test_end_to_end_workflow_with_replies(self):
        """Test complete end-to-end workflow including reply handling."""
        link_service = LinkNumberService()
        telegram_service = TelegramService()

        # Generate set command
        set_command = link_service.generate_set_link_number_telegram("0012345005", 25)
        assert set_command == "<S0012345005F04D0425FC>"

        # Parse ACK reply from specification
        ack_reply_str = "<R0012345005F18DFN>"
        ack_reply = telegram_service.parse_reply_telegram(ack_reply_str)

        # Verify it's properly identified as ACK
        assert link_service.is_ack_response(ack_reply) is True
        assert link_service.is_nak_response(ack_reply) is False

        # Parse NAK reply from specification
        nak_reply_str = "<R0012345005F19DFM>"
        nak_reply = telegram_service.parse_reply_telegram(nak_reply_str)

        # Verify it's properly identified as NAK
        assert link_service.is_nak_response(nak_reply) is True
        assert link_service.is_ack_response(nak_reply) is False

        # Both should have valid checksums
        assert ack_reply.checksum_validated is True
        assert nak_reply.checksum_validated is True

    def test_boundary_values_integration(self):
        """Test boundary values across the entire system."""
        link_service = LinkNumberService()
        telegram_service = TelegramService()

        # Test boundary link numbers
        boundary_cases = [
            ("0000000000", 0),  # Minimum serial and link number
            ("9999999999", 99),  # Maximum serial and link number
            ("0012345005", 0),  # From spec with min link number
            ("0012345005", 99),  # From spec with max link number
        ]

        for serial, link_num in boundary_cases:
            # Generate and parse
            telegram_str = link_service.generate_set_link_number_telegram(
                serial, link_num
            )
            parsed = telegram_service.parse_system_telegram(telegram_str)

            # Verify all properties
            assert parsed.serial_number == serial
            assert parsed.system_function == SystemFunction.WRITE_CONFIG
            assert parsed.datapoint_type is None
            assert parsed.checksum_validated is True

            # Verify telegram format
            expected_link_str = f"{link_num:02d}"
            assert expected_link_str in telegram_str
