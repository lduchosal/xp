"""Unit tests for ConbusScanService."""

from unittest.mock import Mock

import pytest

from xp.models import ConbusResponse
from xp.services.conbus.conbus_scan_service import ConbusScanService


class TestConbusScanService:
    """Unit tests for ConbusScanService functionality."""

    @pytest.fixture
    def mock_conbus_protocol(self):
        """Create a mock ConbusEventProtocol."""
        mock_protocol = Mock()
        mock_protocol.on_connection_made = Mock()
        mock_protocol.on_telegram_sent = Mock()
        mock_protocol.on_telegram_received = Mock()
        mock_protocol.on_timeout = Mock()
        mock_protocol.on_failed = Mock()
        mock_protocol.on_connection_made.connect = Mock()
        mock_protocol.on_telegram_sent.connect = Mock()
        mock_protocol.on_telegram_received.connect = Mock()
        mock_protocol.on_timeout.connect = Mock()
        mock_protocol.on_failed.connect = Mock()
        mock_protocol.on_connection_made.disconnect = Mock()
        mock_protocol.on_telegram_sent.disconnect = Mock()
        mock_protocol.on_telegram_received.disconnect = Mock()
        mock_protocol.on_timeout.disconnect = Mock()
        mock_protocol.on_failed.disconnect = Mock()
        mock_protocol.sendFrame = Mock()
        mock_protocol.start_reactor = Mock()
        mock_protocol.stop_reactor = Mock()
        mock_protocol.timeout_seconds = 0.25
        return mock_protocol

    @pytest.fixture
    def service(self, mock_conbus_protocol):
        """Create service instance with test dependencies."""
        return ConbusScanService(
            conbus_protocol=mock_conbus_protocol,
        )

    def test_service_initialization(self, service, mock_conbus_protocol):
        """Test service can be initialized with required dependencies."""
        assert service.serial_number == ""
        assert service.function_code == ""
        assert service.datapoint_value == -1
        assert service.service_response.success is False
        # Verify signal connections
        mock_conbus_protocol.on_connection_made.connect.assert_called_once()
        mock_conbus_protocol.on_telegram_sent.connect.assert_called_once()
        mock_conbus_protocol.on_telegram_received.connect.assert_called_once()
        mock_conbus_protocol.on_timeout.connect.assert_called_once()
        mock_conbus_protocol.on_failed.connect.assert_called_once()

    def test_service_context_manager(self, service, mock_conbus_protocol):
        """Test service can be used as context manager."""
        # Set some state
        service.serial_number = "0012345678"
        service.function_code = "02"
        service.datapoint_value = 5

        with service as s:
            assert s is service
            # State should be reset
            assert s.serial_number == ""
            assert s.function_code == ""
            assert s.datapoint_value == -1
        # Signals should be disconnected after exit
        mock_conbus_protocol.on_connection_made.disconnect.assert_called_once()
        mock_conbus_protocol.on_telegram_sent.disconnect.assert_called_once()
        mock_conbus_protocol.on_telegram_received.disconnect.assert_called_once()
        mock_conbus_protocol.on_timeout.disconnect.assert_called_once()
        mock_conbus_protocol.on_failed.disconnect.assert_called_once()
        mock_conbus_protocol.stop_reactor.assert_called_once()

    def test_connection_made(self, service, mock_conbus_protocol):
        """Test connection_made starts scan."""
        service.serial_number = "0012345678"
        service.function_code = "02"

        service.connection_made()

        # Should send first telegram (datapoint 00)
        mock_conbus_protocol.sendFrame.assert_called_once()
        call_args = mock_conbus_protocol.sendFrame.call_args[0][0]
        assert call_args == b"S0012345678F02D00"

    def test_scan_next_datacode_continues(self, service, mock_conbus_protocol):
        """Test scan_next_datacode sends telegram and continues."""
        service.serial_number = "0012345678"
        service.function_code = "02"
        service.datapoint_value = 5

        result = service.scan_next_datacode()

        assert result is True
        mock_conbus_protocol.sendFrame.assert_called_once()
        call_args = mock_conbus_protocol.sendFrame.call_args[0][0]
        assert call_args == b"S0012345678F02D06"

    def test_scan_next_datacode_completes(self, service):
        """Test scan_next_datacode emits on_finish when complete."""
        finish_mock = Mock()
        service.on_finish.connect(finish_mock)
        service.datapoint_value = 99

        result = service.scan_next_datacode()

        assert result is False
        finish_mock.assert_called_once_with(service.service_response)

    def test_telegram_sent(self, service):
        """Test telegram_sent callback updates service response."""
        telegram = "<S0012345678F02D05FN>"

        service.telegram_sent(telegram)

        assert service.service_response.success is True
        assert service.service_response.sent_telegrams == [telegram]

    def test_telegram_received(self, service, mock_conbus_protocol):
        """Test telegram_received callback updates response and emits signal."""
        from xp.models.protocol.conbus_protocol import TelegramReceivedEvent

        progress_mock = Mock()
        service.on_progress.connect(progress_mock)

        telegram_event = TelegramReceivedEvent.model_construct(
            protocol=mock_conbus_protocol,
            frame="<R0012345678F02D05XX>",
            telegram="R0012345678F02D05XX",
            payload="R0012345678F02D05",
            telegram_type="R",
            serial_number="0012345678",
            checksum="XX",
            checksum_valid=True,
        )

        service.telegram_received(telegram_event)

        assert service.service_response.received_telegrams == ["<R0012345678F02D05XX>"]
        progress_mock.assert_called_once_with("<R0012345678F02D05XX>")

    def test_timeout(self, service, mock_conbus_protocol):
        """Test timeout callback scans next datacode."""
        service.serial_number = "0012345678"
        service.function_code = "02"
        service.datapoint_value = 5

        service.timeout()

        # Should have sent next telegram
        mock_conbus_protocol.sendFrame.assert_called_once()

    def test_failed(self, service):
        """Test failed callback emits on_finish signal with error."""
        finish_mock = Mock()
        service.on_finish.connect(finish_mock)

        service.failed("Connection timeout")

        assert service.service_response.success is False
        assert service.service_response.error == "Connection timeout"
        finish_mock.assert_called_once_with(service.service_response)

    def test_scan_module(self, service, mock_conbus_protocol):
        """Test scan_module sets up scan parameters."""
        service.scan_module(
            serial_number="0012345678",
            function_code="02",
            timeout_seconds=0.5,
        )

        assert service.serial_number == "0012345678"
        assert service.function_code == "02"
        assert mock_conbus_protocol.timeout_seconds == 0.5

    def test_set_timeout(self, service, mock_conbus_protocol):
        """Test set_timeout delegates to protocol."""
        service.set_timeout(5.0)

        assert mock_conbus_protocol.timeout_seconds == 5.0

    def test_start_reactor(self, service, mock_conbus_protocol):
        """Test start_reactor delegates to protocol."""
        service.start_reactor()

        mock_conbus_protocol.start_reactor.assert_called_once()

    def test_stop_reactor(self, service, mock_conbus_protocol):
        """Test stop_reactor delegates to protocol."""
        service.stop_reactor()

        mock_conbus_protocol.stop_reactor.assert_called_once()

    def test_on_progress_signal(self, service):
        """Test on_progress signal can be connected and emitted."""
        progress_mock = Mock()
        service.on_progress.connect(progress_mock)

        service.on_progress.emit("test progress")

        progress_mock.assert_called_once_with("test progress")

    def test_on_finish_signal(self, service):
        """Test on_finish signal can be connected and emitted."""
        from datetime import datetime

        finish_mock = Mock()
        service.on_finish.connect(finish_mock)

        response = ConbusResponse(
            success=True,
            serial_number="0012345678",
            sent_telegrams=[],
            received_telegrams=[],
            timestamp=datetime.now(),
        )
        service.on_finish.emit(response)

        finish_mock.assert_called_once_with(response)
