"""Integration tests for XP24 action functionality."""

import pytest
from unittest.mock import patch, MagicMock

from src.xp.services.input_service import XPInputService, XPInputError
from src.xp.models.action_type import ActionType
from src.xp.services.conbus_client_send_service import ConbusClientSendService


class TestXPInputIntegration:
    """Integration tests for XP24 action functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.input_service = XPInputService()
        self.conbus_service = ConbusClientSendService()

    def test_end_to_end_action_generation_and_parsing(self):
        """Test complete flow: generate telegram, parse it back."""
        # Generate action telegram
        original_telegram = self.input_service.generate_input_telegram(
            "0020044964", 2, ActionType.RELEASE
        )

        # Parse the generated telegram
        parsed = self.input_service.parse_input_telegram(original_telegram)

        # Verify parsed data matches original
        assert parsed.serial_number == "0020044964"
        assert parsed.input_number == 2
        assert parsed.action_type == ActionType.RELEASE
        assert parsed.raw_telegram == original_telegram
        assert parsed.checksum_validated is True

    def test_end_to_end_status_generation_and_parsing(self):
        """Test complete flow: generate status query, parse response."""
        # Generate status query telegram
        status_telegram = self.input_service.generate_input_status_telegram(
            "0020044964"
        )

        # Verify generated format
        assert status_telegram.startswith("<S0020044964F02D12")
        assert status_telegram.endswith(">")
        assert len(status_telegram) == 21  # <S0020044964F02D12XX>

        # Simulate status response and parse
        mock_response = "<R0020044964F02D12xxxx1010FJ>"
        status = self.input_service.parse_status_response(mock_response)

        expected = {0: True, 1: False, 2: True, 3: False}
        assert status == expected

    def test_all_input_combinations(self):
        """Test telegram generation and parsing for all input combinations."""
        for input_num in range(4):
            for action in [ActionType.PRESS, ActionType.RELEASE]:
                # Generate telegram
                telegram = self.input_service.generate_input_telegram(
                    "1234567890", input_num, action
                )

                # Parse it back
                parsed = self.input_service.parse_input_telegram(telegram)

                # Verify consistency
                assert parsed.serial_number == "1234567890"
                assert parsed.input_number == input_num
                assert parsed.action_type == action
                assert parsed.checksum_validated is True

    def test_all_status_combinations(self):
        """Test status response parsing for all possible status combinations."""
        for status_bits in range(16):  # 0000 to 1111 in binary
            binary_str = format(status_bits, "04b")
            mock_response = f"<R0020044964F02D12xxxx{binary_str}FJ>"

            status = self.input_service.parse_status_response(mock_response)

            # Verify each bit is correctly parsed
            for i in range(4):
                expected_state = binary_str[i] == "1"
                assert status[i] == expected_state

    def test_checksum_validation_integration(self):
        """Test checksum validation with real checksums."""
        # Generate telegram with valid checksum
        valid_telegram = self.input_service.generate_input_telegram(
            "0020044964", 1, ActionType.PRESS
        )

        # Parse and verify checksum is valid
        parsed = self.input_service.parse_input_telegram(valid_telegram)
        assert parsed.checksum_validated is True

        # Create telegram with invalid checksum
        invalid_telegram = valid_telegram[:-3] + "XX>"
        parsed_invalid = self.input_service.parse_input_telegram(invalid_telegram)
        assert parsed_invalid.checksum_validated is False

    def test_telegram_service_integration(self):
        """Test integration with existing telegram service."""
        from src.xp.services.telegram_service import TelegramService

        telegram_service = TelegramService()

        # Generate XP24 action telegram
        xp24_telegram = self.input_service.generate_input_telegram(
            "0020044964", 0, ActionType.PRESS
        )

        # Verify telegram service can recognize it as system telegram
        parsed_generic = telegram_service.parse_telegram(xp24_telegram)

        # Should be parsed as SystemTelegram
        from src.xp.models.system_telegram import SystemTelegram

        assert isinstance(parsed_generic, SystemTelegram)
        assert parsed_generic.serial_number == "0020044964"

    @patch(
        "src.xp.services.conbus_client_send_service.ConbusClientSendService.send_custom_telegram"
    )
    def test_cli_command_integration_action(self, mock_send):
        """Test integration with CLI command for action."""
        from click.testing import CliRunner
        from src.xp.cli.commands.conbus_input_commands import conbus

        # Mock successful response
        mock_response = MagicMock()
        mock_response.success = True
        mock_response.sent_telegram = "<S0020044964F27D01AAFN>"
        mock_response.received_telegrams = ["<R0020044964F18DFA>"]
        mock_response.timestamp.strftime.return_value = "12:34:56,789"
        mock_response.to_dict.return_value = {"success": True}
        mock_send.return_value = mock_response

        runner = CliRunner()
        result = runner.invoke(conbus, ["input", "0020044964", "1", "on"])

        assert result.exit_code == 0
        assert "[TX] <S0020044964F27D01AAFN>" in result.output
        assert "[RX] <R0020044964F18DFA>" in result.output
        assert "XP24 action sent: Press input 1" in result.output

        # Verify service was called with correct parameters
        mock_send.assert_called_once_with("0020044964", "27", "01AA")

    @patch(
        "src.xp.services.conbus_client_send_service.ConbusClientSendService.send_custom_telegram"
    )
    def test_cli_command_integration_status(self, mock_send):
        """Test integration with CLI command for status query."""
        from click.testing import CliRunner
        from src.xp.cli.commands.conbus_input_commands import conbus

        # Mock successful status response
        mock_response = MagicMock()
        mock_response.success = True
        mock_response.sent_telegram = "<S0020044964F02D12FJ>"
        mock_response.received_telegrams = ["<R0020044964F02D12xxxx1010FJ>"]
        mock_response.timestamp.strftime.return_value = "12:34:56,789"
        mock_response.to_dict.return_value = {"success": True}
        mock_send.return_value = mock_response

        runner = CliRunner()
        result = runner.invoke(conbus, ["input", "0020044964", "status"])

        assert result.exit_code == 0
        assert "[TX] <S0020044964F02D12FJ>" in result.output
        assert "[RX] <R0020044964F02D12xxxx1010FJ>" in result.output
        assert "XP24 Input Status:" in result.output
        assert "Input 0: ON" in result.output
        assert "Input 1: OFF" in result.output
        assert "Input 2: ON" in result.output
        assert "Input 3: OFF" in result.output

        # Verify service was called with correct parameters
        mock_send.assert_called_once_with("0020044964", "02", "12")

    @patch(
        "src.xp.services.conbus_client_send_service.ConbusClientSendService.send_custom_telegram"
    )
    def test_cli_command_json_output(self, mock_send):
        """Test CLI command with JSON output."""
        from click.testing import CliRunner
        from src.xp.cli.commands.conbus_input_commands import conbus
        import json

        # Mock successful response
        mock_response = MagicMock()
        mock_response.success = True
        mock_response.to_dict.return_value = {
            "success": True,
            "sent_telegram": "<S0020044964F27D00AAFN>",
            "received_telegrams": ["<R0020044964F18DFA>"],
        }
        mock_send.return_value = mock_response

        runner = CliRunner()
        result = runner.invoke(conbus, ["input", "0020044964", "0"])
        assert result.exit_code == 0

        # Parse JSON output
        output_data = json.loads(result.output)
        assert output_data["success"] is True
        assert output_data["xp24_operation"] == "action_command"
        assert output_data["input_number"] == 0
        assert output_data["action_type"] == "press"
        assert output_data["telegram_type"] == "xp24_action"

    def test_error_handling_integration(self):
        """Test error handling across service layers."""
        # Test invalid input number
        with pytest.raises(XPInputError, match="Invalid input number: 5"):
            self.input_service.generate_input_telegram(
                "0020044964", 5, ActionType.PRESS
            )

        # Test invalid serial number
        with pytest.raises(XPInputError, match="Invalid serial number: 123"):
            self.input_service.generate_input_status_telegram("123")

        # Test invalid telegram parsing
        with pytest.raises(XPInputError, match="Invalid XP24 action telegram format"):
            self.input_service.parse_input_telegram("<E14L00I02MAK>")

    def test_architecture_compliance(self):
        """Test compliance with architecture constraints."""
        # Verify MAX_INPUTS constraint is enforced
        assert self.input_service.MAX_INPUTS == 4

        # Verify all input validation follows architecture rules
        for invalid_input in [-1, 4, 5, 10]:
            with pytest.raises(XPInputError):
                self.input_service.validate_input_number(invalid_input)

        # Verify serial number validation
        for invalid_serial in ["123", "12345678901", "abc1234567"]:
            with pytest.raises(XPInputError):
                self.input_service.validate_serial_number(invalid_serial)

    def test_performance_requirements(self):
        """Test performance characteristics."""
        import time

        # Test telegram generation performance
        start_time = time.time()
        for _ in range(1000):
            self.input_service.generate_input_telegram(
                "0020044964", 0, ActionType.PRESS
            )
        generation_time = time.time() - start_time

        # Should generate 1000 telegrams in under 1 second
        assert generation_time < 1.0

        # Test telegram parsing performance
        test_telegram = "<S0020044964F27D01AAFN>"
        start_time = time.time()
        for _ in range(1000):
            self.input_service.parse_input_telegram(test_telegram)
        parsing_time = time.time() - start_time

        # Should parse 1000 telegrams in under 1 second
        assert parsing_time < 1.0
