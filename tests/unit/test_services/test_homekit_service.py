"""Unit tests for HomekitService."""

from unittest.mock import Mock

import pytest

from xp.models.config.conson_module_config import (
    ConsonModuleConfig,
    ConsonModuleListConfig,
)
from xp.models.homekit.homekit_config import (
    BridgeConfig,
    HomekitAccessoryConfig,
    HomekitConfig,
    RoomConfig,
)
from xp.models.protocol.conbus_protocol import TelegramReceivedEvent
from xp.models.telegram.datapoint_type import DataPointType
from xp.models.telegram.event_telegram import EventTelegram
from xp.models.telegram.event_type import EventType
from xp.models.telegram.reply_telegram import ReplyTelegram
from xp.models.telegram.system_function import SystemFunction
from xp.models.term.connection_state import ConnectionState
from xp.services.term.homekit_service import HomekitService


class TestHomekitService:
    """Unit tests for HomekitService."""

    def _make_event(
        self,
        mock_protocol: Mock,
        frame: str,
        telegram_type: str,
        serial_number: str = "",
    ) -> TelegramReceivedEvent:
        """Create TelegramReceivedEvent helper."""
        telegram = frame[1:-1]
        checksum = telegram[-2:]
        payload = telegram[:-2]
        return TelegramReceivedEvent(
            protocol=mock_protocol,
            frame=frame,
            telegram=telegram,
            payload=payload,
            telegram_type=telegram_type,
            serial_number=serial_number,
            checksum=checksum,
            checksum_valid=True,
        )

    @pytest.fixture
    def mock_protocol(self):
        """Create mock ConbusEventProtocol."""
        from xp.services.protocol.conbus_event_protocol import ConbusEventProtocol

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
        protocol.send_raw_telegram = Mock()
        return protocol

    @pytest.fixture
    def homekit_config(self):
        """Create HomekitConfig with test accessories."""
        return HomekitConfig(
            bridge=BridgeConfig(
                name="Test Bridge",
                rooms=[
                    RoomConfig(name="Living Room", accessories=["light1", "dimmer1"]),
                    RoomConfig(name="Bedroom", accessories=["light2"]),
                ],
            ),
            accessories=[
                HomekitAccessoryConfig(
                    name="light1",
                    id="light1",
                    serial_number="1234567890",
                    output_number=0,
                    description="Main Light",
                    service="Lightbulb",
                    on_action="E02L09I80",
                    off_action="E02L09I80",
                    toggle_action="E02L09I00",
                ),
                HomekitAccessoryConfig(
                    name="dimmer1",
                    id="dimmer1",
                    serial_number="2222222222",
                    output_number=0,
                    description="Dimmer Light",
                    service="Lightbulb",
                    on_action="E02L03I80",
                    off_action="E02L03I80",
                    toggle_action="E02L03I00",
                ),
                HomekitAccessoryConfig(
                    name="light2",
                    id="light2",
                    serial_number="1234567890",
                    output_number=1,
                    description="Bedroom Light",
                    service="Lightbulb",
                    on_action="E02L09I81",
                    off_action="E02L09I81",
                    toggle_action="E02L09I01",
                ),
            ],
        )

    @pytest.fixture
    def conson_config(self):
        """Create ConsonModuleListConfig with test modules."""
        return ConsonModuleListConfig(
            root=[
                ConsonModuleConfig(
                    name="A01",
                    serial_number="1234567890",
                    module_type="XP24",
                    module_type_code=7,
                    link_number=9,
                    auto_report_status="PP",
                ),
                ConsonModuleConfig(
                    name="A02",
                    serial_number="2222222222",
                    module_type="XP33LED",
                    module_type_code=35,
                    link_number=3,
                    auto_report_status="PP",
                ),
            ]
        )

    @pytest.fixture
    def mock_telegram_service(self):
        """Create mock TelegramService."""
        service = Mock()
        service.parse_event_telegram = Mock()
        service.parse_reply_telegram = Mock()
        return service

    @pytest.fixture
    def mock_accessory_driver(self):
        """Create mock HomekitAccessoryDriver."""
        from xp.services.term.homekit_accessory_driver import HomekitAccessoryDriver

        driver = Mock(spec=HomekitAccessoryDriver)
        driver.set_callback = Mock()
        driver.start = Mock()
        driver.stop = Mock()
        driver.update_state = Mock()
        return driver

    @pytest.fixture
    def service(
        self,
        mock_protocol,
        homekit_config,
        conson_config,
        mock_telegram_service,
        mock_accessory_driver,
    ):
        """Create service instance."""
        return HomekitService(
            conbus_protocol=mock_protocol,
            homekit_config=homekit_config,
            conson_config=conson_config,
            telegram_service=mock_telegram_service,
            accessory_driver=mock_accessory_driver,
        )

    def test_initialization(self, service):
        """Test service initializes accessory states from config."""
        assert len(service.accessory_states) == 3

        # Check first accessory (XP24)
        light1 = next(
            (a for a in service.accessory_states if a.accessory_name == "Main Light"),
            None,
        )
        assert light1 is not None
        assert light1.room_name == "Living Room"
        assert light1.serial_number == "1234567890"
        assert light1.module_type == "XP24"
        assert light1.module_name == "A01"
        assert light1.output == 1
        assert light1.output_state == "?"
        assert light1.error_status == "OK"
        assert light1.toggle_action == "E02L09I00"

    def test_initialization_assigns_action_keys(self, service):
        """Test service assigns sequential action keys to accessories."""
        states = service.accessory_states
        actions = [s.action for s in states]
        assert "a" in actions
        assert "b" in actions
        assert "c" in actions

    def test_initialization_assigns_sort_order(self, service):
        """Test service assigns sort order matching config order."""
        states = service.accessory_states
        # Should be sorted by sort field
        assert states[0].sort < states[1].sort < states[2].sort

    def test_connection_state_property(self, service):
        """Test connection_state returns current state."""
        assert service.connection_state == ConnectionState.DISCONNECTED

    def test_server_info_property(self, service):
        """Test server_info returns IP:port."""
        assert service.server_info == "192.168.1.100:10001"

    def test_connect(self, service, mock_protocol):
        """Test connect initiates connection."""
        signal_handler = Mock()
        service.on_connection_state_changed.connect(signal_handler)

        service.connect()

        mock_protocol.connect.assert_called_once()
        assert service.connection_state == ConnectionState.CONNECTING
        signal_handler.assert_called_with(ConnectionState.CONNECTING)

    def test_connect_when_already_connecting(self, service, mock_protocol):
        """Test connect does nothing when already connecting."""
        service.connect()  # First connect
        mock_protocol.connect.reset_mock()

        service.connect()  # Second connect should be ignored

        mock_protocol.connect.assert_not_called()

    def test_disconnect(self, service, mock_protocol):
        """Test disconnect terminates connection."""
        # First connect and establish connection
        service.connect()
        service._on_connection_made()

        signal_handler = Mock()
        service.on_connection_state_changed.connect(signal_handler)

        service.disconnect()

        mock_protocol.disconnect.assert_called_once()
        assert service.connection_state == ConnectionState.DISCONNECTED

    def test_disconnect_when_disconnected(self, service, mock_protocol):
        """Test disconnect does nothing when already disconnected."""
        service.disconnect()

        mock_protocol.disconnect.assert_not_called()

    def test_toggle_connection_connects_when_disconnected(self, service, mock_protocol):
        """Test toggle_connection connects when disconnected."""
        service.toggle_connection()

        mock_protocol.connect.assert_called_once()
        assert service.connection_state == ConnectionState.CONNECTING

    def test_toggle_connection_disconnects_when_connected(self, service, mock_protocol):
        """Test toggle_connection disconnects when connected."""
        service.connect()
        service._on_connection_made()

        service.toggle_connection()

        mock_protocol.disconnect.assert_called_once()

    def test_select_accessory_returns_id(self, service):
        """Test select_accessory returns accessory ID for valid key."""
        accessory_id = service.select_accessory("a")

        assert accessory_id is not None
        assert accessory_id == "A01_1"

    def test_select_accessory_invalid_key(self, service):
        """Test select_accessory returns None for invalid key."""
        accessory_id = service.select_accessory("z")  # Not assigned

        assert accessory_id is None

    def test_toggle_selected_sends_telegram(self, service, mock_protocol):
        """Test toggle_selected sends toggle_action telegram."""
        service.connect()
        service._on_connection_made()

        accessory_id = service.select_accessory("a")
        result = service.toggle_selected(accessory_id)

        assert result is True
        mock_protocol.send_raw_telegram.assert_called()

    def test_toggle_selected_invalid_id(self, service, mock_protocol):
        """Test toggle_selected returns False for invalid ID."""
        result = service.toggle_selected("invalid_id")

        assert result is False

    def test_turn_on_selected_sends_telegram(self, service, mock_protocol):
        """Test turn_on_selected sends on_action telegram."""
        accessory_id = service.select_accessory("a")
        result = service.turn_on_selected(accessory_id)

        assert result is True
        mock_protocol.send_raw_telegram.assert_called()

    def test_turn_off_selected_sends_telegram(self, service, mock_protocol):
        """Test turn_off_selected sends off_action telegram."""
        accessory_id = service.select_accessory("a")
        result = service.turn_off_selected(accessory_id)

        assert result is True
        mock_protocol.send_raw_telegram.assert_called()

    def test_toggle_selected_no_toggle_action(
        self, mock_protocol, conson_config, mock_telegram_service, mock_accessory_driver
    ):
        """Test toggle_selected returns False when no toggle_action."""
        # Create config without toggle_action
        homekit_config = HomekitConfig(
            bridge=BridgeConfig(
                name="Test",
                rooms=[RoomConfig(name="Room", accessories=["light_no_toggle"])],
            ),
            accessories=[
                HomekitAccessoryConfig(
                    name="light_no_toggle",
                    id="light_no_toggle",
                    serial_number="1234567890",
                    output_number=0,
                    description="No Toggle Light",
                    service="Lightbulb",
                    on_action="E02L09I80",
                    off_action="E02L09I80",
                    toggle_action=None,
                ),
            ],
        )

        svc = HomekitService(
            conbus_protocol=mock_protocol,
            homekit_config=homekit_config,
            conson_config=conson_config,
            telegram_service=mock_telegram_service,
            accessory_driver=mock_accessory_driver,
        )
        accessory_id = svc.select_accessory("a")
        assert accessory_id is not None
        result = svc.toggle_selected(accessory_id)

        assert result is False

    def test_refresh_all_queries_eligible_modules(self, service, mock_protocol):
        """Test refresh_all queries XP24/XP33LR/XP33LED modules."""
        service.connect()
        service._on_connection_made()

        service.refresh_all()

        # Should query both modules (XP24 and XP33LED)
        assert mock_protocol.send_telegram.call_count == 2

    def test_on_connection_made_handler(self, service):
        """Test _on_connection_made updates state and emits signals."""
        service.connect()

        signal_handler = Mock()
        service.on_connection_state_changed.connect(signal_handler)

        room_list_handler = Mock()
        service.on_room_list_updated.connect(room_list_handler)

        service._on_connection_made()

        assert service.connection_state == ConnectionState.CONNECTED
        signal_handler.assert_called_with(ConnectionState.CONNECTED)
        room_list_handler.assert_called_once()

    def test_on_connection_failed_handler(self, service):
        """Test _on_connection_failed updates state."""
        service.connect()

        signal_handler = Mock()
        service.on_connection_state_changed.connect(signal_handler)

        service._on_connection_failed(Exception("Connection error"))

        assert service.connection_state == ConnectionState.FAILED
        signal_handler.assert_called_with(ConnectionState.FAILED)

    def test_on_timeout_handler(self, service):
        """Test _on_timeout emits status message."""
        status_handler = Mock()
        service.on_status_message.connect(status_handler)

        service._on_timeout()

        status_handler.assert_called_once()

    def test_on_failed_handler(self, service):
        """Test _on_failed updates state."""
        service.connect()

        signal_handler = Mock()
        service.on_connection_state_changed.connect(signal_handler)

        service._on_failed(Exception("Protocol error"))

        assert service.connection_state == ConnectionState.FAILED

    def test_handle_event_telegram_xp24_output_on(
        self, service, mock_telegram_service, mock_protocol
    ):
        """Test _handle_event_telegram processes XP24 output ON event."""
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

        signal_handler = Mock()
        service.on_module_state_changed.connect(signal_handler)

        event = self._make_event(mock_protocol, "<E07L09I80MAE>", "E")
        service._on_telegram_received(event)

        # Find the accessory with output=1 for module A01
        light1 = next(
            (a for a in service.accessory_states if a.accessory_name == "Main Light"),
            None,
        )
        assert light1 is not None
        assert light1.output_state == "ON"
        assert light1.last_update is not None
        signal_handler.assert_called()

    def test_handle_event_telegram_xp24_output_off(
        self, service, mock_telegram_service, mock_protocol
    ):
        """Test _handle_event_telegram processes XP24 output OFF event."""
        event_telegram = EventTelegram(
            raw_telegram="<E07L09I80BAE>",
            checksum="AE",
            checksum_validated=True,
            event_telegram_type="E",
            module_type=7,  # XP24
            link_number=9,
            input_number=80,  # Output 0
            event_type=EventType.BUTTON_RELEASE,
        )
        mock_telegram_service.parse_event_telegram.return_value = event_telegram

        event = self._make_event(mock_protocol, "<E07L09I80BAE>", "E")
        service._on_telegram_received(event)

        light1 = next(
            (a for a in service.accessory_states if a.accessory_name == "Main Light"),
            None,
        )
        assert light1 is not None
        assert light1.output_state == "OFF"

    def test_handle_event_telegram_xp33led_channel_on(
        self, service, mock_telegram_service, mock_protocol
    ):
        """Test _handle_event_telegram processes XP33LED channel ON event."""
        event_telegram = EventTelegram(
            raw_telegram="<E35L03I80MAE>",
            checksum="AE",
            checksum_validated=True,
            event_telegram_type="E",
            module_type=35,  # XP33LED
            link_number=3,
            input_number=80,  # Channel 0
            event_type=EventType.BUTTON_PRESS,
        )
        mock_telegram_service.parse_event_telegram.return_value = event_telegram

        event = self._make_event(mock_protocol, "<E35L03I80MAE>", "E")
        service._on_telegram_received(event)

        dimmer = next(
            (a for a in service.accessory_states if a.accessory_name == "Dimmer Light"),
            None,
        )
        assert dimmer is not None
        assert dimmer.output_state == "ON"
        assert dimmer.dimming_state == ""  # Empty when ON

    def test_handle_event_telegram_xp33led_channel_off(
        self, service, mock_telegram_service, mock_protocol
    ):
        """Test _handle_event_telegram processes XP33LED channel OFF event."""
        event_telegram = EventTelegram(
            raw_telegram="<E35L03I80BAE>",
            checksum="AE",
            checksum_validated=True,
            event_telegram_type="E",
            module_type=35,  # XP33LED
            link_number=3,
            input_number=80,  # Channel 0
            event_type=EventType.BUTTON_RELEASE,
        )
        mock_telegram_service.parse_event_telegram.return_value = event_telegram

        event = self._make_event(mock_protocol, "<E35L03I80BAE>", "E")
        service._on_telegram_received(event)

        dimmer = next(
            (a for a in service.accessory_states if a.accessory_name == "Dimmer Light"),
            None,
        )
        assert dimmer is not None
        assert dimmer.output_state == "OFF"
        assert dimmer.dimming_state == "-"  # Dash when OFF and dimmable

    def test_handle_event_telegram_ignores_input_events(
        self, service, mock_telegram_service, mock_protocol
    ):
        """Test _handle_event_telegram ignores input events (I00-I09)."""
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

        signal_handler = Mock()
        service.on_module_state_changed.connect(signal_handler)

        event = self._make_event(mock_protocol, "<E07L09I02MAE>", "E")
        service._on_telegram_received(event)

        # Signal should not be emitted for input events
        signal_handler.assert_not_called()

    def test_handle_event_telegram_malformed(
        self, service, mock_telegram_service, mock_protocol
    ):
        """Test _handle_event_telegram handles malformed telegram."""
        mock_telegram_service.parse_event_telegram.return_value = None

        event = self._make_event(mock_protocol, "<INVALID>", "E")

        # Should not raise exception
        service._on_telegram_received(event)

    def test_handle_reply_telegram_updates_outputs(
        self, service, mock_telegram_service, mock_protocol
    ):
        """Test _handle_reply_telegram updates accessory outputs."""
        reply_telegram = ReplyTelegram(
            raw_telegram="<R1234567890F42D0009AB>",
            checksum="AB",
            checksum_validated=True,
            serial_number="1234567890",
            system_function=SystemFunction.READ_DATAPOINT,
            datapoint_type=DataPointType.MODULE_OUTPUT_STATE,
            data_value="03",  # Binary 0011 = outputs 0,1 ON
        )
        mock_telegram_service.parse_reply_telegram.return_value = reply_telegram

        signal_handler = Mock()
        service.on_module_state_changed.connect(signal_handler)

        event = TelegramReceivedEvent(
            protocol=mock_protocol,
            frame="<R1234567890F42D0009AB>",
            telegram="R1234567890F42D0009AB",
            payload="R1234567890F42D0009",
            telegram_type="R",
            serial_number="1234567890",
            checksum="AB",
            checksum_valid=True,
        )

        service._on_telegram_received(event)

        # Both accessories with serial 1234567890 should be updated
        light1 = next(
            (a for a in service.accessory_states if a.accessory_name == "Main Light"),
            None,
        )
        light2 = next(
            (
                a
                for a in service.accessory_states
                if a.accessory_name == "Bedroom Light"
            ),
            None,
        )

        assert light1 is not None
        assert light2 is not None
        assert signal_handler.call_count == 2  # Called for each accessory

    def test_handle_reply_telegram_no_serial(
        self, service, mock_telegram_service, mock_protocol
    ):
        """Test _handle_reply_telegram ignores events without serial number."""
        event = TelegramReceivedEvent(
            protocol=mock_protocol,
            frame="<RAB>",
            telegram="RAB",
            payload="R",
            telegram_type="R",
            serial_number="",  # No serial
            checksum="AB",
            checksum_valid=True,
        )

        # Should not raise exception
        service._on_telegram_received(event)

    def test_handle_reply_telegram_not_output_state(
        self, service, mock_telegram_service, mock_protocol
    ):
        """Test _handle_reply_telegram ignores non-output-state replies."""
        reply_telegram = ReplyTelegram(
            raw_telegram="<R1234567890F01D00AB>",
            checksum="AB",
            checksum_validated=True,
            serial_number="1234567890",
            system_function=SystemFunction.DISCOVERY,  # Not READ_DATAPOINT
            datapoint_type=None,
            data_value="",
        )
        mock_telegram_service.parse_reply_telegram.return_value = reply_telegram

        signal_handler = Mock()
        service.on_module_state_changed.connect(signal_handler)

        event = TelegramReceivedEvent(
            protocol=mock_protocol,
            frame="<R1234567890F01D00AB>",
            telegram="R1234567890F01D00AB",
            payload="R1234567890F01D00",
            telegram_type="R",
            serial_number="1234567890",
            checksum="AB",
            checksum_valid=True,
        )

        service._on_telegram_received(event)

        signal_handler.assert_not_called()

    def test_cleanup(self, service, mock_protocol):
        """Test cleanup disconnects signals."""
        service.cleanup()

        mock_protocol.on_connection_made.disconnect.assert_called_once()
        mock_protocol.on_connection_failed.disconnect.assert_called_once()
        mock_protocol.on_telegram_received.disconnect.assert_called_once()
        mock_protocol.on_timeout.disconnect.assert_called_once()
        mock_protocol.on_failed.disconnect.assert_called_once()

    def test_context_manager(self, service, mock_protocol):
        """Test context manager entry and exit."""
        with service as svc:
            assert svc is service

        # Verify cleanup was called
        mock_protocol.on_connection_made.disconnect.assert_called_once()

    def test_accessory_not_in_config(
        self, mock_protocol, conson_config, mock_telegram_service, mock_accessory_driver
    ):
        """Test service handles missing accessory config gracefully."""
        homekit_config = HomekitConfig(
            bridge=BridgeConfig(
                name="Test",
                rooms=[RoomConfig(name="Room", accessories=["nonexistent"])],
            ),
            accessories=[],  # No accessories defined
        )

        service = HomekitService(
            conbus_protocol=mock_protocol,
            homekit_config=homekit_config,
            conson_config=conson_config,
            telegram_service=mock_telegram_service,
            accessory_driver=mock_accessory_driver,
        )

        # Should handle gracefully with empty states
        assert len(service.accessory_states) == 0

    def test_module_not_in_config(
        self, mock_protocol, mock_telegram_service, mock_accessory_driver
    ):
        """Test service handles missing module config gracefully."""
        homekit_config = HomekitConfig(
            bridge=BridgeConfig(
                name="Test",
                rooms=[RoomConfig(name="Room", accessories=["light"])],
            ),
            accessories=[
                HomekitAccessoryConfig(
                    name="light",
                    id="light",
                    serial_number="9999999999",  # Not in conson_config
                    output_number=0,
                    description="Light",
                    service="Lightbulb",
                    on_action="E02L09I80",
                    off_action="E02L09I80",
                ),
            ],
        )

        conson_config = ConsonModuleListConfig(root=[])  # Empty config

        service = HomekitService(
            conbus_protocol=mock_protocol,
            homekit_config=homekit_config,
            conson_config=conson_config,
            telegram_service=mock_telegram_service,
            accessory_driver=mock_accessory_driver,
        )

        # Should handle gracefully with empty states
        assert len(service.accessory_states) == 0
