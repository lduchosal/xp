"""Integration tests for Conbus datapoint functionality."""

from unittest.mock import Mock

from click.testing import CliRunner

from xp.cli.main import cli
from xp.models.conbus.conbus_datapoint import ConbusDatapointResponse
from xp.models.telegram.system_function import SystemFunction
from xp.services.conbus.conbus_datapoint_queryall_service import (
    ConbusDatapointQueryAllService,
)
from xp.services.conbus.conbus_datapoint_service import (
    ConbusDatapointService,
)


class TestConbusDatapointIntegration:
    """Integration tests for conbus datapoint CLI operations."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.valid_serial = "0123450001"
        self.invalid_serial = "invalid"

    def test_conbus_datapoint_all_valid_serial(self):
        """Test querying all datapoints with valid serial number."""
        # Mock successful response
        mock_service = Mock()
        mock_service.__enter__ = Mock(return_value=mock_service)
        mock_service.__exit__ = Mock(return_value=None)

        mock_response = ConbusDatapointResponse(
            success=True,
            serial_number=self.valid_serial,
            system_function=SystemFunction.READ_DATAPOINT,
            datapoints=[
                {"MODULE_TYPE": "XP33LED"},
                {"HW_VERSION": "XP33LED_HW_VER1"},
                {"SW_VERSION": "XP33LED_V0.04.01"},
                {"AUTO_REPORT_STATUS": "AA"},
                {"MODULE_STATE": "OFF"},
                {"MODULE_OUTPUT_STATE": "xxxxx000"},
            ],
        )

        # Make the mock service call the callback immediately
        def mock_query_all_datapoints(
            serial_number, finish_callback, progress_callback
        ):
            """Test helper function.

            Args:
                serial_number: Serial number of the module.
                finish_callback: Callback when finished.
                progress_callback: Callback for progress updates.
            """
            finish_callback(mock_response)

        mock_service.query_all_datapoints.side_effect = mock_query_all_datapoints

        # Setup mock container to resolve ConbusDatapointQueryAllService
        mock_container = Mock()
        mock_container.resolve.return_value = mock_service
        mock_service_container = Mock()
        mock_service_container.get_container.return_value = mock_container

        # Run CLI command
        result = self.runner.invoke(
            cli,
            ["conbus", "datapoint", "all", self.valid_serial],
            obj={"container": mock_service_container},
        )

        # Debug output
        print(f"Exit code: {result.exit_code}")
        print(f"Output: {result.output}")
        print(f"Exception: {result.exception}")
        print(f"Mock service calls: {mock_service.method_calls}")

        # Assertions
        assert '"success": true' in result.output
        assert result.exit_code == 0
        assert mock_service.query_all_datapoints.called

        # Check the response content
        assert f'"serial_number": "{self.valid_serial}"' in result.output
        assert '"datapoints"' in result.output
        assert '"MODULE_TYPE": "XP33LED"' in result.output

    def test_conbus_datapoint_all_invalid_serial(self):
        """Test querying all datapoints with invalid serial number."""
        # Mock service that raises error
        mock_service = Mock()
        mock_service.__enter__ = Mock(return_value=mock_service)
        mock_service.__exit__ = Mock(return_value=None)

        # Setup mock container to resolve ConbusDatapointService
        mock_container = Mock()
        mock_container.resolve.return_value = mock_service
        mock_service_container = Mock()
        mock_service_container.get_container.return_value = mock_container

        # Run CLI command
        result = self.runner.invoke(
            cli,
            ["conbus", "datapoint", "all", self.invalid_serial],
            obj={"container": mock_service_container},
        )

        # Should handle the error gracefully
        assert result.exit_code != 0
        assert "Invalid serial number" in result.output or "Error" in result.output

    def test_conbus_datapoint_invalid_response(self):
        """Test handling invalid responses from the server."""
        # Mock service with failed response
        mock_service = Mock()
        mock_service.__enter__ = Mock(return_value=mock_service)
        mock_service.__exit__ = Mock(return_value=None)

        mock_response = ConbusDatapointResponse(
            success=False,
            serial_number=self.valid_serial,
            error="Invalid response from server",
            datapoints=[],
        )

        # Make the mock service call the callback immediately
        def mock_query_all_datapoints(
            serial_number, finish_callback, progress_callback
        ):
            """Test helper function.

            Args:
                serial_number: Serial number of the module.
                finish_callback: Callback when finished.
                progress_callback: Callback for progress updates.
            """
            finish_callback(mock_response)

        mock_service.query_all_datapoints.side_effect = mock_query_all_datapoints

        # Setup mock container to resolve ConbusDatapointQueryAllService
        mock_container = Mock()
        mock_container.resolve.return_value = mock_service
        mock_service_container = Mock()
        mock_service_container.get_container.return_value = mock_container

        # Run CLI command
        result = self.runner.invoke(
            cli,
            ["conbus", "datapoint", "all", self.valid_serial],
            obj={"container": mock_service_container},
        )

        # Should return the failed response
        assert '"success": false' in result.output
        assert result.exit_code == 0  # CLI succeeds but response indicates failure
        assert "Invalid response from server" in result.output

    def test_conbus_datapoint_empty_datapoints(self):
        """Test handling when no datapoints are returned."""
        # Mock service with successful but empty response
        mock_service = Mock()
        mock_service.__enter__ = Mock(return_value=mock_service)
        mock_service.__exit__ = Mock(return_value=None)

        mock_response = ConbusDatapointResponse(
            success=True,
            serial_number=self.valid_serial,
            system_function=SystemFunction.READ_DATAPOINT,
            datapoints=[],
        )

        # Make the mock service call the callback immediately
        def mock_query_all_datapoints(
            serial_number, finish_callback, progress_callback
        ):
            """Test helper function.

            Args:
                serial_number: Serial number of the module.
                finish_callback: Callback when finished.
                progress_callback: Callback for progress updates.
            """
            finish_callback(mock_response)

        mock_service.query_all_datapoints.side_effect = mock_query_all_datapoints

        # Setup mock container to resolve ConbusDatapointQueryAllService
        mock_container = Mock()
        mock_container.resolve.return_value = mock_service
        mock_service_container = Mock()
        mock_service_container.get_container.return_value = mock_container

        # Run CLI command
        result = self.runner.invoke(
            cli,
            ["conbus", "datapoint", "all", self.valid_serial],
            obj={"container": mock_service_container},
        )

        # Should succeed with empty datapoints
        assert '"success": true' in result.output
        assert result.exit_code == 0
        assert f'"serial_number": "{self.valid_serial}"' in result.output
        # datapoints field should not be included when empty
        assert '"datapoints"' not in result.output


class TestConbusDatapointService:
    """Unit tests for ConbusDatapointService functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.valid_serial = "0123450001"
        self.mock_cli_config = Mock()
        self.mock_reactor = Mock()
        self.mock_telegram_service = Mock()

    def test_service_initialization(self):
        """Test service can be initialized with required dependencies."""
        service = ConbusDatapointService(
            telegram_service=self.mock_telegram_service,
            cli_config=self.mock_cli_config,
            reactor=self.mock_reactor,
        )

        assert service.telegram_service == self.mock_telegram_service
        assert service.serial_number == ""
        assert service.datapoint_type is None
        assert service.datapoint_finished_callback is None
        assert service.service_response.success is False

    def test_service_context_manager(self):
        """Test service can be used as context manager."""
        service = ConbusDatapointService(
            telegram_service=self.mock_telegram_service,
            cli_config=self.mock_cli_config,
            reactor=self.mock_reactor,
        )

        with service as s:
            assert s is service


class TestConbusDatapointQueryAllService:
    """Unit tests for ConbusDatapointQueryAllService functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.valid_serial = "0123450001"
        self.mock_cli_config = Mock()
        self.mock_reactor = Mock()
        self.mock_telegram_service = Mock()

    def test_service_initialization(self):
        """Test service can be initialized with required dependencies."""
        service = ConbusDatapointQueryAllService(
            telegram_service=self.mock_telegram_service,
            cli_config=self.mock_cli_config,
            reactor=self.mock_reactor,
        )

        assert service.telegram_service == self.mock_telegram_service
        assert service.cli_config == self.mock_cli_config.conbus
        assert service.reactor == self.mock_reactor

    def test_service_context_manager(self):
        """Test service can be used as context manager."""
        service = ConbusDatapointQueryAllService(
            telegram_service=self.mock_telegram_service,
            cli_config=self.mock_cli_config,
            reactor=self.mock_reactor,
        )

        with service as s:
            assert s is service
