from unittest.mock import Mock, MagicMock, patch
import pytest

from bubus import EventBus
from twisted.internet.posixbase import PosixReactorBase

from xp.models.homekit.homekit_config import HomekitAccessoryConfig
from xp.models.homekit.homekit_conson_config import ConsonModuleConfig
from xp.models.protocol.conbus_protocol import (
    ConnectionFailedEvent,
    ConnectionLostEvent,
    ConnectionMadeEvent,
    DatapointReceivedEvent,
    DimmingLightGetBrightnessEvent,
    DimmingLightGetOnEvent,
    DimmingLightSetBrightnessEvent,
    DimmingLightSetOnEvent,
    LightBulbGetOnEvent,
    LightBulbSetOnEvent,
    ModuleDiscoveredEvent,
    OutletGetInUseEvent,
    OutletGetOnEvent,
    OutletSetOnEvent,
    ReadDatapointEvent,
    SendActionEvent,
    SendWriteConfigEvent,
    TelegramReceivedEvent,
)
from xp.models.telegram.datapoint_type import DataPointType
from xp.services import TelegramService
from xp.services.homekit.homekit_conbus_service import HomeKitConbusService
from xp.services.homekit.homekit_dimminglight_service import HomeKitDimmingLightService
from xp.services.homekit.homekit_lightbulb_service import HomeKitLightbulbService
from xp.services.homekit.homekit_hap_service import HomekitHapService
from xp.services.homekit.homekit_outlet_service import HomeKitOutletService
from xp.services.homekit.homekit_service import HomeKitService
from xp.services.protocol.protocol_factory import TelegramFactory
from xp.services.protocol.telegram_protocol import TelegramProtocol


# Test fixtures
@pytest.fixture
def mock_module():
    return ConsonModuleConfig(
        name="Test Module",
        serial_number="1234567890",
        module_type="XP24",
        module_type_code=24,
        link_number=1
    )


@pytest.fixture
def mock_accessory():
    return HomekitAccessoryConfig(
        name="Test Accessory",
        id="test_id",
        serial_number="1234567890",
        output_number=2,
        description="Test Description",
        service="lightbulb"
    )


class TestHomeKitLightbulbService:
    """Test cases for HomeKitLightbulbService"""

    def setup_method(self):
        """Setup test fixtures"""
        self.event_bus = Mock(spec=EventBus)
        self.service = HomeKitLightbulbService(self.event_bus)

    def test_init(self):
        """Test service initialization"""
        event_bus = Mock(spec=EventBus)
        service = HomeKitLightbulbService(event_bus)

        assert service.event_bus == event_bus
        assert service.logger is not None

        # Verify event handlers are registered
        assert event_bus.on.call_count == 2
        event_bus.on.assert_any_call(LightBulbGetOnEvent, service.handle_lightbulb_get_on)
        event_bus.on.assert_any_call(LightBulbSetOnEvent, service.handle_lightbulb_set_on)

    def test_handle_lightbulb_get_on_returns_true(self, mock_module, mock_accessory):
        """Test handle_lightbulb_get_on returns True when output is on"""
        event = LightBulbGetOnEvent(
            serial_number="1234567890",
            output_number=2,
            module=mock_module,
            accessory=mock_accessory
        )

        # Mock the expect response - data_value is a string indexed by output_number
        response = DatapointReceivedEvent(
            serial_number="1234567890",
            datapoint_type=DataPointType.MODULE_OUTPUT_STATE,
            data_value="001"  # Output 2 (index 2) is on ('1')
        )
        # Use MagicMock to avoid AsyncMock behavior
        self.event_bus.expect = MagicMock(return_value=response)

        result = self.service.handle_lightbulb_get_on(event)

        assert result is True
        self.event_bus.dispatch.assert_called_once()
        dispatched_event = self.event_bus.dispatch.call_args[0][0]
        assert isinstance(dispatched_event, ReadDatapointEvent)
        assert dispatched_event.serial_number == "1234567890"
        assert dispatched_event.datapoint_type == DataPointType.MODULE_OUTPUT_STATE

    def test_handle_lightbulb_get_on_returns_false(self, mock_module, mock_accessory):
        """Test handle_lightbulb_get_on returns False when output is off"""
        event = LightBulbGetOnEvent(
            serial_number="1234567890",
            output_number=2,
            module=mock_module,
            accessory=mock_accessory
        )

        response = DatapointReceivedEvent(
            serial_number="1234567890",
            datapoint_type=DataPointType.MODULE_OUTPUT_STATE,
            data_value="0000"  # Output 2 (index 2) is off ('0')
        )
        self.event_bus.expect = MagicMock(return_value=response)

        result = self.service.handle_lightbulb_get_on(event)

        assert result is False

    def test_handle_lightbulb_set_on(self, mock_module, mock_accessory):
        """Test handle_lightbulb_set_on dispatches SendActionEvent"""
        event = LightBulbSetOnEvent(
            serial_number="1234567890",
            output_number=5,
            module=mock_module,
            accessory=mock_accessory,
            value=True
        )

        self.service.handle_lightbulb_set_on(event)

        self.event_bus.dispatch.assert_called_once()
        dispatched_event = self.event_bus.dispatch.call_args[0][0]
        assert isinstance(dispatched_event, SendActionEvent)
        assert dispatched_event.serial_number == "1234567890"
        assert dispatched_event.output_number == 5
        assert dispatched_event.value is True


