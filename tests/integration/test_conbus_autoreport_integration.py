"""Integration tests for Conbus auto report functionality"""

from unittest.mock import Mock

from click.testing import CliRunner

from xp.cli.main import cli
from xp.models.conbus.conbus_autoreport import ConbusAutoreportResponse
from xp.services.conbus.conbus_autoreport_get_service import (
    ConbusAutoreportGetService,
)
from xp.services.conbus.conbus_autoreport_set_service import (
    ConbusAutoreportSetService,
)


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

    def test_conbus_autoreport_get_valid_serial(self):
        """Test getting auto report status with valid serial number"""

        # Mock successful response
        mock_service = Mock()
        mock_service.__enter__ = Mock(return_value=mock_service)
        mock_service.__exit__ = Mock(return_value=None)

        mock_response = ConbusAutoreportResponse(
            success=True,
            serial_number=self.valid_serial,
            auto_report_status="AA",
        )

        # Make the mock service call the callback immediately
        def mock_get_autoreport_status(serial_number, finish_callback):
            finish_callback(mock_response)

        mock_service.get_autoreport_status.side_effect = mock_get_autoreport_status

        # Mock container
        mock_container_instance = Mock()
        mock_container_instance.resolve.return_value = mock_service
        mock_container = Mock()
        mock_container.get_container.return_value = mock_container_instance

        # Run CLI command with mocked container
        result = self.runner.invoke(
            cli,
            ["conbus", "autoreport", "get", self.valid_serial],
            obj={"container": mock_container},
        )

        # Assertions
        assert result.exit_code == 0
        assert '"success": true' in result.output
        assert f'"serial_number": "{self.valid_serial}"' in result.output
        assert '"auto_report_status": "AA"' in result.output
        assert mock_service.get_autoreport_status.called

    def test_conbus_autoreport_set_on_valid_serial(self):
        """Test setting auto report status to ON with valid serial"""

        # Mock successful response
        mock_service = Mock()
        mock_service.__enter__ = Mock(return_value=mock_service)
        mock_service.__exit__ = Mock(return_value=None)

        mock_response = ConbusAutoreportResponse(
            success=True,
            serial_number=self.valid_serial,
            auto_report_status="on",
            result="ACK",
        )

        # Make the mock service call the callback immediately
        def mock_set_autoreport_status(serial_number, status, status_callback):
            status_callback(mock_response)

        mock_service.set_autoreport_status.side_effect = mock_set_autoreport_status

        # Mock container
        mock_container_instance = Mock()
        mock_container_instance.resolve.return_value = mock_service
        mock_container = Mock()
        mock_container.get_container.return_value = mock_container_instance

        # Run CLI command with mocked container
        result = self.runner.invoke(
            cli,
            ["conbus", "autoreport", "set", self.valid_serial, "on"],
            obj={"container": mock_container},
        )

        # Assertions
        assert result.exit_code == 0
        assert '"success": true' in result.output
        assert '"auto_report_status": "on"' in result.output
        assert '"result": "ACK"' in result.output
        assert mock_service.set_autoreport_status.called

    def test_conbus_autoreport_set_off_valid_serial(self):
        """Test setting auto report status to OFF with valid serial"""

        # Mock successful response
        mock_service = Mock()
        mock_service.__enter__ = Mock(return_value=mock_service)
        mock_service.__exit__ = Mock(return_value=None)

        mock_response = ConbusAutoreportResponse(
            success=True,
            serial_number=self.valid_serial,
            auto_report_status="off",
            result="ACK",
        )

        # Make the mock service call the callback immediately
        def mock_set_autoreport_status(serial_number, status, status_callback):
            status_callback(mock_response)

        mock_service.set_autoreport_status.side_effect = mock_set_autoreport_status

        # Mock container
        mock_container_instance = Mock()
        mock_container_instance.resolve.return_value = mock_service
        mock_container = Mock()
        mock_container.get_container.return_value = mock_container_instance

        # Run CLI command with mocked container
        result = self.runner.invoke(
            cli,
            ["conbus", "autoreport", "set", self.valid_serial, "off"],
            obj={"container": mock_container},
        )

        # Assertions
        assert result.exit_code == 0
        assert '"success": true' in result.output
        assert '"auto_report_status": "off"' in result.output
        assert '"result": "ACK"' in result.output
        assert mock_service.set_autoreport_status.called

    def test_conbus_autoreport_invalid_response(self):
        """Test handling invalid responses from the server"""

        # Mock service with failed response
        mock_service = Mock()
        mock_service.__enter__ = Mock(return_value=mock_service)
        mock_service.__exit__ = Mock(return_value=None)

        mock_response = ConbusAutoreportResponse(
            success=False,
            serial_number=self.valid_serial,
            error="Invalid response from server",
        )

        # Make the mock service call the callback immediately
        def mock_get_autoreport_status(serial_number, finish_callback):
            finish_callback(mock_response)

        mock_service.get_autoreport_status.side_effect = mock_get_autoreport_status

        # Mock container
        mock_container_instance = Mock()
        mock_container_instance.resolve.return_value = mock_service
        mock_container = Mock()
        mock_container.get_container.return_value = mock_container_instance

        # Run CLI command with mocked container
        result = self.runner.invoke(
            cli,
            ["conbus", "autoreport", "get", self.valid_serial],
            obj={"container": mock_container},
        )

        # Should return the failed response
        assert '"success": false' in result.output
        assert result.exit_code == 0  # CLI succeeds but response indicates failure
        assert "Invalid response from server" in result.output


class TestConbusAutoreportGetService:
    """Unit tests for ConbusAutoreportGetService functionality."""

    def setup_method(self):
        """Set up test fixtures"""
        self.valid_serial = "0123450001"
        self.mock_cli_config = Mock()
        self.mock_reactor = Mock()
        self.mock_telegram_service = Mock()

    def test_service_initialization(self):
        """Test service can be initialized with required dependencies"""
        service = ConbusAutoreportGetService(
            telegram_service=self.mock_telegram_service,
            cli_config=self.mock_cli_config,
            reactor=self.mock_reactor,
        )

        assert service.telegram_service == self.mock_telegram_service
        assert service.serial_number == ""
        assert service.finish_callback is None
        assert service.service_response.success is False

    def test_service_context_manager(self):
        """Test service can be used as context manager"""
        service = ConbusAutoreportGetService(
            telegram_service=self.mock_telegram_service,
            cli_config=self.mock_cli_config,
            reactor=self.mock_reactor,
        )

        with service as s:
            assert s is service


class TestConbusAutoreportSetService:
    """Unit tests for ConbusAutoreportSetService functionality."""

    def setup_method(self):
        """Set up test fixtures"""
        self.valid_serial = "0123450001"
        self.mock_cli_config = Mock()
        self.mock_reactor = Mock()

    def test_service_initialization(self):
        """Test service can be initialized with required dependencies"""
        service = ConbusAutoreportSetService(
            cli_config=self.mock_cli_config,
            reactor=self.mock_reactor,
        )

        assert service.serial_number == ""
        assert service.status is False
        assert service.finish_callback is None
        assert service.service_response.success is False

    def test_service_context_manager(self):
        """Test service can be used as context manager"""
        service = ConbusAutoreportSetService(
            cli_config=self.mock_cli_config,
            reactor=self.mock_reactor,
        )

        with service as s:
            assert s is service
