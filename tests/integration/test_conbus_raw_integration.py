"""Integration tests for conbus raw CLI commands.

Tests the complete flow from CLI input to output,
ensuring proper integration between all layers.
"""

from unittest.mock import MagicMock

from click.testing import CliRunner

from xp.cli.main import cli
from xp.models.conbus.conbus_raw import ConbusRawResponse


class TestConbusRawIntegration:
    """Test class for conbus raw CLI integration."""

    def setup_method(self):
        """Set up test runner."""
        self.runner = CliRunner()

    def test_conbus_raw_single_telegram(self):
        """Test conbus raw command with single telegram."""
        # Mock the service
        mock_service = MagicMock()
        mock_service.__enter__.return_value = mock_service
        mock_service.__exit__.return_value = None

        # Mock the response
        mock_response = ConbusRawResponse(
            success=True,
            sent_telegrams="<S2113010000F02D12>",
            received_telegrams=["<R2113010000F02D12>"],
        )

        # Make the mock service call the callback immediately
        def mock_send_raw_telegram(
            raw_input, progress_callback, finish_callback, timeout_seconds=None
        ):
            """Test helper function.

            Args:
                raw_input: Raw telegram input.
                progress_callback: Callback for progress updates.
                finish_callback: Callback when finished.
                timeout_seconds: Timeout in seconds.
            """
            finish_callback(mock_response)

        mock_service.send_raw_telegram.side_effect = mock_send_raw_telegram

        # Mock the container
        mock_container = MagicMock()
        mock_container.get_container().resolve.return_value = mock_service

        result = self.runner.invoke(
            cli,
            ["conbus", "raw", "<S2113010000F02D12>"],
            obj={"container": mock_container},
        )

        assert result.exit_code == 0
        assert '"success": true' in result.output
        assert '"received_telegrams": [' in result.output
        mock_service.send_raw_telegram.assert_called_once()

    def test_conbus_raw_multiple_telegrams(self):
        """Test conbus raw command with multiple telegrams."""
        # Mock the service
        mock_service = MagicMock()
        mock_service.__enter__.return_value = mock_service
        mock_service.__exit__.return_value = None

        # Mock the response
        mock_response = ConbusRawResponse(
            success=True,
            sent_telegrams="<S2113010000F02D12><S2113010001F02D12><S2113010002F02D12>",
            received_telegrams=[
                "<R2113010000F02D12>",
                "<R2113010001F02D12>",
                "<S2113010002F02D12>",
            ],
        )

        # Make the mock service call the callback immediately
        def mock_send_raw_telegram(
            raw_input, progress_callback, finish_callback, timeout_seconds=None
        ):
            """Test helper function.

            Args:
                raw_input: Raw telegram input.
                progress_callback: Callback for progress updates.
                finish_callback: Callback when finished.
                timeout_seconds: Timeout in seconds.
            """
            # Simulate progress callbacks for each received telegram
            if mock_response.received_telegrams:
                for telegram in mock_response.received_telegrams:
                    progress_callback(telegram)
            finish_callback(mock_response)

        mock_service.send_raw_telegram.side_effect = mock_send_raw_telegram

        # Mock the container
        mock_container = MagicMock()
        mock_container.get_container().resolve.return_value = mock_service

        raw_input = "<S2113010000F02D12><S2113010001F02D12><S2113010002F02D12>"
        result = self.runner.invoke(
            cli, ["conbus", "raw", raw_input], obj={"container": mock_container}
        )

        assert result.exit_code == 0
        assert "<R2113010000F02D12>" in result.output
        assert "<R2113010001F02D12>" in result.output
        assert "<S2113010002F02D12>" in result.output
        mock_service.send_raw_telegram.assert_called_once()

    def test_conbus_raw_connection_error(self):
        """Test conbus raw command with connection error."""
        # Mock the service
        mock_service = MagicMock()
        mock_service.__enter__.return_value = mock_service
        mock_service.__exit__.return_value = None

        # Mock the response with error
        mock_response = ConbusRawResponse(success=False, error="Connection failed")

        # Make the mock service call the callback immediately
        def mock_send_raw_telegram(
            raw_input, progress_callback, finish_callback, timeout_seconds=None
        ):
            """Test helper function.

            Args:
                raw_input: Raw telegram input.
                progress_callback: Callback for progress updates.
                finish_callback: Callback when finished.
                timeout_seconds: Timeout in seconds.
            """
            finish_callback(mock_response)

        mock_service.send_raw_telegram.side_effect = mock_send_raw_telegram

        # Mock the container
        mock_container = MagicMock()
        mock_container.get_container().resolve.return_value = mock_service

        result = self.runner.invoke(
            cli,
            ["conbus", "raw", "<S2113010000F02D12>"],
            obj={"container": mock_container},
        )

        assert (
            result.exit_code == 0
        )  # CLI doesn't exit with error code, but shows error
        assert '"success": false' in result.output
        assert '"error": "Connection failed"' in result.output

    def test_conbus_raw_no_response(self):
        """Test conbus raw command with no response."""
        # Mock the service
        mock_service = MagicMock()
        mock_service.__enter__.return_value = mock_service
        mock_service.__exit__.return_value = None

        # Mock the response with no received telegrams
        mock_response = ConbusRawResponse(
            success=True, sent_telegrams="<S2113010000F02D12>", received_telegrams=[]
        )

        # Make the mock service call the callback immediately
        def mock_send_raw_telegram(
            raw_input, progress_callback, finish_callback, timeout_seconds=None
        ):
            """Test helper function.

            Args:
                raw_input: Raw telegram input.
                progress_callback: Callback for progress updates.
                finish_callback: Callback when finished.
                timeout_seconds: Timeout in seconds.
            """
            finish_callback(mock_response)

        mock_service.send_raw_telegram.side_effect = mock_send_raw_telegram

        # Mock the container
        mock_container = MagicMock()
        mock_container.get_container().resolve.return_value = mock_service

        result = self.runner.invoke(
            cli,
            ["conbus", "raw", "<S2113010000F02D12>"],
            obj={"container": mock_container},
        )

        assert result.exit_code == 0
        assert '"success": true' in result.output
        # received_telegrams field should not be included when empty
        assert (
            '"received_telegrams"' not in result.output
            or '"received_telegrams": []' in result.output
        )

    def test_conbus_raw_help_command(self):
        """Test conbus raw help command."""
        result = self.runner.invoke(cli, ["conbus", "raw", "--help"])

        assert result.exit_code == 0
        output = result.output

        assert "Send raw telegram sequence to Conbus server" in output
        assert "RAW_TELEGRAMS" in output

    def test_conbus_raw_missing_arguments(self):
        """Test conbus raw command with missing arguments."""
        result = self.runner.invoke(cli, ["conbus", "raw"])

        assert result.exit_code != 0
        assert "Usage: cli conbus raw [OPTIONS] RAW_TELEGRAMS" in result.output

    def test_conbus_raw_service_exception(self):
        """Test conbus raw command when service raises exception."""
        # Mock the service to raise an exception
        mock_service = MagicMock()
        mock_service.__enter__.return_value = mock_service
        mock_service.__exit__.return_value = None

        # Make the service raise an exception when send_raw_telegram is called
        mock_service.send_raw_telegram.side_effect = Exception("Service error")

        # Mock the container
        mock_container = MagicMock()
        mock_container.get_container().resolve.return_value = mock_service

        result = self.runner.invoke(
            cli,
            ["conbus", "raw", "<S2113010000F02D12>"],
            obj={"container": mock_container},
        )

        # The CLI should handle the exception gracefully
        assert result.exit_code != 0

    def test_conbus_raw_command_registration(self):
        """Test that conbus raw command is properly registered."""
        result = self.runner.invoke(cli, ["conbus", "--help"])

        assert result.exit_code == 0
        assert "raw" in result.output