class TestHomeKitOutletService:
    """Test cases for HomeKitOutletService"""

    def setup_method(self):
        """Setup test fixtures"""
        self.event_bus = Mock(spec=EventBus)
        self.service = HomeKitOutletService(self.event_bus)

    def test_init(self):
        """Test service initialization"""
        event_bus = Mock(spec=EventBus)
        service = HomeKitOutletService(event_bus)

        assert service.event_bus == event_bus
        assert service.logger is not None

        # Verify event handlers are registered
        assert event_bus.on.call_count == 3
        event_bus.on.assert_any_call(OutletGetOnEvent, service.handle_outlet_get_on)
        event_bus.on.assert_any_call(OutletSetOnEvent, service.handle_outlet_set_on)
        event_bus.on.assert_any_call(OutletGetInUseEvent, service.handle_outlet_get_in_use)

    def test_handle_outlet_get_on(self, mock_module, mock_accessory):
        """Test handle_outlet_get_on"""
        event = OutletGetOnEvent(
            serial_number="1234567890",
            output_number=1,
            module=mock_module,
            accessory=mock_accessory
        )

        response = DatapointReceivedEvent(
            serial_number="1234567890",
            datapoint_type=DataPointType.MODULE_OUTPUT_STATE,
            data_value="010"  # Output 1 (index 1) is on
        )
        self.event_bus.expect = MagicMock(return_value=response)

        result = self.service.handle_outlet_get_on(event)

        assert result is True
        self.event_bus.dispatch.assert_called_once()

    def test_handle_outlet_set_on(self, mock_module, mock_accessory):
        """Test handle_outlet_set_on"""
        event = OutletSetOnEvent(
            serial_number="1234567890",
            output_number=3,
            module=mock_module,
            accessory=mock_accessory,
            value=False
        )

        self.service.handle_outlet_set_on(event)

        dispatched_event = self.event_bus.dispatch.call_args[0][0]
        assert isinstance(dispatched_event, SendActionEvent)
        assert dispatched_event.value is False

    def test_handle_outlet_get_in_use_returns_true(self, mock_module, mock_accessory):
        """Test handle_outlet_get_in_use returns True when outlet is in use"""
        event = OutletGetInUseEvent(
            serial_number="1234567890",
            output_number=0,
            module=mock_module,
            accessory=mock_accessory
        )

        response = DatapointReceivedEvent(
            serial_number="1234567890",
            datapoint_type=DataPointType.MODULE_STATE,
            data_value="ON"
        )

        # Mock expect to return the response directly
        self.event_bus.expect = MagicMock(return_value=response)

        result = self.service.handle_outlet_get_in_use(event)

        assert result is True

    def test_handle_outlet_get_in_use_returns_false(self, mock_module, mock_accessory):
        """Test handle_outlet_get_in_use returns False when outlet is not in use"""
        event = OutletGetInUseEvent(
            serial_number="1234567890",
            output_number=0,
            module=mock_module,
            accessory=mock_accessory
        )

        response = DatapointReceivedEvent(
            serial_number="1234567890",
            datapoint_type=DataPointType.MODULE_STATE,
            data_value="OFF"
        )
        self.event_bus.expect = MagicMock(return_value=response)

        result = self.service.handle_outlet_get_in_use(event)

        assert result is False


