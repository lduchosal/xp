# Copyright (c) 2025 ldvchosal
"""Unit tests for StateMonitorService."""

from collections.abc import Callable
from unittest.mock import Mock

import pytest

from xp.models.config.conson_module_config import (
    ConsonModuleConfig,
    ConsonModuleListConfig,
)
from xp.models.protocol.conbus_protocol import TelegramReceivedEvent
from xp.models.telegram.event_telegram import EventTelegram
from xp.models.telegram.event_type import EventType
from xp.models.term.module_state import ModuleState
from xp.services.protocol.conbus_event_protocol import ConbusEventProtocol
from xp.services.term.state_monitor_service import StateMonitorService

# Number of modules declared in the conson_config fixture.
EXPECTED_MODULE_COUNT = 4
# Link numbers of the modules declared in the conson_config fixture.
XP24_LINK_NUMBER = 9
XP130_LINK_NUMBER = 5
XP33LR_LINK_NUMBER = 3
XP33LED_LINK_NUMBER = 4


def get_connected_handler(signal_mock: Mock) -> Callable[..., None]:
    """Return the handler the service connected to the given protocol signal.

    Returns:
        The handler the service connected to the given protocol signal.

    """
    handler: Callable[..., None] = signal_mock.connect.call_args.args[0]
    return handler


def find_module_by_link(service: StateMonitorService, link_number: int) -> ModuleState:
    """Find a module state by link number via the public module_states API.

    Returns:
        The first ModuleState whose link_number matches.

    """
    return next(m for m in service.module_states if m.link_number == link_number)


