# Copyright (c) 2025 ldvchosal
"""Unit tests for ConbusDiscoverService."""

from unittest.mock import Mock, call

import pytest

from xp.models.protocol.conbus_protocol import TelegramReceivedEvent
from xp.models.telegram.datapoint_type import DataPointType
from xp.models.telegram.system_function import SystemFunction
from xp.models.telegram.telegram_type import TelegramType
from xp.services.conbus.conbus_discover_service import ConbusDiscoverService

# Serial number used by the fake discovered module in these tests.
SERIAL_NUMBER = "0012345011"

# Module type code for XP24 in MODULE_TYPE_REGISTRY.
XP24_MODULE_TYPE_CODE = 7

# Timeout value used to exercise set_timeout delegation.
TIMEOUT_SECONDS = 2.5

# One on_device_discovered emission per step: discovery, type, type code.
EXPECTED_DEVICE_UPDATE_EVENTS = 3


class TestConbusDiscoverService:
    """Unit tests for ConbusDiscoverService functionality."""

    @pytest.fixture
    def mock_conbus_protocol(self) -> Mock:
        """Create a mock ConbusEventProtocol.

        Returns:
            A mock ConbusEventProtocol.

        """
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
        mock_protocol.send_telegram = Mock()
        mock_protocol.set_event_loop = Mock()
        mock_protocol.start_reactor = Mock()
        mock_protocol.stop_reactor = Mock()
        mock_protocol.timeout_seconds = 0.25
        return mock_protocol

    @pytest.fixture
    def service(self, mock_conbus_protocol: Mock) -> ConbusDiscoverService:
        """Create service instance with test dependencies.

        Returns:
            Service instance with test dependencies.

        """
        return ConbusDiscoverService(conbus_protocol=mock_conbus_protocol)

    @staticmethod
    def make_event(mock_conbus_protocol: Mock, payload: str) -> TelegramReceivedEvent:
        """Build a TelegramReceivedEvent for a reply payload.

        Args:
            mock_conbus_protocol: Mock protocol carried by the event.
            payload: Telegram payload (frame without checksum and brackets).

        Returns:
            TelegramReceivedEvent with a valid checksum.

        """
        return TelegramReceivedEvent.model_construct(
            protocol=mock_conbus_protocol,
            frame=f"<{payload}FM>",
            telegram=f"{payload}FM",
            payload=payload,
            telegram_type=payload[0],
            serial_number=payload[1:11],
            checksum="FM",
            checksum_valid=True,
        )

    def test_service_initialization(
        self, service: ConbusDiscoverService, mock_conbus_protocol: Mock
    ) -> None:
        """Test service can be initialized with required dependencies."""
        assert service.discovered_device_result.success is False
        assert service.discovered_device_result.discovered_devices is None
        # Verify signal connections
        mock_conbus_protocol.on_connection_made.connect.assert_called_once()
        mock_conbus_protocol.on_telegram_sent.connect.assert_called_once()
        mock_conbus_protocol.on_telegram_received.connect.assert_called_once()
        mock_conbus_protocol.on_timeout.connect.assert_called_once()
        mock_conbus_protocol.on_failed.connect.assert_called_once()

    def test_connection_made_sends_broadcast_discover(
        self, service: ConbusDiscoverService, mock_conbus_protocol: Mock
    ) -> None:
        """Test connection_made sends a broadcast discovery telegram."""
        service.connection_made()

        mock_conbus_protocol.send_telegram.assert_called_once_with(
            telegram_type=TelegramType.SYSTEM,
            serial_number="0000000000",
            system_function=SystemFunction.DISCOVERY,
            data_value="00",
        )

    def test_telegram_sent(self, service: ConbusDiscoverService) -> None:
        """Test telegram_sent records the sent telegram in the result."""
        telegram = "<S0000000000F01D00FA>"

        service.telegram_sent(telegram)

        assert service.discovered_device_result.sent_telegram == telegram

    def test_telegram_received_discovery_reply(
        self, service: ConbusDiscoverService, mock_conbus_protocol: Mock
    ) -> None:
        """Test a discovery reply registers the device and queries its type."""
        progress_mock = Mock()
        discovered_mock = Mock()
        service.on_progress.connect(progress_mock)
        service.on_device_discovered.connect(discovered_mock)
        event = self.make_event(mock_conbus_protocol, f"R{SERIAL_NUMBER}F01D")

        service.telegram_received(event)

        assert service.discovered_device_result.received_telegrams == [event.frame]
        assert service.discovered_device_result.discovered_devices == [
            {
                "serial_number": SERIAL_NUMBER,
                "module_type": None,
                "module_type_code": None,
                "module_type_name": None,
            }
        ]
        discovered_mock.assert_called_once()
        progress_mock.assert_called_once_with(SERIAL_NUMBER)
        # Module type query is sent for the discovered serial number
        mock_conbus_protocol.send_telegram.assert_called_once_with(
            telegram_type=TelegramType.SYSTEM,
            serial_number=SERIAL_NUMBER,
            system_function=SystemFunction.READ_DATAPOINT,
            data_value=DataPointType.MODULE_TYPE.value,
        )

    def test_telegram_received_module_type_reply(
        self, service: ConbusDiscoverService, mock_conbus_protocol: Mock
    ) -> None:
        """Test a module type reply updates the device and queries the code."""
        discovered_mock = Mock()
        service.on_device_discovered.connect(discovered_mock)
        service.telegram_received(
            self.make_event(mock_conbus_protocol, f"R{SERIAL_NUMBER}F01D")
        )
        mock_conbus_protocol.send_telegram.reset_mock()

        service.telegram_received(
            self.make_event(mock_conbus_protocol, f"R{SERIAL_NUMBER}F02D0007")
        )

        devices = service.discovered_device_result.discovered_devices
        assert devices is not None
        assert devices[0]["module_type"] == "07"
        # Module type code query is sent for the same serial number
        mock_conbus_protocol.send_telegram.assert_called_once_with(
            telegram_type=TelegramType.SYSTEM,
            serial_number=SERIAL_NUMBER,
            system_function=SystemFunction.READ_DATAPOINT,
            data_value=DataPointType.MODULE_TYPE_CODE.value,
        )

    def test_full_discovery_flow_succeeds(
        self, service: ConbusDiscoverService, mock_conbus_protocol: Mock
    ) -> None:
        """Test discovery, module type and code replies complete the result."""
        finish_mock = Mock()
        discovered_mock = Mock()
        service.on_finish.connect(finish_mock)
        service.on_device_discovered.connect(discovered_mock)

        service.telegram_received(
            self.make_event(mock_conbus_protocol, f"R{SERIAL_NUMBER}F01D")
        )
        service.telegram_received(
            self.make_event(mock_conbus_protocol, f"R{SERIAL_NUMBER}F02D0007")
        )
        service.telegram_received(
            self.make_event(mock_conbus_protocol, f"R{SERIAL_NUMBER}F02D0707")
        )

        assert service.discovered_device_result.success is True
        assert service.discovered_device_result.error is None
        assert service.discovered_device_result.discovered_devices == [
            {
                "serial_number": SERIAL_NUMBER,
                "module_type": "07",
                "module_type_code": XP24_MODULE_TYPE_CODE,
                "module_type_name": "XP24",
            }
        ]
        finish_mock.assert_called_once_with(service.discovered_device_result)
        # Initial discovery + module type update + module type code update
        assert discovered_mock.call_count == EXPECTED_DEVICE_UPDATE_EVENTS

    def test_module_type_code_reply_without_module_type_does_not_finish(
        self, service: ConbusDiscoverService, mock_conbus_protocol: Mock
    ) -> None:
        """Test an incomplete device (missing module_type) defers completion."""
        finish_mock = Mock()
        service.on_finish.connect(finish_mock)

        service.telegram_received(
            self.make_event(mock_conbus_protocol, f"R{SERIAL_NUMBER}F01D")
        )
        service.telegram_received(
            self.make_event(mock_conbus_protocol, f"R{SERIAL_NUMBER}F02D0707")
        )

        finish_mock.assert_not_called()
        assert service.discovered_device_result.success is False

    def test_telegram_received_invalid_checksum_ignored(
        self, service: ConbusDiscoverService, mock_conbus_protocol: Mock
    ) -> None:
        """Test a reply with invalid checksum is recorded but not processed."""
        event = TelegramReceivedEvent.model_construct(
            protocol=mock_conbus_protocol,
            frame=f"<R{SERIAL_NUMBER}F01DXX>",
            telegram=f"R{SERIAL_NUMBER}F01DXX",
            payload=f"R{SERIAL_NUMBER}F01D",
            telegram_type="R",
            serial_number=SERIAL_NUMBER,
            checksum="XX",
            checksum_valid=False,
        )

        service.telegram_received(event)

        assert service.discovered_device_result.received_telegrams == [event.frame]
        assert service.discovered_device_result.discovered_devices is None
        mock_conbus_protocol.send_telegram.assert_not_called()

    def test_telegram_received_non_reply_ignored(
        self, service: ConbusDiscoverService, mock_conbus_protocol: Mock
    ) -> None:
        """Test a non-reply telegram is recorded but not processed."""
        event = self.make_event(mock_conbus_protocol, f"E{SERIAL_NUMBER}F01D")

        service.telegram_received(event)

        assert service.discovered_device_result.received_telegrams == [event.frame]
        assert service.discovered_device_result.discovered_devices is None
        mock_conbus_protocol.send_telegram.assert_not_called()

    def test_handle_module_type_code_response_unknown_code(
        self, service: ConbusDiscoverService, mock_conbus_protocol: Mock
    ) -> None:
        """Test an unknown module type code is stored as UNKNOWN_xx."""
        service.telegram_received(
            self.make_event(mock_conbus_protocol, f"R{SERIAL_NUMBER}F01D")
        )

        service.handle_module_type_code_response(SERIAL_NUMBER, "99")

        devices = service.discovered_device_result.discovered_devices
        assert devices is not None
        assert devices[0]["module_type_name"] == "UNKNOWN_99"

    def test_handle_module_type_code_response_invalid_code(
        self, service: ConbusDiscoverService, mock_conbus_protocol: Mock
    ) -> None:
        """Test a non-numeric module type code is stored as INVALID_xx."""
        service.telegram_received(
            self.make_event(mock_conbus_protocol, f"R{SERIAL_NUMBER}F01D")
        )

        service.handle_module_type_code_response(SERIAL_NUMBER, "XX")

        devices = service.discovered_device_result.discovered_devices
        assert devices is not None
        assert devices[0]["module_type_name"] == "INVALID_XX"
        assert devices[0]["module_type_code"] == 0

    def test_handle_module_type_code_response_without_devices_succeeds(
        self, service: ConbusDiscoverService
    ) -> None:
        """Test a code reply with no discovered devices finishes successfully."""
        finish_mock = Mock()
        service.on_finish.connect(finish_mock)

        service.handle_module_type_code_response(SERIAL_NUMBER, "07")

        assert service.discovered_device_result.success is True
        finish_mock.assert_called_once_with(service.discovered_device_result)

    def test_handle_module_type_response_unknown_serial(
        self, service: ConbusDiscoverService, mock_conbus_protocol: Mock
    ) -> None:
        """Test a module type reply for an unknown serial still queries the code."""
        service.telegram_received(
            self.make_event(mock_conbus_protocol, f"R{SERIAL_NUMBER}F01D")
        )
        mock_conbus_protocol.send_telegram.reset_mock()

        service.handle_module_type_response("0099999999", "07")

        devices = service.discovered_device_result.discovered_devices
        assert devices is not None
        assert devices[0]["module_type"] is None
        mock_conbus_protocol.send_telegram.assert_called_once_with(
            telegram_type=TelegramType.SYSTEM,
            serial_number="0099999999",
            system_function=SystemFunction.READ_DATAPOINT,
            data_value=DataPointType.MODULE_TYPE_CODE.value,
        )

    def test_timeout(self, service: ConbusDiscoverService) -> None:
        """Test timeout emits on_finish with an error."""
        finish_mock = Mock()
        service.on_finish.connect(finish_mock)

        service.timeout()

        assert service.discovered_device_result.success is False
        assert service.discovered_device_result.error == "Discovered device timeout"
        finish_mock.assert_called_once_with(service.discovered_device_result)

    def test_failed(self, service: ConbusDiscoverService) -> None:
        """Test failed emits on_finish with the failure message."""
        finish_mock = Mock()
        service.on_finish.connect(finish_mock)

        service.failed("Connection refused")

        assert service.discovered_device_result.success is False
        assert service.discovered_device_result.error == "Connection refused"
        finish_mock.assert_called_once_with(service.discovered_device_result)

    def test_succeed(self, service: ConbusDiscoverService) -> None:
        """Test succeed emits on_finish with a successful result."""
        finish_mock = Mock()
        service.on_finish.connect(finish_mock)

        service.succeed()

        assert service.discovered_device_result.success is True
        assert service.discovered_device_result.error is None
        finish_mock.assert_called_once_with(service.discovered_device_result)

    def test_set_timeout(
        self, service: ConbusDiscoverService, mock_conbus_protocol: Mock
    ) -> None:
        """Test set_timeout delegates to protocol."""
        service.set_timeout(TIMEOUT_SECONDS)

        assert mock_conbus_protocol.timeout_seconds == TIMEOUT_SECONDS

    def test_set_event_loop(
        self, service: ConbusDiscoverService, mock_conbus_protocol: Mock
    ) -> None:
        """Test set_event_loop delegates to protocol."""
        event_loop = Mock()

        service.set_event_loop(event_loop)

        mock_conbus_protocol.set_event_loop.assert_called_once_with(event_loop)

    def test_start_reactor(
        self, service: ConbusDiscoverService, mock_conbus_protocol: Mock
    ) -> None:
        """Test start_reactor delegates to protocol."""
        service.start_reactor()

        mock_conbus_protocol.start_reactor.assert_called_once()

    def test_stop_reactor(
        self, service: ConbusDiscoverService, mock_conbus_protocol: Mock
    ) -> None:
        """Test stop_reactor delegates to protocol."""
        service.stop_reactor()

        mock_conbus_protocol.stop_reactor.assert_called_once()

    def test_service_context_manager(
        self, service: ConbusDiscoverService, mock_conbus_protocol: Mock
    ) -> None:
        """Test context manager disconnects signals and stops the reactor."""
        with service as s:
            assert s is service
        # Signals should be disconnected after exit
        mock_conbus_protocol.on_connection_made.disconnect.assert_called_once()
        mock_conbus_protocol.on_telegram_sent.disconnect.assert_called_once()
        mock_conbus_protocol.on_telegram_received.disconnect.assert_called_once()
        mock_conbus_protocol.on_timeout.disconnect.assert_called_once()
        mock_conbus_protocol.on_failed.disconnect.assert_called_once()
        mock_conbus_protocol.stop_reactor.assert_called_once()

    def test_progress_events_across_multiple_devices(
        self, service: ConbusDiscoverService, mock_conbus_protocol: Mock
    ) -> None:
        """Test each discovered device emits one progress event."""
        progress_mock = Mock()
        service.on_progress.connect(progress_mock)
        other_serial = "0012345022"

        service.telegram_received(
            self.make_event(mock_conbus_protocol, f"R{SERIAL_NUMBER}F01D")
        )
        service.telegram_received(
            self.make_event(mock_conbus_protocol, f"R{other_serial}F01D")
        )

        assert progress_mock.call_args_list == [
            call(SERIAL_NUMBER),
            call(other_serial),
        ]
        devices = service.discovered_device_result.discovered_devices
        assert devices is not None
        assert [device["serial_number"] for device in devices] == [
            SERIAL_NUMBER,
            other_serial,
        ]