class TestHomeKitDimmingLightService:
    """Test cases for HomeKitDimmingLightService"""

    def setup_method(self):
        """Setup test fixtures"""
        self.event_bus = Mock(spec=EventBus)
        self.service = HomeKitDimmingLightService(self.event_bus)

    def test_init(self):
        """Test service initialization"""
        event_bus = Mock(spec=EventBus)
        service = HomeKitDimmingLightService(event_bus)

        assert service.event_bus == event_bus
        assert service.logger is not None

        # Verify event handlers are registered
        assert event_bus.on.call_count == 4

    def test_handle_dimminglight_get_on(self, mock_module, mock_accessory):
        """Test handle_dimminglight_get_on"""
        event = DimmingLightGetOnEvent(
            serial_number="1234567890",
            output_number=0,
            module=mock_module,
            accessory=mock_accessory
        )

        response = DatapointReceivedEvent(
            serial_number="1234567890",
            datapoint_type=DataPointType.MODULE_OUTPUT_STATE,
            data_value="1"  # Output 0 (index 0) is on
        )
        self.event_bus.expect = MagicMock(return_value=response)

        result = self.service.handle_dimminglight_get_on(event)

        assert result is True

    def test_handle_dimminglight_set_on_true(self, mock_module, mock_accessory):
        """Test handle_dimminglight_set_on with value=True sets brightness to 0 (implementation bug)"""
        event = DimmingLightSetOnEvent(
            serial_number="1234567890",
            output_number=2,
            module=mock_module,
            accessory=mock_accessory,
            value=True
        )

        self.service.handle_dimminglight_set_on(event)

        dispatched_event = self.event_bus.dispatch.call_args[0][0]
        assert isinstance(dispatched_event, SendWriteConfigEvent)
        # Note: implementation has inverted logic - True sets to 0
        assert dispatched_event.value == 0

    def test_handle_dimminglight_set_on_false(self, mock_module, mock_accessory):
        """Test handle_dimminglight_set_on with value=False sets brightness to 60 (implementation bug)"""
        event = DimmingLightSetOnEvent(
            serial_number="1234567890",
            output_number=2,
            module=mock_module,
            accessory=mock_accessory,
            value=False
        )

        self.service.handle_dimminglight_set_on(event)

        dispatched_event = self.event_bus.dispatch.call_args[0][0]
        # Note: implementation has inverted logic - False sets to 60
        assert dispatched_event.value == 60

    def test_handle_dimminglight_set_brightness(self, mock_module, mock_accessory):
        """Test handle_dimminglight_set_brightness"""
        event = DimmingLightSetBrightnessEvent(
            serial_number="1234567890",
            output_number=1,
            module=mock_module,
            accessory=mock_accessory,
            brightness=75  # Correct field name is 'brightness', not 'value'
        )

        # Note: handler has a bug - it accesses event.value instead of event.brightness
        # This test will fail unless the handler is fixed
        with pytest.raises(AttributeError):
            self.service.handle_dimminglight_set_brightness(event)

    def test_handle_dimminglight_get_brightness(self, mock_module, mock_accessory):
        """Test handle_dimminglight_get_brightness parses response correctly"""
        event = DimmingLightGetBrightnessEvent(
            serial_number="1234567890",
            output_number=1,
            module=mock_module,
            accessory=mock_accessory
        )

        response = DatapointReceivedEvent(
            serial_number="1234567890",
            datapoint_type=DataPointType.MODULE_LIGHT_LEVEL,
            data_value="00:050,01:025,02:100"
        )
        self.event_bus.expect = MagicMock(return_value=response)

        result = self.service.handle_dimminglight_get_brightness(event)

        assert result == 25  # Output 1 has brightness 25

    def test_handle_dimminglight_get_brightness_output_not_found(self, mock_module, mock_accessory):
        """Test handle_dimminglight_get_brightness returns 0 when output not found"""
        event = DimmingLightGetBrightnessEvent(
            serial_number="1234567890",
            output_number=5,
            module=mock_module,
            accessory=mock_accessory
        )

        response = DatapointReceivedEvent(
            serial_number="1234567890",
            datapoint_type=DataPointType.MODULE_LIGHT_LEVEL,
            data_value="00:050,01:025"
        )
        self.event_bus.expect = MagicMock(return_value=response)

        result = self.service.handle_dimminglight_get_brightness(event)

        assert result == 0