class TestStateMonitorService:
    """Unit tests for StateMonitorService."""

    def _make_event(
        self, mock_protocol: Mock, frame: str, telegram_type: str
    ) -> TelegramReceivedEvent:
        """Create TelegramReceivedEvent helper.

        Args:
            mock_protocol: Mock protocol fixture.
            frame: Telegram frame.
            telegram_type: Telegram type.

        Returns:
            Telegram event.

        """
        telegram = frame[1:-1]
        checksum = telegram[-2:]
        payload = telegram[:-2]
        return TelegramReceivedEvent(
            protocol=mock_protocol,
            frame=frame,
            telegram=telegram,
            payload=payload,
            telegram_type=telegram_type,
            serial_number="",
            checksum=checksum,
            checksum_valid=True,
        )

    @pytest.fixture
    def mock_protocol(self) -> Mock:
        """Create mock ConbusEventProtocol.

        Returns:
            Mock ConbusEventProtocol.

        """
        protocol = Mock(spec=ConbusEventProtocol)
        protocol.cli_config = Mock()
        protocol.cli_config.ip = "192.168.1.100"
        protocol.cli_config.port = 10001
        protocol.on_connection_made = Mock()
        protocol.on_connection_failed = Mock()
        protocol.on_telegram_received = Mock()
        protocol.on_timeout = Mock()
        protocol.on_failed = Mock()
        protocol.connect = Mock()
        protocol.disconnect = Mock()
        protocol.send_telegram = Mock()
        return protocol

    @pytest.fixture
    def conson_config(self) -> ConsonModuleListConfig:
        """Create ConsonModuleListConfig with test modules.

        Returns:
            ConsonModuleListConfig with test modules.

        """
        return ConsonModuleListConfig(
            root=[
                ConsonModuleConfig(
                    name="A01",
                    serial_number="1234567890",
                    module_type="XP24",
                    module_type_code=7,
                    link_number=XP24_LINK_NUMBER,
                    auto_report_status="PP",
                ),
                ConsonModuleConfig(
                    name="A02",
                    serial_number="0987654321",
                    module_type="XP130",
                    module_type_code=13,
                    link_number=XP130_LINK_NUMBER,
                    auto_report_status="NN",
                ),
                ConsonModuleConfig(
                    name="A03",
                    serial_number="1111111111",
                    module_type="XP33LR",
                    module_type_code=30,
                    link_number=XP33LR_LINK_NUMBER,
                    auto_report_status="PP",
                ),
                ConsonModuleConfig(
                    name="A04",
                    serial_number="2222222222",
                    module_type="XP33LED",
                    module_type_code=35,
                    link_number=XP33LED_LINK_NUMBER,
                    auto_report_status="PP",
                ),
            ]
        )

    @pytest.fixture
    def mock_telegram_service(self) -> Mock:
        """Create mock TelegramService.

        Returns:
            Mock TelegramService.

        """
        service = Mock()
        service.parse_event_telegram = Mock()
        service.parse_reply_telegram = Mock()
        return service

    @pytest.fixture
    def service(
        self,
        mock_protocol: Mock,
        conson_config: ConsonModuleListConfig,
        mock_telegram_service: Mock,
    ) -> StateMonitorService:
        """Create service instance.

        Returns:
            Service instance.

        """
        return StateMonitorService(
            conbus_protocol=mock_protocol,
            conson_config=conson_config,
            telegram_service=mock_telegram_service,
        )

    def test_initialization(self, service: StateMonitorService) -> None:
        """Test service initializes module states from config."""
        assert len(service.module_states) == EXPECTED_MODULE_COUNT

        # Check first module (XP24)
        xp24_state = next(m for m in service.module_states if m.name == "A01")
        assert xp24_state.serial_number == "1234567890"
        assert xp24_state.module_type == "XP24"
        assert xp24_state.link_number == XP24_LINK_NUMBER
        assert xp24_state.auto_report is True
        assert not xp24_state.outputs
        assert xp24_state.error_status == "OK"

        # Check second module (XP130)
        xp130_state = next(m for m in service.module_states if m.name == "A02")
        assert xp130_state.link_number == XP130_LINK_NUMBER
        assert xp130_state.auto_report is False

        # Check third module (XP33LR)
        xp33lr_state = next(m for m in service.module_states if m.name == "A03")
        assert xp33lr_state.serial_number == "1111111111"
        assert xp33lr_state.module_type == "XP33LR"
        assert xp33lr_state.link_number == XP33LR_LINK_NUMBER
        assert xp33lr_state.auto_report is True

        # Check fourth module (XP33LED)
        xp33led_state = next(m for m in service.module_states if m.name == "A04")
        assert xp33led_state.serial_number == "2222222222"
        assert xp33led_state.module_type == "XP33LED"
        assert xp33led_state.link_number == XP33LED_LINK_NUMBER
        assert xp33led_state.auto_report is True

    def test_find_module_by_link_found(self, service: StateMonitorService) -> None:
        """Test _find_module_by_link returns module when found."""
        # The private helper itself is the unit under test.
        module = service._find_module_by_link(XP24_LINK_NUMBER)  # noqa: SLF001

        assert module is not None
        assert module.name == "A01"
        assert module.link_number == XP24_LINK_NUMBER

    def test_find_module_by_link_not_found(self, service: StateMonitorService) -> None:
        """Test _find_module_by_link returns None when not found."""
        # The private helper itself is the unit under test.
        module = service._find_module_by_link(99)  # noqa: SLF001
        assert module is None

    def test_update_output_bit_empty_outputs(
        self, service: StateMonitorService
    ) -> None:
        """Test _update_output_bit with empty outputs string."""
        module = find_module_by_link(service, XP24_LINK_NUMBER)
        module.outputs = ""

        # The private helper itself is the unit under test.
        update_bit = service._update_output_bit  # noqa: SLF001

        update_bit(module, 0, output_state=True)
        assert module.outputs == "1"

        update_bit(module, 2, output_state=True)
        assert module.outputs == "1 0 1"

    def test_update_output_bit_existing_outputs(
        self, service: StateMonitorService
    ) -> None:
        """Test _update_output_bit with existing outputs."""
        module = find_module_by_link(service, XP24_LINK_NUMBER)
        module.outputs = "0 0 0 0"

        # The private helper itself is the unit under test.
        update_bit = service._update_output_bit  # noqa: SLF001

        update_bit(module, 1, output_state=True)
        assert module.outputs == "0 1 0 0"

        update_bit(module, 3, output_state=True)
        assert module.outputs == "0 1 0 1"

        update_bit(module, 1, output_state=False)
        assert module.outputs == "0 0 0 1"

    def test_update_output_bit_expand_outputs(
        self, service: StateMonitorService
    ) -> None:
        """Test _update_output_bit expands outputs when too short."""
        module = find_module_by_link(service, XP24_LINK_NUMBER)
        module.outputs = "1"

        # The private helper itself is the unit under test.
        update_bit = service._update_output_bit  # noqa: SLF001

        update_bit(module, 3, output_state=True)
        assert module.outputs == "1 0 0 1"

    def test_handle_event_telegram_xp24_output_on(
        self,
        service: StateMonitorService,
        mock_telegram_service: Mock,
        mock_protocol: Mock,
    ) -> None:
        """Test event handling processes XP24 output ON event."""
        # Mock event telegram for XP24 L09 output 0 ON
        event_telegram = EventTelegram(
            raw_telegram="<E07L09I80MAE>",
            checksum="AE",
            checksum_validated=True,
            event_telegram_type="E",
            module_type=7,  # XP24
            link_number=9,
            input_number=80,  # Output 0
            event_type=EventType.BUTTON_PRESS,
        )
        mock_telegram_service.parse_event_telegram.return_value = event_telegram

        # Setup module initial state
        module = find_module_by_link(service, XP24_LINK_NUMBER)
        module.outputs = "0 0 0 0"

        # Mock signal to verify emission
        signal_handler = Mock()
        service.on_module_state_changed.connect(signal_handler)

        # Create event
        event = self._make_event(mock_protocol, "<E07L09I80MAE>", "E")

        # Process event through the handler registered on the protocol
        get_connected_handler(mock_protocol.on_telegram_received)(event)

        # Verify output updated
        assert module.outputs == "1 0 0 0"
        assert module.last_update is not None
        signal_handler.assert_called_once()

    def test_handle_event_telegram_xp24_output_off(
        self,
        service: StateMonitorService,
        mock_telegram_service: Mock,
        mock_protocol: Mock,
    ) -> None:
        """Test event handling processes XP24 output OFF event."""
        # Mock event telegram for XP24 L09 output 2 OFF
        event_telegram = EventTelegram(
            raw_telegram="<E07L09I82BAE>",
            checksum="AE",
            checksum_validated=True,
            event_telegram_type="E",
            module_type=7,
            link_number=9,
            input_number=82,  # Output 2
            event_type=EventType.BUTTON_RELEASE,
        )
        mock_telegram_service.parse_event_telegram.return_value = event_telegram

        module = find_module_by_link(service, XP24_LINK_NUMBER)
        module.outputs = "1 1 1 1"

        event = self._make_event(mock_protocol, "<E07L09I82BAE>", "E")

        get_connected_handler(mock_protocol.on_telegram_received)(event)
        assert module.outputs == "1 1 0 1"

    def test_handle_event_telegram_ignores_non_xp24(
        self,
        service: StateMonitorService,
        mock_telegram_service: Mock,
        mock_protocol: Mock,
    ) -> None:
        """Test event handling ignores non-XP24 events."""
        # Mock event telegram from XP130 (not XP24)
        event_telegram = EventTelegram(
            raw_telegram="<E13L05I80MAE>",
            checksum="AE",
            checksum_validated=True,
            module_type=13,  # XP130
            link_number=5,
            input_number=80,
            event_type=EventType.BUTTON_PRESS,
        )
        mock_telegram_service.parse_event_telegram.return_value = event_telegram

        module = find_module_by_link(service, XP130_LINK_NUMBER)
        module.outputs = "0 0 0 0"

        event = self._make_event(mock_protocol, "<E13L05I80MAE>", "E")

        get_connected_handler(mock_protocol.on_telegram_received)(event)

        # Output should not change
        assert module.outputs == "0 0 0 0"

    def test_handle_event_telegram_ignores_input_events(
        self,
        service: StateMonitorService,
        mock_telegram_service: Mock,
        mock_protocol: Mock,
    ) -> None:
        """Test event handling ignores input events (I00-I09)."""
        # Mock event telegram for input event
        event_telegram = EventTelegram(
            raw_telegram="<E07L09I02MAE>",
            checksum="AE",
            checksum_validated=True,
            module_type=7,
            link_number=9,
            input_number=2,  # Input event, not output
            event_type=EventType.BUTTON_PRESS,
        )
        mock_telegram_service.parse_event_telegram.return_value = event_telegram

        module = find_module_by_link(service, XP24_LINK_NUMBER)
        module.outputs = "0 0 0 0"

        event = self._make_event(mock_protocol, "<E07L09I02MAE>", "E")

        get_connected_handler(mock_protocol.on_telegram_received)(event)

        # Output should not change
        assert module.outputs == "0 0 0 0"

    @pytest.mark.usefixtures("service")
    def test_handle_event_telegram_unknown_link(
        self, mock_telegram_service: Mock, mock_protocol: Mock
    ) -> None:
        """Test event handling handles unknown link number."""
        event_telegram = EventTelegram(
            raw_telegram="<E07L99I80MAE>",
            checksum="AE",
            checksum_validated=True,
            module_type=7,
            link_number=99,  # Unknown link
            input_number=80,
            event_type=EventType.BUTTON_PRESS,
        )
        mock_telegram_service.parse_event_telegram.return_value = event_telegram

        event = self._make_event(mock_protocol, "<E07L99I80MAE>", "E")

        # Should not raise exception
        get_connected_handler(mock_protocol.on_telegram_received)(event)

    @pytest.mark.usefixtures("service")
    def test_handle_event_telegram_malformed(
        self, mock_telegram_service: Mock, mock_protocol: Mock
    ) -> None:
        """Test event handling handles malformed telegram."""
        mock_telegram_service.parse_event_telegram.return_value = None

        event = self._make_event(mock_protocol, "<INVALID>", "E")

        # Should not raise exception
        get_connected_handler(mock_protocol.on_telegram_received)(event)

    def test_on_telegram_received_routes_event(
        self,
        service: StateMonitorService,
        mock_telegram_service: Mock,
        mock_protocol: Mock,
    ) -> None:
        """Test the registered handler routes EVENT telegrams."""
        event_telegram = EventTelegram(
            raw_telegram="<E07L09I80MAE>",
            checksum="AE",
            checksum_validated=True,
            module_type=7,
            link_number=9,
            input_number=80,
            event_type=EventType.BUTTON_PRESS,
        )
        mock_telegram_service.parse_event_telegram.return_value = event_telegram

        module = find_module_by_link(service, XP24_LINK_NUMBER)
        module.outputs = "0 0 0 0"

        event = self._make_event(mock_protocol, "<E07L09I80MAE>", "E")

        get_connected_handler(mock_protocol.on_telegram_received)(event)

        # Verify event was processed
        assert module.outputs == "1 0 0 0"

    @pytest.mark.usefixtures("service")
    def test_on_telegram_received_routes_reply(
        self, mock_telegram_service: Mock, mock_protocol: Mock
    ) -> None:
        """Test the registered handler routes REPLY telegrams."""
        # Create reply event with proper serial number
        telegram = "R1234567890F42D00AB"
        event = TelegramReceivedEvent(
            protocol=mock_protocol,
            frame=f"<{telegram}>",
            telegram=telegram,
            payload="R1234567890F42D00",
            telegram_type="R",
            serial_number="1234567890",
            checksum="AB",
            checksum_valid=True,
        )

        # Mock reply telegram
        mock_telegram_service.parse_reply_telegram.return_value = None

        get_connected_handler(mock_protocol.on_telegram_received)(event)

        # Verify parse_reply_telegram was called
        mock_telegram_service.parse_reply_telegram.assert_called_once()

    def test_handle_event_telegram_xp33lr_channel_on(
        self,
        service: StateMonitorService,
        mock_telegram_service: Mock,
        mock_protocol: Mock,
    ) -> None:
        """Test event handling processes XP33LR channel ON event."""
        # Mock event telegram for XP33LR L03 channel 0 ON
        event_telegram = EventTelegram(
            raw_telegram="<E30L03I80MAE>",
            checksum="AE",
            checksum_validated=True,
            event_telegram_type="E",
            module_type=30,  # XP33LR
            link_number=3,
            input_number=80,  # Channel 0 (I80)
            event_type=EventType.BUTTON_PRESS,
        )
        mock_telegram_service.parse_event_telegram.return_value = event_telegram

        # Setup module initial state
        module = find_module_by_link(service, XP33LR_LINK_NUMBER)
        module.outputs = "0 0 0"

        # Mock signal to verify emission
        signal_handler = Mock()
        service.on_module_state_changed.connect(signal_handler)

        # Create event
        event = self._make_event(mock_protocol, "<E30L03I80MAE>", "E")

        # Process event
        get_connected_handler(mock_protocol.on_telegram_received)(event)

        # Verify output updated
        assert module.outputs == "1 0 0"
        assert module.last_update is not None
        signal_handler.assert_called_once()

    def test_handle_event_telegram_xp33lr_channel_off(
        self,
        service: StateMonitorService,
        mock_telegram_service: Mock,
        mock_protocol: Mock,
    ) -> None:
        """Test event handling processes XP33LR channel OFF event."""
        # Mock event telegram for XP33LR L03 channel 1 OFF
        event_telegram = EventTelegram(
            raw_telegram="<E30L03I81BAE>",
            checksum="AE",
            checksum_validated=True,
            event_telegram_type="E",
            module_type=30,  # XP33LR
            link_number=3,
            input_number=81,  # Channel 1 (I81)
            event_type=EventType.BUTTON_RELEASE,
        )
        mock_telegram_service.parse_event_telegram.return_value = event_telegram

        module = find_module_by_link(service, XP33LR_LINK_NUMBER)
        module.outputs = "1 1 1"

        event = self._make_event(mock_protocol, "<E30L03I81BAE>", "E")

        get_connected_handler(mock_protocol.on_telegram_received)(event)
        assert module.outputs == "1 0 1"

    def test_handle_event_telegram_xp33led_channel_on(
        self,
        service: StateMonitorService,
        mock_telegram_service: Mock,
        mock_protocol: Mock,
    ) -> None:
        """Test event handling processes XP33LED channel ON event."""
        # Mock event telegram for XP33LED L04 channel 2 ON
        event_telegram = EventTelegram(
            raw_telegram="<E35L04I82MAE>",
            checksum="AE",
            checksum_validated=True,
            event_telegram_type="E",
            module_type=35,  # XP33LED
            link_number=4,
            input_number=82,  # Channel 2 (I82)
            event_type=EventType.BUTTON_PRESS,
        )
        mock_telegram_service.parse_event_telegram.return_value = event_telegram

        # Setup module initial state
        module = find_module_by_link(service, XP33LED_LINK_NUMBER)
        module.outputs = "0 0 0"

        # Create event
        event = self._make_event(mock_protocol, "<E35L04I82MAE>", "E")

        # Process event
        get_connected_handler(mock_protocol.on_telegram_received)(event)

        # Verify output updated
        assert module.outputs == "0 0 1"
        assert module.last_update is not None

    def test_handle_event_telegram_xp33_ignores_invalid_channel(
        self,
        service: StateMonitorService,
        mock_telegram_service: Mock,
        mock_protocol: Mock,
    ) -> None:
        """Test event handling ignores XP33 events for invalid channels."""
        # Mock event telegram for XP33LR with invalid channel number
        event_telegram = EventTelegram(
            raw_telegram="<E30L03I05MAE>",
            checksum="AE",
            checksum_validated=True,
            event_telegram_type="E",
            module_type=30,  # XP33LR
            link_number=3,
            input_number=5,  # Invalid channel (only 0-2 valid)
            event_type=EventType.BUTTON_PRESS,
        )
        mock_telegram_service.parse_event_telegram.return_value = event_telegram

        module = find_module_by_link(service, XP33LR_LINK_NUMBER)
        module.outputs = "0 0 0"

        event = self._make_event(mock_protocol, "<E30L03I05MAE>", "E")

        get_connected_handler(mock_protocol.on_telegram_received)(event)

        # Output should not change
        assert module.outputs == "0 0 0"
