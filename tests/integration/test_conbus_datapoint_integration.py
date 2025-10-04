"""Integration tests for Conbus datapoint functionality."""

from unittest.mock import Mock

from click.testing import CliRunner

from xp.cli.main import cli
from xp.models.conbus.conbus_datapoint import ConbusDatapointResponse
from xp.models.telegram.datapoint_type import DataPointType
from xp.models.telegram.system_function import SystemFunction
from xp.services.conbus.conbus_datapoint_service import (
    ConbusDatapointError,
    ConbusDatapointService,
)


class TestConbusDatapointIntegration:
    """Integration tests for conbus datapoint CLI operations."""

    def setup_method(self):
        """Set up test fixtures"""
        self.runner = CliRunner()
        self.valid_serial = "0123450001"
        self.invalid_serial = "invalid"

    def test_conbus_datapoint_all_valid_serial(self):
        """Test querying all datapoints with valid serial number"""

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
        mock_service.query_all_datapoints.return_value = mock_response

        # Setup mock container to resolve ConbusDatapointService
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
        mock_service.query_all_datapoints.assert_called_once_with(
            serial_number=self.valid_serial
        )

        # Check the response content
        assert f'"serial_number": "{self.valid_serial}"' in result.output
        assert '"datapoints"' in result.output
        assert '"MODULE_TYPE": "XP33LED"' in result.output

    def test_conbus_datapoint_all_invalid_serial(self):
        """Test querying all datapoints with invalid serial number"""

        # Mock service that raises error
        mock_service = Mock()
        mock_service.__enter__ = Mock(return_value=mock_service)
        mock_service.__exit__ = Mock(return_value=None)

        mock_service.query_all_datapoints.side_effect = ConbusDatapointError(
            "Invalid serial number"
        )

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

    def test_conbus_datapoint_connection_error(self):
        """Test handling network connection failures"""

        # Mock service that raises connection error
        mock_service = Mock()
        mock_service.__enter__ = Mock(return_value=mock_service)
        mock_service.__exit__ = Mock(return_value=None)

        mock_service.query_all_datapoints.side_effect = ConbusDatapointError(
            "Connection failed"
        )

        # Setup mock container to resolve ConbusDatapointService
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

        # Should handle the error gracefully
        assert "Connection failed" in result.output or "Error" in result.output
        assert result.exit_code != 0

    def test_conbus_datapoint_invalid_response(self):
        """Test handling invalid responses from the server"""

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
        mock_service.query_all_datapoints.return_value = mock_response

        # Setup mock container to resolve ConbusDatapointService
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
        """Test handling when no datapoints are returned"""

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
        mock_service.query_all_datapoints.return_value = mock_response

        # Setup mock container to resolve ConbusDatapointService
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
        """Set up test fixtures"""
        self.valid_serial = "0123450001"

    def test_query_all_datapoints_success(self):
        """Test successful querying of all datapoints"""

        # Mock dependencies
        mock_telegram_service = Mock()
        mock_conbus_service = Mock()

        # Mock successful telegram response for each datapoint type
        mock_reply_telegram = Mock()
        mock_reply_telegram.data = "TEST_VALUE"

        mock_single_response = Mock()
        mock_single_response.success = True
        mock_single_response.datapoint_telegram = mock_reply_telegram

        service = ConbusDatapointService(
            telegram_service=mock_telegram_service, conbus_service=mock_conbus_service
        )

        # Mock the send_telegram method to return successful responses
        service.query_datapoint = Mock(return_value=mock_single_response)

        # Test the query_all_datapoints method
        result = service.query_all_datapoints(self.valid_serial)

        # Assertions
        assert result.success is True
        assert result.serial_number == self.valid_serial
        assert result.system_function == SystemFunction.READ_DATAPOINT
        assert result.datapoints is not None
        assert len(result.datapoints) > 0

        # Should have called send_telegram for each DataPointType
        assert service.query_datapoint.call_count == len(DataPointType)

    def test_query_all_datapoints_partial_failure(self):
        """Test querying datapoints when some datapoints fail"""

        # Mock dependencies
        mock_telegram_service = Mock()
        mock_conbus_service = Mock()

        service = ConbusDatapointService(
            telegram_service=mock_telegram_service, conbus_service=mock_conbus_service
        )

        # Mock send_telegram to return success for some, failure for others
        def mock_send_telegram(datapoint_type, _serial_number):
            if datapoint_type == DataPointType.MODULE_TYPE:
                mock_reply = Mock()
                mock_reply.data_value = "XP33LED"

                mock_response = Mock()
                mock_response.success = True
                mock_response.datapoint_telegram = mock_reply
                return mock_response
            else:
                # Simulate failure for other datapoints
                mock_response = Mock()
                mock_response.success = False
                mock_response.datapoint_telegram = None
                return mock_response

        service.query_datapoint = Mock(side_effect=mock_send_telegram)

        # Test the query_all_datapoints method
        result = service.query_all_datapoints(self.valid_serial)

        # Should still succeed overall but with fewer datapoints
        assert result.success is True
        assert result.serial_number == self.valid_serial
        assert result.datapoints is not None
        assert len(result.datapoints) == 1  # Only MODULE_TYPE succeeded
        assert result.datapoints[0] == {"MODULE_TYPE": "XP33LED"}