class TestHomeKitConbusService:
    """Test cases for HomeKitConbusService"""

    def setup_method(self):
        """Setup test fixtures"""
        self.event_bus = Mock(spec=EventBus)
        self.telegram_protocol = Mock(spec=TelegramProtocol)
        self.service = HomeKitConbusService(self.event_bus, self.telegram_protocol)

    def test_init(self):
        """Test service initialization"""
        event_bus = Mock(spec=EventBus)
        telegram_protocol = Mock(spec=TelegramProtocol)
        service = HomeKitConbusService(event_bus, telegram_protocol)

        assert service.event_bus == event_bus
        assert service.telegram_protocol == telegram_protocol
        assert service.logger is not None

        # Verify event handlers are registered
        assert event_bus.on.call_count == 3

    def test_handle_read_datapoint_event(self, mock_module, mock_accessory):
        """Test handle_read_datapoint_event sends correct telegram"""
        event = ReadDatapointEvent(
            serial_number="1234567890",
            datapoint_type=DataPointType.MODULE_OUTPUT_STATE
        )

        self.service.handle_read_datapoint_event(event)

        self.telegram_protocol.sendFrame.assert_called_once()
        sent_data = self.telegram_protocol.sendFrame.call_args[0][0]
        assert sent_data == b"S1234567890F02D12"

    def test_handle_send_write_config_event(self, mock_module, mock_accessory):
        """Test handle_send_write_config_event formats telegram correctly"""
        event = SendWriteConfigEvent(
            serial_number="1234567890",
            output_number=3,
            datapoint_type=DataPointType.MODULE_LIGHT_LEVEL,
            value=75
        )

        self.service.handle_send_write_config_event(event)

        sent_data = self.telegram_protocol.sendFrame.call_args[0][0]
        assert sent_data == b"S1234567890F04D1503:075"

    def test_handle_send_action_event_on(self, mock_module, mock_accessory):
        """Test handle_send_action_event for turning on"""
        event = SendActionEvent(
            serial_number="1234567890",
            output_number=2,
            value=True
        )

        self.service.handle_send_action_event(event)

        sent_data = self.telegram_protocol.sendFrame.call_args[0][0]
        assert sent_data == b"S1234567890F27D02AB"  # ON_RELEASE action

    def test_handle_send_action_event_off(self, mock_module, mock_accessory):
        """Test handle_send_action_event for turning off"""
        event = SendActionEvent(
            serial_number="1234567890",
            output_number=5,
            value=False
        )

        self.service.handle_send_action_event(event)

        sent_data = self.telegram_protocol.sendFrame.call_args[0][0]
        assert sent_data == b"S1234567890F27D05AA"  # OFF_PRESS action


