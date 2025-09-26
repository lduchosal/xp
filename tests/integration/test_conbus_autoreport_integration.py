"""Integration tests for Conbus auto report functionality"""

from unittest.mock import Mock, patch
from click.testing import CliRunner

from xp.cli.main import cli
from xp.services.conbus_autoreport_service import (
    ConbusAutoreportService,
    ConbusAutoreportError,
)
from xp.models.conbus_autoreport import ConbusAutoreportResponse


class TestConbusAutoreportIntegration:
    """Integration test cases for Conbus auto report operations"""

    def setup_method(self):
        """Set up test fixtures"""
        self.runner = CliRunner()
        self.valid_serial = "0123450001"
        self.invalid_serial = "invalid"

    @staticmethod
    def _create_mock_conbus_response(
        success=True, serial_number="0123450001", error=None, telegrams=None
    ):
        """Helper to create a properly formed ConbusResponse"""
        if telegrams is None:
            telegrams = [f"<R{serial_number}F18DFA>"] if success else []

        mock_response = Mock()
        mock_response.success = success
        mock_response.sent_telegram = f"<S{serial_number}F04E21PPFG>"
        mock_response.received_telegrams = telegrams
        mock_response.error = error
        mock_response.timestamp = Mock()
        return mock_response

    def _create_mock_conbus_service(self, success=True, ack_response=True):
        """Helper to create a properly mocked ConbusService"""
        mock_conbus_instance = Mock()
        mock_conbus_instance.__enter__ = Mock(return_value=mock_conbus_instance)
        mock_conbus_instance.__exit__ = Mock(return_value=False)

        # Configure response based on test scenario
        if success and ack_response:
            telegrams = ["<R0123450001F18DFH>"]  # ACK response
        elif success and not ack_response:
            telegrams = ["<R0123450001F19DFH>"]  # NAK response
        else:
            telegrams = []

        response = self._create_mock_conbus_response(
            success=success, telegrams=telegrams
        )
        mock_conbus_instance.send_raw_telegram.return_value = response
        return mock_conbus_instance

    @staticmethod
    def _create_mock_datapoint_response(
        success=True, serial_number="0123450001", auto_report_status="AA", error=None
    ):
        """Helper to create a properly formed ConbusDatapointResponse"""
        mock_response = Mock()
        mock_response.success = success
        mock_response.sent_telegram = f"<S{serial_number}F02D21FG>"
        mock_response.received_telegrams = (
            [f"<R{serial_number}F02D21{auto_report_status}FH>"] if success else []
        )
        mock_response.error = error
        mock_response.timestamp = Mock()

        if success:
            mock_response.datapoint_telegram = Mock()
            mock_response.datapoint_telegram.data_value = auto_report_status
        else:
            mock_response.datapoint_telegram = None

        return mock_response

    @patch("xp.cli.commands.conbus_autoreport_commands.ConbusAutoreportService")
    def test_conbus_autoreport_get_valid_serial(self, mock_service_class):
        """Test getting auto report status with valid serial number"""

        # Mock successful response
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.__enter__ = Mock(return_value=mock_service)
        mock_service.__exit__ = Mock(return_value=None)

        mock_response = ConbusAutoreportResponse(
            success=True,
            serial_number=self.valid_serial,
            auto_report_status="AA",
        )
        mock_service.get_autoreport_status.return_value = mock_response

        # Run CLI command
        result = self.runner.invoke(
            cli, ["conbus", "autoreport", "get", self.valid_serial]
        )

        # Assertions
        assert result.exit_code == 0
        assert '"success": true' in result.output
        assert f'"serial_number": "{self.valid_serial}"' in result.output
        assert '"auto_report_status": "AA"' in result.output
        mock_service.get_autoreport_status.assert_called_once_with(self.valid_serial)

    @patch("xp.cli.commands.conbus_autoreport_commands.ConbusAutoreportService")
    def test_conbus_autoreport_set_on_valid_serial(self, mock_service_class):
        """Test setting auto report status to ON with valid serial"""

        # Mock successful response
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.__enter__ = Mock(return_value=mock_service)
        mock_service.__exit__ = Mock(return_value=None)

        mock_response = ConbusAutoreportResponse(
            success=True,
            serial_number=self.valid_serial,
            auto_report_status="on",
            result="ACK",
        )
        mock_service.set_autoreport_status.return_value = mock_response

        # Run CLI command
        result = self.runner.invoke(
            cli, ["conbus", "autoreport", "set", self.valid_serial, "on"]
        )

        # Assertions
        assert result.exit_code == 0
        assert '"success": true' in result.output
        assert '"auto_report_status": "on"' in result.output
        assert '"result": "ACK"' in result.output
        mock_service.set_autoreport_status.assert_called_once_with(
            self.valid_serial, True
        )

    @patch("xp.cli.commands.conbus_autoreport_commands.ConbusAutoreportService")
    def test_conbus_autoreport_set_off_valid_serial(self, mock_service_class):
        """Test setting auto report status to OFF with valid serial"""

        # Mock successful response
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.__enter__ = Mock(return_value=mock_service)
        mock_service.__exit__ = Mock(return_value=None)

        mock_response = ConbusAutoreportResponse(
            success=True,
            serial_number=self.valid_serial,
            auto_report_status="off",
            result="ACK",
        )
        mock_service.set_autoreport_status.return_value = mock_response

        # Run CLI command
        result = self.runner.invoke(
            cli, ["conbus", "autoreport", "set", self.valid_serial, "off"]
        )

        # Assertions
        assert result.exit_code == 0
        assert '"success": true' in result.output
        assert '"auto_report_status": "off"' in result.output
        assert '"result": "ACK"' in result.output
        mock_service.set_autoreport_status.assert_called_once_with(
            self.valid_serial, False
        )

    @patch("xp.cli.commands.conbus_autoreport_commands.ConbusAutoreportService")
    def test_conbus_autoreport_invalid_serial(self, mock_service_class):
        """Test with invalid serial number"""

        # Mock service that raises error
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.__enter__ = Mock(return_value=mock_service)
        mock_service.__exit__ = Mock(return_value=None)

        mock_service.get_autoreport_status.side_effect = ConbusAutoreportError(
            "Invalid serial number"
        )

        # Run CLI command
        result = self.runner.invoke(
            cli, ["conbus", "autoreport", "get", self.invalid_serial]
        )

        # Should handle the error gracefully
        assert result.exit_code != 0
        assert "Invalid serial number" in result.output or "Error" in result.output

    @patch("xp.cli.commands.conbus_autoreport_commands.ConbusAutoreportService")
    def test_conbus_autoreport_connection_error(self, mock_service_class):
        """Test handling network connection failures"""

        # Mock service that raises connection error
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.__enter__ = Mock(return_value=mock_service)
        mock_service.__exit__ = Mock(return_value=None)

        mock_service.get_autoreport_status.side_effect = ConbusAutoreportError(
            "Connection failed"
        )

        # Run CLI command
        result = self.runner.invoke(
            cli, ["conbus", "autoreport", "get", self.valid_serial]
        )

        # Should handle the error gracefully
        assert "Connection failed" in result.output or "Error" in result.output
        assert result.exit_code != 0

    @patch("xp.cli.commands.conbus_autoreport_commands.ConbusAutoreportService")
    def test_conbus_autoreport_invalid_response(self, mock_service_class):
        """Test handling invalid responses from the server"""

        # Mock service with failed response
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.__enter__ = Mock(return_value=mock_service)
        mock_service.__exit__ = Mock(return_value=None)

        mock_response = ConbusAutoreportResponse(
            success=False,
            serial_number=self.valid_serial,
            error="Invalid response from server",
        )
        mock_service.get_autoreport_status.return_value = mock_response

        # Run CLI command
        result = self.runner.invoke(
            cli, ["conbus", "autoreport", "get", self.valid_serial]
        )

        # Should return the failed response
        assert '"success": false' in result.output
        assert result.exit_code == 0  # CLI succeeds but response indicates failure
        assert "Invalid response from server" in result.output


