"""Unit tests for conbus msactiontable upload CLI command."""

from unittest.mock import Mock

import pytest
from click.testing import CliRunner

from xp.cli.commands.conbus.conbus_msactiontable_commands import (
    conbus_upload_msactiontable,
)
from xp.models.actiontable.actiontable_type import ActionTableType2


class TestConbusMsActionTableUploadCommand:
    """Test cases for conbus msactiontable upload CLI command."""

    @pytest.fixture
    def runner(self):
        """Create CLI test runner."""
        return CliRunner()

    def _create_mock_service(self, success=True, error=None):
        """
        Create mock upload service with signal pattern.

        Args:
            success: Whether upload should succeed.
            error: Optional error message to trigger error callback.

        Returns:
            Mock service object configured with signals.
        """
        mock_service = Mock()
        mock_service.__enter__ = Mock(return_value=mock_service)
        mock_service.__exit__ = Mock(return_value=None)

        # Create mock signals
        mock_service.on_progress = Mock()
        mock_service.on_finish = Mock()
        mock_service.on_error = Mock()

        # Track connected callbacks
        progress_callbacks = []
        finish_callbacks = []
        error_callbacks = []

        def connect_progress(callback):
            """
            Mock connect for progress signal.

            Args:
                callback: Callback function to connect.
            """
            progress_callbacks.append(callback)

        def connect_finish(callback):
            """
            Mock connect for finish signal.

            Args:
                callback: Callback function to connect.
            """
            finish_callbacks.append(callback)

        def connect_error(callback):
            """
            Mock connect for error signal.

            Args:
                callback: Callback function to connect.
            """
            error_callbacks.append(callback)

        mock_service.on_progress.connect = connect_progress
        mock_service.on_finish.connect = connect_finish
        mock_service.on_error.connect = connect_error

        def mock_start_reactor():
            """Execute mock start_reactor operation."""
            if error:
                for callback in error_callbacks:
                    callback(error)
            else:
                # Simulate progress
                for callback in progress_callbacks:
                    callback(".")
                # Simulate finish
                for callback in finish_callbacks:
                    callback(success)

        mock_service.start = Mock()
        mock_service.start_reactor.side_effect = mock_start_reactor
        mock_service.stop_reactor = Mock()
        return mock_service

    def test_upload_msactiontable_success(self, runner):
        """Test successful msactiontable upload command."""
        # Setup mock service
        mock_service = self._create_mock_service(success=True)

        # Setup mock container
        mock_container = Mock()
        mock_container.resolve.return_value = mock_service
        mock_service_container = Mock()
        mock_service_container.get_container.return_value = mock_container

        # Execute command
        result = runner.invoke(
            conbus_upload_msactiontable,
            ["0020044991"],
            obj={"container": mock_service_container},
        )

        # Verify success
        assert result.exit_code == 0
        mock_service.start.assert_called_once_with(
            serial_number="0020044991",
            actiontable_type=ActionTableType2.MSACTIONTABLE,
        )
        assert "Uploading msactiontable to 0020044991" in result.output
        assert "Msactiontable uploaded successfully" in result.output

    def test_upload_msactiontable_progress_display(self, runner):
        """Test that progress dots are displayed during upload."""
        # Setup mock service
        mock_service = self._create_mock_service(success=True)

        # Setup mock container
        mock_container = Mock()
        mock_container.resolve.return_value = mock_service
        mock_service_container = Mock()
        mock_service_container.get_container.return_value = mock_container

        # Execute command
        result = runner.invoke(
            conbus_upload_msactiontable,
            ["0020044991"],
            obj={"container": mock_service_container},
        )

        # Verify progress indicator
        assert "." in result.output

    def test_upload_msactiontable_module_not_found_error(self, runner):
        """Test error handling when module not found."""
        # Setup mock service with error
        mock_service = self._create_mock_service(
            error="Module 0020044991 not found in conson.yml"
        )

        # Setup mock container
        mock_container = Mock()
        mock_container.resolve.return_value = mock_service
        mock_service_container = Mock()
        mock_service_container.get_container.return_value = mock_container

        # Execute command
        result = runner.invoke(
            conbus_upload_msactiontable,
            ["0020044991"],
            obj={"container": mock_service_container},
        )

        # Verify error message
        assert "Error: Module 0020044991 not found in conson.yml" in result.output
        mock_service.stop_reactor.assert_called()

    def test_upload_msactiontable_missing_config_error(self, runner):
        """Test error handling when msactiontable config is missing."""
        # Setup mock service with error
        mock_service = self._create_mock_service(
            error="Module 0020044991 does not have msaction_table configured"
        )

        # Setup mock container
        mock_container = Mock()
        mock_container.resolve.return_value = mock_service
        mock_service_container = Mock()
        mock_service_container.get_container.return_value = mock_container

        # Execute command
        result = runner.invoke(
            conbus_upload_msactiontable,
            ["0020044991"],
            obj={"container": mock_service_container},
        )

        # Verify error message
        assert "Error:" in result.output
        assert "msaction_table configured" in result.output

    def test_upload_msactiontable_empty_list_error(self, runner):
        """Test error handling when msactiontable list is empty."""
        # Setup mock service with error
        mock_service = self._create_mock_service(
            error="Module 0020044991 has empty msaction_table list in conson.yml"
        )

        # Setup mock container
        mock_container = Mock()
        mock_container.resolve.return_value = mock_service
        mock_service_container = Mock()
        mock_service_container.get_container.return_value = mock_container

        # Execute command
        result = runner.invoke(
            conbus_upload_msactiontable,
            ["0020044991"],
            obj={"container": mock_service_container},
        )

        # Verify error message
        assert "Error:" in result.output
        assert "empty msaction_table list" in result.output

    def test_upload_msactiontable_invalid_format_error(self, runner):
        """Test error handling when short format is invalid."""
        # Setup mock service with error
        mock_service = self._create_mock_service(
            error="Invalid msactiontable format: Invalid short format syntax"
        )

        # Setup mock container
        mock_container = Mock()
        mock_container.resolve.return_value = mock_service
        mock_service_container = Mock()
        mock_service_container.get_container.return_value = mock_container

        # Execute command
        result = runner.invoke(
            conbus_upload_msactiontable,
            ["0020044991"],
            obj={"container": mock_service_container},
        )

        # Verify error message
        assert "Error:" in result.output
        assert "Invalid msactiontable format" in result.output

    def test_upload_msactiontable_timeout_error(self, runner):
        """Test error handling for timeout."""
        # Setup mock service with error
        mock_service = self._create_mock_service(error="Upload timeout")

        # Setup mock container
        mock_container = Mock()
        mock_container.resolve.return_value = mock_service
        mock_service_container = Mock()
        mock_service_container.get_container.return_value = mock_container

        # Execute command
        result = runner.invoke(
            conbus_upload_msactiontable,
            ["0020044991"],
            obj={"container": mock_service_container},
        )

        # Verify error message
        assert "Error: Upload timeout" in result.output

    def test_upload_msactiontable_nak_error(self, runner):
        """Test error handling for NAK response."""
        # Setup mock service with error
        mock_service = self._create_mock_service(error="Upload failed: NAK received")

        # Setup mock container
        mock_container = Mock()
        mock_container.resolve.return_value = mock_service
        mock_service_container = Mock()
        mock_service_container.get_container.return_value = mock_container

        # Execute command
        result = runner.invoke(
            conbus_upload_msactiontable,
            ["0020044991"],
            obj={"container": mock_service_container},
        )

        # Verify error message
        assert "Error:" in result.output
        assert "NAK received" in result.output

    def test_upload_msactiontable_invalid_serial_number(self, runner):
        """Test error handling for invalid serial number format."""
        # Execute command with invalid serial (too short)
        result = runner.invoke(
            conbus_upload_msactiontable,
            ["123"],
            obj={"container": Mock()},
        )

        # Click should reject invalid serial before service is called
        assert result.exit_code != 0
