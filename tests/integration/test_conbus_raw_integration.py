# Copyright (c) 2025 ldvchosal
"""Integration tests for conbus raw CLI commands.

Tests the complete flow from CLI input to output, ensuring proper integration between
all layers.
"""

from collections.abc import Callable
from unittest.mock import MagicMock

from click.testing import CliRunner

from xp.cli.main import cli
from xp.models.conbus.conbus_raw import ConbusRawResponse


class TestConbusRawIntegration:
    """Test class for conbus raw CLI integration."""

    def setup_method(self) -> None:
        """Set up test runner."""
        self.runner = CliRunner()

    def test_conbus_raw_single_telegram(self) -> None:
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

        # Store the callbacks that are connected
        callbacks: dict[str, Callable[..., None] | None] = {
            "on_finish": None,
            "on_progress": None,
        }

        def mock_on_finish_connect(callback: Callable[..., None]) -> None:
            """Mock on_finish event connection.

            Args:
                callback: Callback function to store.

            """
            callbacks["on_finish"] = callback

        def mock_on_progress_connect(callback: Callable[..., None]) -> None:
            """Mock on_progress event connection.

            Args:
                callback: Callback function to store.

            """
            callbacks["on_progress"] = callback

        mock_service.on_finish.connect.side_effect = mock_on_finish_connect
        mock_service.on_progress.connect.side_effect = mock_on_progress_connect

        # Make the mock service call the callback immediately
        def mock_send_raw_telegrams(
            telegrams: list[str], timeout_seconds: float | None = None
        ) -> None:
            """Invoke the connected on_finish callback immediately."""
            del telegrams, timeout_seconds  # Unused; accepted for kwargs call
            # Call the on_finish callback that was connected
            on_finish = callbacks["on_finish"]
            if on_finish:
                on_finish(mock_response)

        def mock_start_reactor() -> None:
            """Mock reactor start method."""
            # Do nothing in test

        mock_service.send_raw_telegrams.side_effect = mock_send_raw_telegrams
        mock_service.start_reactor.side_effect = mock_start_reactor

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
        mock_service.send_raw_telegrams.assert_called_once()

    def test_conbus_raw_multiple_telegrams(self) -> None:
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

        # Store the callbacks that are connected
        callbacks: dict[str, Callable[..., None] | None] = {
            "on_finish": None,
            "on_progress": None,
        }

        def mock_on_finish_connect(callback: Callable[..., None]) -> None:
            """Mock on_finish event connection.

            Args:
                callback: Callback function to store.

            """
            callbacks["on_finish"] = callback

        def mock_on_progress_connect(callback: Callable[..., None]) -> None:
            """Mock on_progress event connection.

            Args:
                callback: Callback function to store.

            """
            callbacks["on_progress"] = callback

        mock_service.on_finish.connect.side_effect = mock_on_finish_connect
        mock_service.on_progress.connect.side_effect = mock_on_progress_connect

        # Make the mock service call the callback immediately
        def mock_send_raw_telegrams(
            telegrams: list[str], timeout_seconds: float | None = None
        ) -> None:
            """Invoke progress callbacks, then the on_finish callback."""
            del telegrams, timeout_seconds  # Unused; accepted for kwargs call
            # Simulate progress callbacks for each received telegram
            on_progress = callbacks["on_progress"]
            if mock_response.received_telegrams:
                for telegram in mock_response.received_telegrams:
                    if on_progress:
                        on_progress(telegram)
            # Call the on_finish callback that was connected
            on_finish = callbacks["on_finish"]
            if on_finish:
                on_finish(mock_response)

        def mock_start_reactor() -> None:
            """Mock reactor start method."""
            # Do nothing in test

        mock_service.send_raw_telegrams.side_effect = mock_send_raw_telegrams
        mock_service.start_reactor.side_effect = mock_start_reactor

        # Mock the container
        mock_container = MagicMock()
        mock_container.get_container().resolve.return_value = mock_service

        result = self.runner.invoke(
            cli,
            [
                "conbus",
                "raw",
                "<S2113010000F02D12>",
                "<S2113010001F02D12>",
                "<S2113010002F02D12>",
            ],
            obj={"container": mock_container},
        )

        assert result.exit_code == 0
        assert "<R2113010000F02D12>" in result.output
        assert "<R2113010001F02D12>" in result.output
        assert "<S2113010002F02D12>" in result.output
        mock_service.send_raw_telegrams.assert_called_once()

    def test_conbus_raw_connection_error(self) -> None:
        """Test conbus raw command with connection error."""
        # Mock the service
        mock_service = MagicMock()
        mock_service.__enter__.return_value = mock_service
        mock_service.__exit__.return_value = None

        # Mock the response with error
        mock_response = ConbusRawResponse(success=False, error="Connection failed")

        # Store the callbacks that are connected
        callbacks: dict[str, Callable[..., None] | None] = {
            "on_finish": None,
            "on_progress": None,
        }

        def mock_on_finish_connect(callback: Callable[..., None]) -> None:
            """Mock on_finish event connection.

            Args:
                callback: Callback function to store.

            """
            callbacks["on_finish"] = callback

        def mock_on_progress_connect(callback: Callable[..., None]) -> None:
            """Mock on_progress event connection.

            Args:
                callback: Callback function to store.

            """
            callbacks["on_progress"] = callback

        mock_service.on_finish.connect.side_effect = mock_on_finish_connect
        mock_service.on_progress.connect.side_effect = mock_on_progress_connect

        # Make the mock service call the callback immediately
        def mock_send_raw_telegrams(
            telegrams: list[str], timeout_seconds: float | None = None
        ) -> None:
            """Invoke the connected on_finish callback immediately."""
            del telegrams, timeout_seconds  # Unused; accepted for kwargs call
            # Call the on_finish callback that was connected
            on_finish = callbacks["on_finish"]
            if on_finish:
                on_finish(mock_response)

        def mock_start_reactor() -> None:
            """Mock reactor start method."""
            # Do nothing in test

        mock_service.send_raw_telegrams.side_effect = mock_send_raw_telegrams
        mock_service.start_reactor.side_effect = mock_start_reactor

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

    def test_conbus_raw_no_response(self) -> None:
        """Test conbus raw command with no response."""
        # Mock the service
        mock_service = MagicMock()
        mock_service.__enter__.return_value = mock_service
        mock_service.__exit__.return_value = None

        # Mock the response with no received telegrams
        mock_response = ConbusRawResponse(
            success=True, sent_telegrams="<S2113010000F02D12>", received_telegrams=[]
        )

        # Store the callbacks that are connected
        callbacks: dict[str, Callable[..., None] | None] = {
            "on_finish": None,
            "on_progress": None,
        }

        def mock_on_finish_connect(callback: Callable[..., None]) -> None:
            """Mock on_finish event connection.

            Args:
                callback: Callback function to store.

            """
            callbacks["on_finish"] = callback

        def mock_on_progress_connect(callback: Callable[..., None]) -> None:
            """Mock on_progress event connection.

            Args:
                callback: Callback function to store.

            """
            callbacks["on_progress"] = callback

        mock_service.on_finish.connect.side_effect = mock_on_finish_connect
        mock_service.on_progress.connect.side_effect = mock_on_progress_connect

        # Make the mock service call the callback immediately
        def mock_send_raw_telegrams(
            telegrams: list[str], timeout_seconds: float | None = None
        ) -> None:
            """Invoke the connected on_finish callback immediately."""
            del telegrams, timeout_seconds  # Unused; accepted for kwargs call
            # Call the on_finish callback that was connected
            on_finish = callbacks["on_finish"]
            if on_finish:
                on_finish(mock_response)

        def mock_start_reactor() -> None:
            """Mock reactor start method."""
            # Do nothing in test

        mock_service.send_raw_telegrams.side_effect = mock_send_raw_telegrams
        mock_service.start_reactor.side_effect = mock_start_reactor

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

    def test_conbus_raw_help_command(self) -> None:
        """Test conbus raw help command."""
        result = self.runner.invoke(cli, ["conbus", "raw", "--help"])

        assert result.exit_code == 0
        output = result.output

        assert "Send raw telegram sequence to Conbus server" in output
        assert "TELEGRAMS" in output

    def test_conbus_raw_missing_arguments(self) -> None:
        """Test conbus raw command with missing arguments."""
        result = self.runner.invoke(cli, ["conbus", "raw"])

        assert result.exit_code != 0
        assert "Usage: cli conbus raw [OPTIONS] TELEGRAMS" in result.output

    def test_conbus_raw_service_exception(self) -> None:
        """Test conbus raw command when service raises exception."""
        # Mock the service to raise an exception
        mock_service = MagicMock()
        mock_service.__enter__.return_value = mock_service
        mock_service.__exit__.return_value = None

        # Make the service raise an exception when send_raw_telegrams is called
        mock_service.send_raw_telegrams.side_effect = Exception("Service error")

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

    def test_conbus_raw_command_registration(self) -> None:
        """Test that conbus raw command is properly registered."""
        result = self.runner.invoke(cli, ["conbus", "--help"])

        assert result.exit_code == 0
        assert "raw" in result.output
