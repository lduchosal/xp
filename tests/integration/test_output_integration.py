"""Integration tests for XP24 action functionality."""

import pytest

from xp.models.telegram.action_type import ActionType
from xp.services.telegram.telegram_output_service import (
    TelegramOutputService,
    XPOutputError,
)
from xp.services.telegram.telegram_service import TelegramService


class TestOutputIntegration:
    """Integration tests for XP24 action functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        telegram_service = TelegramService()
        self.output_service = TelegramOutputService(telegram_service=telegram_service)

    def test_end_to_end_action_generation_and_parsing(self):
        """Test complete flow: generate telegram, parse it back."""
        # Generate action telegram
        original_telegram = self.output_service.generate_system_action_telegram(
            "0012345008", 2, ActionType.ON_RELEASE
        )

        # Parse the generated telegram
        parsed = self.output_service.parse_system_telegram(original_telegram)

        # Verify parsed data matches original
        assert parsed.serial_number == "0012345008"
        assert parsed.output_number == 2
        assert parsed.action_type == ActionType.ON_RELEASE
        assert parsed.raw_telegram == original_telegram
        assert parsed.checksum_validated is True

    def test_end_to_end_status_generation_and_parsing(self):
        """Test complete flow: generate status query, parse response."""
        # Generate status query telegram
        status_telegram = self.output_service.generate_system_status_telegram(
            "0012345008"
        )

        # Verify generated format
        assert "<S0012345008F02D12" in status_telegram
        assert ">" in status_telegram
        assert len(status_telegram) == 21  # <S0012345008F02D12XX>

        # Simulate status response and parse
        mock_response = "<R0012345008F02D12xxxx1010FJ>"
        status = self.output_service.parse_status_response(mock_response)

        expected = [False, True, False, True]
        assert status == expected

    def test_all_output_combinations(self):
        """Test telegram generation and parsing for all output combinations."""
        for output_number in range(4):
            for action in (ActionType.OFF_PRESS, ActionType.ON_RELEASE):
                # Generate telegram
                telegram = self.output_service.generate_system_action_telegram(
                    "1234567890", output_number, action
                )

                # Parse it back
                parsed = self.output_service.parse_system_telegram(telegram)

                # Verify consistency
                assert parsed.serial_number == "1234567890"
                assert parsed.output_number == output_number
                assert parsed.action_type == action
                assert parsed.checksum_validated is True

    def test_all_status_combinations(self):
        """Test status response parsing for all possible status combinations."""
        for status_bits in range(16):  # 0000 to 1111 in binary
            binary_str = format(status_bits, "04b")
            mock_response = f"<R0012345008F02D12xxxx{binary_str}FJ>"

            status = self.output_service.parse_status_response(mock_response)

            # Verify each bit is correctly parsed
            for i in range(4):
                expected_state = binary_str[3 - i] == "1"
                assert status[i] == expected_state

    def test_checksum_validation_integration(self):
        """Test checksum validation with real checksums."""
        # Generate telegram with valid checksum
        valid_telegram = self.output_service.generate_system_action_telegram(
            "0012345008", 1, ActionType.OFF_PRESS
        )

        # Parse and verify checksum is valid
        parsed = self.output_service.parse_system_telegram(valid_telegram)
        assert parsed.checksum_validated is True

        # Create telegram with invalid checksum
        invalid_telegram = valid_telegram[:-3] + "XX>"
        parsed_invalid = self.output_service.parse_system_telegram(invalid_telegram)
        assert parsed_invalid.checksum_validated is False

    def test_telegram_service_integration(self):
        """Test integration with existing telegram service."""
        from xp.services.telegram.telegram_service import TelegramService

        telegram_service = TelegramService()

        # Generate XP24 action telegram
        xp24_telegram = self.output_service.generate_system_action_telegram(
            "0012345008", 0, ActionType.OFF_PRESS
        )

        # Verify telegram service can recognize it as system telegram
        parsed_generic = telegram_service.parse_telegram(xp24_telegram)

        # Should be parsed as SystemTelegram
        from xp.models.telegram.system_telegram import SystemTelegram

        assert isinstance(parsed_generic, SystemTelegram)
        assert parsed_generic.serial_number == "0012345008"

    def test_error_handling_integration(self):
        """Test error handling across service layers."""
        # Test invalid output number
        with pytest.raises(XPOutputError, match="Invalid output number: 100"):
            self.output_service.generate_system_action_telegram(
                "0012345008", 100, ActionType.OFF_PRESS
            )

        # Test invalid serial number
        with pytest.raises(XPOutputError, match="Invalid serial number: 123"):
            self.output_service.generate_system_status_telegram("123")

        # Test invalid telegram parsing
        with pytest.raises(XPOutputError, match="Invalid XP24 action telegram format"):
            self.output_service.parse_system_telegram("<E14L00I02MAK>")

    def test_performance_requirements(self):
        """Test performance characteristics."""
        import time

        # Test telegram generation performance
        start_time = time.time()
        for _ in range(1000):
            self.output_service.generate_system_action_telegram(
                "0012345008", 0, ActionType.OFF_PRESS
            )
        generation_time = time.time() - start_time

        # Should generate 1000 telegrams in under 1 second
        assert generation_time < 1.0

        # Test telegram parsing performance
        test_telegram = "<S0012345008F27D01AAFN>"
        start_time = time.time()
        for _ in range(1000):
            self.output_service.parse_system_telegram(test_telegram)
        parsing_time = time.time() - start_time

        # Should parse 1000 telegrams in under 1 second
        assert parsing_time < 1.0
