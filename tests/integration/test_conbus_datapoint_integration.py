"""Integration tests for Conbus datapoint functionality."""

from unittest.mock import Mock, patch
from click.testing import CliRunner

from xp.cli.main import cli
from xp.models.conbus_datapoint import ConbusDatapointResponse
from xp.models.datapoint_type import DataPointType
from xp.models.system_function import SystemFunction
from xp.services.conbus_datapoint_service import (
    ConbusDatapointService,
    ConbusDatapointError,
)


class TestConbusDatapointIntegration:
    """Integration tests for conbus datapoint CLI operations."""

    def setup_method(self):
        """Set up test fixtures"""
        self.runner = CliRunner()
        self.valid_serial = "0123450001"
        self.invalid_serial = "invalid"

    @patch("xp.cli.commands.conbus_datapoint_commands.ConbusDatapointService")
    def test_conbus_datapoint_all_valid_serial(self, mock_service_class):
        """Test querying all datapoints with valid serial number"""

        # Mock successful response
        mock_service = Mock()
        mock_service_class.return_value = mock_service
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

        # Run CLI command
        result = self.runner.invoke(
            cli, ["conbus", "datapoint", "all", self.valid_serial]
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

    @patch("xp.cli.commands.conbus_datapoint_commands.ConbusDatapointService")
    def test_conbus_datapoint_all_invalid_serial(self, mock_service_class):
        """Test querying all datapoints with invalid serial number"""

        # Mock service that raises error
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.__enter__ = Mock(return_value=mock_service)
        mock_service.__exit__ = Mock(return_value=None)

        mock_service.query_all_datapoints.side_effect = ConbusDatapointError(
            "Invalid serial number"
        )

        # Run CLI command
        result = self.runner.invoke(
            cli, ["conbus", "datapoint", "all", self.invalid_serial]
        )

        # Should handle the error gracefully
        assert result.exit_code != 0
        assert "Invalid serial number" in result.output or "Error" in result.output

    @patch("xp.cli.commands.conbus_datapoint_commands.ConbusDatapointService")
    def test_conbus_datapoint_connection_error(self, mock_service_class):
        """Test handling network connection failures"""

        # Mock service that raises connection error
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.__enter__ = Mock(return_value=mock_service)
        mock_service.__exit__ = Mock(return_value=None)

        mock_service.query_all_datapoints.side_effect = ConbusDatapointError(
            "Connection failed"
        )

        # Run CLI command
        result = self.runner.invoke(
            cli, ["conbus", "datapoint", "all", self.valid_serial]
        )

        # Should handle the error gracefully
        assert "Connection failed" in result.output or "Error" in result.output
        assert result.exit_code != 0

    @patch("xp.cli.commands.conbus_datapoint_commands.ConbusDatapointService")
    def test_conbus_datapoint_invalid_response(self, mock_service_class):
        """Test handling invalid responses from the server"""

        # Mock service with failed response
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.__enter__ = Mock(return_value=mock_service)
        mock_service.__exit__ = Mock(return_value=None)

        mock_response = ConbusDatapointResponse(
            success=False,
            serial_number=self.valid_serial,
            error="Invalid response from server",
            datapoints=[],
        )
        mock_service.query_all_datapoints.return_value = mock_response

        # Run CLI command
        result = self.runner.invoke(
            cli, ["conbus", "datapoint", "all", self.valid_serial]
        )

        # Should return the failed response
        assert '"success": false' in result.output
        assert result.exit_code == 0  # CLI succeeds but response indicates failure
        assert "Invalid response from server" in result.output

    @patch("xp.cli.commands.conbus_datapoint_commands.ConbusDatapointService")
    def test_conbus_datapoint_empty_datapoints(self, mock_service_class):
        """Test handling when no datapoints are returned"""

        # Mock service with successful but empty response
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.__enter__ = Mock(return_value=mock_service)
        mock_service.__exit__ = Mock(return_value=None)

        mock_response = ConbusDatapointResponse(
            success=True,
            serial_number=self.valid_serial,
            system_function=SystemFunction.READ_DATAPOINT,
            datapoints=[],
        )
        mock_service.query_all_datapoints.return_value = mock_response

        # Run CLI command
        result = self.runner.invoke(
            cli, ["conbus", "datapoint", "all", self.valid_serial]
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

    @patch("xp.services.conbus_datapoint_service.ConbusService")
    @patch("xp.services.conbus_datapoint_service.TelegramService")
    def test_query_all_datapoints_success(
        self, mock_telegram_service, mock_conbus_service
    ):
        """Test successful querying of all datapoints"""

        # Mock dependencies
        mock_conbus = Mock()
        mock_conbus_service.return_value = mock_conbus
        mock_telegram = Mock()
        mock_telegram_service.return_value = mock_telegram

        # Mock successful telegram response for each datapoint type
        mock_reply_telegram = Mock()
        mock_reply_telegram.data = "TEST_VALUE"

        mock_single_response = Mock()
        mock_single_response.success = True
        mock_single_response.datapoint_telegram = mock_reply_telegram

        service = ConbusDatapointService()

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

        service = ConbusDatapointService()

        # Mock send_telegram to return success for some, failure for others
        def mock_send_telegram(datapoint_type, _serial_number):
            if datapoint_type == DataPointType.ERROR_CODE:
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
        assert len(result.datapoints) == 1  # Only ERROR_CODE succeeded
        assert result.datapoints[0] == {"ERROR_CODE": "XP33LED"}