class TestConbusAutoreportService:
    """Unit tests for ConbusAutoreportService functionality."""

    def setup_method(self):
        """Set up test fixtures"""
        self.valid_serial = "0123450001"

    @patch("xp.services.conbus_autoreport_service.ConbusDatapointService")
    def test_get_autoreport_status_success(self, mock_datapoint_service_class):
        """Test successful getting of auto report status"""

        # Mock datapoint service
        mock_datapoint_service = Mock()
        mock_datapoint_service_class.return_value = mock_datapoint_service

        # Create mock datapoint response
        mock_datapoint_response = Mock()
        mock_datapoint_response.success = True
        mock_datapoint_response.datapoint_telegram = Mock()
        mock_datapoint_response.datapoint_telegram.data_value = "AA"
        mock_datapoint_response.sent_telegram = "<S0123450001F02D21FG>"
        mock_datapoint_response.received_telegrams = ["<R0123450001F02D21AAFH>"]
        mock_datapoint_response.timestamp = Mock()

        mock_datapoint_service.query_datapoint.return_value = mock_datapoint_response

        # Test the service
        result = ConbusAutoreportService().get_autoreport_status(self.valid_serial)

        # Assertions
        assert result.success is True
        assert result.serial_number == self.valid_serial
        assert result.auto_report_status == "AA"
        assert result.error is None

        # Verify datapoint service was called correctly
        from xp.models.datapoint_type import DataPointType

        mock_datapoint_service.query_datapoint.assert_called_once_with(
            DataPointType.AUTO_REPORT_STATUS, self.valid_serial
        )

    @patch("xp.services.conbus_autoreport_service.ConbusService")
    def test_set_autoreport_status_on_success(self, mock_conbus_service_class):
        """Test successful setting of auto report status to ON"""

        # Mock conbus service
        mock_conbus_service = Mock()
        mock_conbus_service_class.return_value = mock_conbus_service
        mock_conbus_service.__enter__ = Mock(return_value=mock_conbus_service)
        mock_conbus_service.__exit__ = Mock(return_value=None)

        # Create mock response with ACK
        mock_response = Mock()
        mock_response.success = True
        mock_response.received_telegrams = ["<R0123450001F18DFH>"]  # ACK
        mock_response.error = None
        mock_response.timestamp = Mock()

        mock_conbus_service.send_raw_telegram.return_value = mock_response

        # Test the service
        result = ConbusAutoreportService().set_autoreport_status(
            self.valid_serial, True
        )

        # Assertions
        assert result.success is True
        assert result.serial_number == self.valid_serial
        assert result.auto_report_status == "on"
        assert result.result == "ACK"
        assert result.error is None

        # Verify telegram was sent correctly
        mock_conbus_service.send_raw_telegram.assert_called_once()
        sent_telegram = mock_conbus_service.send_raw_telegram.call_args[0][0]
        assert "F04E21PP" in sent_telegram  # Should contain PP for ON

    @patch("xp.services.conbus_autoreport_service.ConbusService")
    def test_set_autoreport_status_off_success(self, mock_conbus_service_class):
        """Test successful setting of auto report status to OFF"""

        # Mock conbus service
        mock_conbus_service = Mock()
        mock_conbus_service_class.return_value = mock_conbus_service
        mock_conbus_service.__enter__ = Mock(return_value=mock_conbus_service)
        mock_conbus_service.__exit__ = Mock(return_value=None)

        # Create mock response with ACK
        mock_response = Mock()
        mock_response.success = True
        mock_response.received_telegrams = ["<R0123450001F18DFH>"]  # ACK
        mock_response.error = None
        mock_response.timestamp = Mock()

        mock_conbus_service.send_raw_telegram.return_value = mock_response

        # Test the service
        result = ConbusAutoreportService().set_autoreport_status(
            self.valid_serial, False
        )

        # Assertions
        assert result.success is True
        assert result.serial_number == self.valid_serial
        assert result.auto_report_status == "off"
        assert result.result == "ACK"
        assert result.error is None

        # Verify telegram was sent correctly
        mock_conbus_service.send_raw_telegram.assert_called_once()
        sent_telegram = mock_conbus_service.send_raw_telegram.call_args[0][0]
        assert "F04E21AA" in sent_telegram  # Should contain AA for OFF

    def test_service_context_manager(self):
        """Test service can be used as context manager"""
        service = ConbusAutoreportService("test.yml")

        with service as s:
            assert s is service
