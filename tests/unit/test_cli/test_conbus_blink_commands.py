"""Tests for conbus blink commands"""

from unittest.mock import Mock, patch
from click.testing import CliRunner
from src.xp.cli.commands.conbus_blink_commands import send_blink_telegram, send_blink_on_telegram, send_blink_off_telegram
from src.xp.cli.commands import *
from src.xp.services.conbus_client_send_service import ConbusClientSendError
from src.xp.models import ConbusSendRequest, ConbusSendResponse, DatapointTypeName
from datetime import datetime


class TestConbusBlinkCommands:
    """Test cases for conbus blink and unblink commands"""

    def test_conbus_blink_help(self):
        """Test help text for conbus blink command"""
        runner = CliRunner()
        result = runner.invoke(conbus, ["blink", "--help"])

        assert result.exit_code == 0
        assert "Send blink command to start blinking module LED" in result.output
        assert "Usage:" in result.output
        assert "conbus blink [OPTIONS] COMMAND" in result.output

    def test_conbus_unblink_help(self):
        """Test help text for conbus unblink command"""
        runner = CliRunner()
        result = runner.invoke(conbus, ["blink", "--help"])

        assert result.exit_code == 0
        assert "Usage: conbus blink [OPTIONS] COMMAND [ARGS]" in result.output
        assert "Usage:" in result.output

    @patch("src.xp.cli.commands.conbus_blink_commands.ConbusClientSendService")
    def test_conbus_blink_success(self, mock_service_class):
        """Test successful blink command execution"""
        # Mock the service instance and response
        mock_service = Mock()
        mock_service_class.return_value = mock_service

        # Mock the context manager behavior
        mock_service.__enter__ = Mock(return_value=mock_service)
        mock_service.__exit__ = Mock(return_value=None)

        mock_response = ConbusSendResponse(
            success=True,
            request=ConbusSendRequest(
                telegram_type=DatapointTypeName.BLINK, target_serial="0020044964"
            ),
            sent_telegram="<S0020044964F05D00FN>",
            received_telegrams=["<R0020044964F18DFA>"],
            timestamp=datetime(2025, 9, 11, 23, 0, 0),
            error=None,
        )

        mock_service.send_custom_telegram.return_value = mock_response

        runner = CliRunner()
        result = runner.invoke(conbus, ["blink", "on", "0020044964"])

        assert result.exit_code == 0
        assert "<S0020044964F05D00FN>" in result.output
        assert "<R0020044964F18DFA>" in result.output
        assert '"operation": "blink"' in result.output

        # Verify the service was called correctly
        mock_service.send_custom_telegram.assert_called_once_with(
            "0020044964", "05", "00"
        )

    @patch("src.xp.cli.commands.conbus_blink_commands.ConbusClientSendService")
    def test_conbus_unblink_success(self, mock_service_class):
        """Test successful unblink command execution"""
        # Mock the service instance and response
        mock_service = Mock()
        mock_service_class.return_value = mock_service

        # Mock the context manager behavior
        mock_service.__enter__ = Mock(return_value=mock_service)
        mock_service.__exit__ = Mock(return_value=None)

        mock_response = ConbusSendResponse(
            success=True,
            request=ConbusSendRequest(
                telegram_type=DatapointTypeName.UNBLINK, target_serial="0020030837"
            ),
            sent_telegram="<S0020030837F06D00FK>",
            received_telegrams=["<R0020030837F18DFE>"],
            timestamp=datetime(2025, 9, 11, 23, 0, 0),
            error=None,
        )

        mock_service.send_custom_telegram.return_value = mock_response

        runner = CliRunner()
        result = runner.invoke(conbus, ["blink", "off", "0020030837"])

        assert result.exit_code == 0
        assert "<S0020030837F06D00FK>" in result.output
        assert "<R0020030837F18DFE>" in result.output
        assert '"telegram_type": "unblink"' in result.output

        # Verify the service was called correctly
        mock_service.send_custom_telegram.assert_called_once_with(
            "0020030837", "06", "00"
        )

    @patch("src.xp.cli.commands.conbus_blink_commands.ConbusClientSendService")
    def test_conbus_blink_json_success(self, mock_service_class):
        """Test successful blink command with JSON output"""
        # Mock the service instance and response
        mock_service = Mock()
        mock_service_class.return_value = mock_service

        # Mock the context manager behavior
        mock_service.__enter__ = Mock(return_value=mock_service)
        mock_service.__exit__ = Mock(return_value=None)

        mock_response = ConbusSendResponse(
            success=True,
            request=ConbusSendRequest(
                telegram_type=DatapointTypeName.BLINK, target_serial="0020044964"
            ),
            sent_telegram="<S0020044964F05D00FN>",
            received_telegrams=["<R0020044964F18DFA>"],
            timestamp=datetime(2025, 9, 11, 23, 0, 0),
            error=None,
        )

        mock_service.send_custom_telegram.return_value = mock_response

        runner = CliRunner()
        result = runner.invoke(conbus, ["blink", "on", "0020044964"])

        assert result.exit_code == 0
        assert '"operation": "blink"' in result.output
        assert '"telegram_type": "blink"' in result.output
        assert '"sent_telegram": "<S0020044964F05D00FN>"' in result.output

    def test_conbus_blink_invalid_serial_json(self):
        """Test blink command with invalid serial number and JSON output"""
        runner = CliRunner()
        result = runner.invoke(conbus, ["blink", "on", "invalid"])

        assert result.exit_code == 2
        assert (
            "Error: Invalid value for 'SERIAL_NUMBER': 'invalid' contains non-numeric characters" in result.output
        )

    @patch("src.xp.cli.commands.conbus_blink_commands.ConbusClientSendService")
    def test_conbus_blink_connection_error(self, mock_service_class):
        """Test blink command with connection error"""
        # Mock the service instance to raise connection error
        mock_service = Mock()
        mock_service_class.return_value = mock_service

        # Mock the context manager behavior
        mock_service.__enter__ = Mock(return_value=mock_service)
        mock_service.__exit__ = Mock(return_value=None)

        mock_service.send_custom_telegram.side_effect = ConbusClientSendError(
            "Connection timeout"
        )

        runner = CliRunner()
        result = runner.invoke(conbus, ["blink", "on", "0020044964"])

        assert result.exit_code != 0
        assert "Connection timeout" in result.output

    @patch("src.xp.cli.commands.conbus_blink_commands.ConbusClientSendService")
    def test_conbus_blink_no_response(self, mock_service_class):
        """Test blink command with no response from server"""
        # Mock the service instance and response with no received telegrams
        mock_service = Mock()
        mock_service_class.return_value = mock_service

        # Mock the context manager behavior
        mock_service.__enter__ = Mock(return_value=mock_service)
        mock_service.__exit__ = Mock(return_value=None)

        mock_response = ConbusSendResponse(
            success=True,
            request=ConbusSendRequest(
                telegram_type=DatapointTypeName.BLINK, target_serial="0020044964"
            ),
            sent_telegram="<S0020044964F05D00FN>",
            received_telegrams=[],  # No response
            timestamp=datetime(2025, 9, 11, 23, 0, 0),
            error=None,
        )

        mock_service.send_custom_telegram.return_value = mock_response

        runner = CliRunner()
        result = runner.invoke(conbus, ["blink", "on", "0020044964"])

        assert result.exit_code == 0
        assert "<S0020044964F05D00FN>" in result.output
        assert '"received_telegrams": []' in result.output

    def test_conbus_unblink_invalid_serial(self):
        """Test unblink command with invalid serial number"""
        runner = CliRunner()
        result = runner.invoke(conbus, ["blink", "off", "123"])

        assert result.exit_code == 0
        assert '"target_serial": "0000000123"' in result.output

    @patch("src.xp.cli.commands.conbus_blink_commands.ConbusClientSendService")
    def test_conbus_unblink_json_success(self, mock_service_class):
        """Test successful unblink command with JSON output"""
        # Mock the service instance and response
        mock_service = Mock()
        mock_service_class.return_value = mock_service

        # Mock the context manager behavior
        mock_service.__enter__ = Mock(return_value=mock_service)
        mock_service.__exit__ = Mock(return_value=None)

        mock_response = ConbusSendResponse(
            success=True,
            request=ConbusSendRequest(
                telegram_type=DatapointTypeName.UNBLINK, target_serial="0020030837"
            ),
            sent_telegram="<S0020030837F06D00FK>",
            received_telegrams=["<R0020030837F18DFE>"],
            timestamp=datetime(2025, 9, 11, 23, 0, 0),
            error=None,
        )

        mock_service.send_custom_telegram.return_value = mock_response

        runner = CliRunner()
        result = runner.invoke(conbus, ["blink", "off", "0020030837"])

        assert result.exit_code == 0
        assert '"operation": "unblink"' in result.output
        assert '"telegram_type": "unblink"' in result.output
        assert '"sent_telegram": "<S0020030837F06D00FK>"' in result.output