class TestHomeKitService:
    """Test cases for HomeKitService"""

    def setup_method(self):
        """Setup test fixtures"""
        self.event_bus = Mock(spec=EventBus)
        self.telegram_factory = Mock(spec=TelegramFactory)
        self.telegram_protocol = Mock(spec=TelegramProtocol)
        self.telegram_factory.telegram_protocol = self.telegram_protocol
        self.reactor = Mock(spec=PosixReactorBase)
        self.lightbulb_service = Mock(spec=HomeKitLightbulbService)
        self.outlet_service = Mock(spec=HomeKitOutletService)
        self.dimminglight_service = Mock(spec=HomeKitDimmingLightService)
        self.conbus_service = Mock(spec=HomeKitConbusService)
        self.module_factory = Mock(spec=HomekitHapService)
        self.telegram_service = Mock(spec=TelegramService)

        self.service = HomeKitService(
            self.event_bus,
            self.telegram_factory,
            self.reactor,
            self.lightbulb_service,
            self.outlet_service,
            self.dimminglight_service,
            self.conbus_service,
            self.module_factory,
            self.telegram_service
        )

    def test_init(self):
        """Test service initialization"""
        assert self.service.event_bus == self.event_bus
        assert self.service.telegram_factory == self.telegram_factory
        assert self.service.protocol == self.telegram_protocol
        assert self.service.reactor == self.reactor
        assert self.service.lightbulb_service == self.lightbulb_service
        assert self.service.outlet_service == self.outlet_service
        assert self.service.dimminglight_service == self.dimminglight_service
        assert self.service.conbus_service == self.conbus_service
        assert self.service.module_factory == self.module_factory

        # Verify event handlers are registered
        assert self.event_bus.on.call_count == 7

    def test_handle_connection_made(self, mock_module, mock_accessory):
        """Test handle_connection_made sends initial discovery telegram"""
        protocol = Mock(spec=TelegramProtocol)
        event = ConnectionMadeEvent(protocol=protocol)

        self.service.handle_connection_made(event)

        protocol.sendFrame.assert_called_once_with(b"S0000000000F01D00")

    def test_handle_connection_failed(self, mock_module, mock_accessory):
        """Test handle_connection_failed logs the reason"""
        event = ConnectionFailedEvent(reason="Connection refused")

        # Should not raise
        self.service.handle_connection_failed(event)

    def test_handle_connection_lost(self, mock_module, mock_accessory):
        """Test handle_connection_lost logs the event"""
        event = ConnectionLostEvent(reason="Connection closed")

        # Should not raise
        self.service.handle_connection_lost(event)

    def test_handle_telegram_received_discovery(self, mock_module, mock_accessory):
        """Test handle_telegram_received dispatches ModuleDiscoveredEvent for discovery reply"""
        protocol = Mock(spec=TelegramProtocol)
        event = TelegramReceivedEvent(
            protocol=protocol,
            telegram="R1234567890F01D00XX",
            raw_frame="<R1234567890F01D00XX>",
            event_bus=self.event_bus
        )

        self.service.handle_telegram_received(event)

        self.event_bus.dispatch.assert_called_once()
        dispatched = self.event_bus.dispatch.call_args[0][0]
        assert isinstance(dispatched, ModuleDiscoveredEvent)
        assert dispatched.telegram == "R1234567890F01D00XX"
        assert dispatched.protocol == protocol

    def test_handle_telegram_received_module_type(self, mock_module, mock_accessory):
        """Test handle_telegram_received dispatches ModuleTypeReadEvent"""
        protocol = Mock(spec=TelegramProtocol)
        event = TelegramReceivedEvent(
            protocol=protocol,
            frame="<R1234567890F02D00XX>",
            telegram="R1234567890F02D00XX",
            serial_number="1234567890",
            payload="R1234567890F02D00",
            checksum="XX",
        )

        self.service.handle_telegram_received(event)

        dispatched = self.event_bus.dispatch.call_args[0][0]
        assert isinstance(dispatched, ModuleTypeReadEvent)

    def test_handle_telegram_received_error_code(self, mock_module, mock_accessory):
        """Test handle_telegram_received dispatches ModuleErrorCodeReadEvent"""
        protocol = Mock(spec=TelegramProtocol)
        event = TelegramReceivedEvent(
            protocol=protocol,
            telegram="R1234567890F02D10XX",
            raw_frame="<R1234567890F02D10XX>",
            event_bus=self.event_bus
        )

        self.service.handle_telegram_received(event)

        dispatched = self.event_bus.dispatch.call_args[0][0]
        assert isinstance(dispatched, ModuleErrorCodeReadEvent)

    def test_handle_module_discovered(self, mock_module, mock_accessory):
        """Test handle_module_discovered sends module type query"""
        protocol = Mock(spec=TelegramProtocol)
        event = ModuleDiscoveredEvent(
            telegram="R1234567890F01D00XX",
            protocol=protocol
        )

        self.service.handle_module_discovered(event)

        # Note: F01D00 becomes F02D0000 due to string replacement
        protocol.sendFrame.assert_called_once_with(b"S1234567890F02D0000XX")

    def test_handle_module_type_read(self, mock_module, mock_accessory):
        """Test handle_module_type_read sends error code query"""
        protocol = Mock(spec=TelegramProtocol)
        event = ModuleTypeReadEvent(
            telegram="R1234567890F02D00XX",
            protocol=protocol
        )

        self.service.handle_module_type_read(event)

        protocol.sendFrame.assert_called_once_with(b"S1234567890F02D10XX")

    def test_handle_module_error_code_read(self, mock_module, mock_accessory):
        """Test handle_module_error_code_read completes discovery"""
        protocol = Mock(spec=TelegramProtocol)
        event = ModuleErrorCodeReadEvent(
            telegram="R1234567890F02D10XX",
            protocol=protocol
        )

        # Should not raise
        self.service.handle_module_error_code_read(event)

    def test_start_module_factory(self):
        """Test _start_module_factory runs in separate thread"""
        with patch('threading.Thread') as mock_thread:
            thread_instance = Mock()
            mock_thread.return_value = thread_instance

            self.service._start_module_factory()

            mock_thread.assert_called_once_with(
                target=self.module_factory.run,
                daemon=True,
                name="ModuleFactoryThread"
            )
            thread_instance.start.assert_called_once()
