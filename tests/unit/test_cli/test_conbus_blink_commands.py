"""Tests for conbus blink commands"""

from unittest.mock import Mock, patch
from click.testing import CliRunner
from xp.cli.commands.conbus_blink_commands import send_blink_telegram, send_blink_on_telegram, send_blink_off_telegram
from xp.cli.commands import *
from xp.services.conbus_datapoint_service import ConbusDatapointError
from xp.models import ConbusDatapointRequest
from xp.models import ConbusDatapointResponse, DatapointTypeName
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


    def test_conbus_blink_invalid_serial_json(self):
        """Test blink command with invalid serial number and JSON output"""
        runner = CliRunner()
        result = runner.invoke(conbus, ["blink", "on", "invalid"])

        assert result.exit_code == 2
        assert (
            "Error: Invalid value for 'SERIAL_NUMBER': 'invalid' contains non-numeric characters" in result.output
        )

    @patch("xp.cli.commands.conbus_blink_commands.ConbusDatapointService")
    def test_conbus_blink_connection_error(self, mock_service_class):
        """Test blink command with connection error"""
        # Mock the service instance to raise connection error
        mock_service = Mock()
        mock_service_class.return_value = mock_service

        # Mock the context manager behavior
        mock_service.__enter__ = Mock(return_value=mock_service)
        mock_service.__exit__ = Mock(return_value=None)

        mock_service.send_custom_telegram.side_effect = ConbusDatapointError(
            "Connection timeout"
        )

        runner = CliRunner()
        result = runner.invoke(conbus, ["blink", "on", "0020044964"])

        assert result.exit_code != 0
        assert "Connection timeout" in result.output

    def test_conbus_unblink_invalid_serial(self):
        """Test unblink command with invalid serial number"""
        runner = CliRunner()
        result = runner.invoke(conbus, ["blink", "off", "123"])

        assert result.exit_code == 0
        assert '"target_serial": "0000000123"' in result.output

