"""Unit tests for HomeKit services."""

from unittest.mock import Mock, patch

import pytest
from bubus import EventBus
from twisted.internet.posixbase import PosixReactorBase

from xp.models import ConbusClientConfig
from xp.models.homekit.homekit_config import HomekitAccessoryConfig
from xp.models.homekit.homekit_conson_config import ConsonModuleConfig
from xp.models.protocol.conbus_protocol import (
    ConnectionFailedEvent,
    ConnectionLostEvent,
    ConnectionMadeEvent,
    DimmingLightGetBrightnessEvent,
    DimmingLightGetOnEvent,
    DimmingLightSetBrightnessEvent,
    DimmingLightSetOnEvent,
    LightBulbGetOnEvent,
    LightBulbSetOnEvent,
    LightLevelReceivedEvent,
    ModuleDiscoveredEvent,
    ModuleStateChangedEvent,
    OutletGetInUseEvent,
    OutletGetOnEvent,
    OutletSetOnEvent,
    OutputStateReceivedEvent,
    ReadDatapointEvent,
    ReadDatapointFromProtocolEvent,
    SendActionEvent,
    SendWriteConfigEvent,
    TelegramReceivedEvent,
)
from xp.models.telegram.datapoint_type import DataPointType
from xp.services import TelegramService
from xp.services.homekit.homekit_cache_service import HomeKitCacheService
from xp.services.homekit.homekit_conbus_service import HomeKitConbusService
from xp.services.homekit.homekit_dimminglight_service import HomeKitDimmingLightService
from xp.services.homekit.homekit_hap_service import HomekitHapService
from xp.services.homekit.homekit_lightbulb_service import HomeKitLightbulbService
from xp.services.homekit.homekit_outlet_service import HomeKitOutletService
from xp.services.homekit.homekit_service import HomeKitService
from xp.services.protocol.protocol_factory import TelegramFactory
from xp.services.protocol.telegram_protocol import TelegramProtocol


# Test fixtures
@pytest.fixture
def mock_module():
    """Create mock ConsonModuleConfig for testing."""
    return ConsonModuleConfig(
        name="Test Module",
        serial_number="1234567890",
        module_type="XP24",
        module_type_code=24,
        link_number=1,
    )


@pytest.fixture
def mock_accessory():
    """Create mock HomekitAccessoryConfig for testing."""
    return HomekitAccessoryConfig(
        name="Test Accessory",
        id="test_id",
        serial_number="1234567890",
        output_number=2,
        description="Test Description",
        service="lightbulb",
        on_action="E00L01I01",
        off_action="E00L01I05",
    )


class TestHomeKitLightbulbService:
    """Test cases for HomeKitLightbulbService."""

    def setup_method(self):
        """Set up test fixtures."""
        self.event_bus = Mock(spec=EventBus)
        self.service = HomeKitLightbulbService(self.event_bus)

    def test_init(self):
        """Test service initialization."""
        event_bus = Mock(spec=EventBus)
        service = HomeKitLightbulbService(event_bus)

        assert service.event_bus == event_bus
        assert service.logger is not None

        # Verify event handlers are registered
        assert event_bus.on.call_count == 2
        event_bus.on.assert_any_call(
            LightBulbGetOnEvent, service.handle_lightbulb_get_on
        )
        event_bus.on.assert_any_call(
            LightBulbSetOnEvent, service.handle_lightbulb_set_on
        )

    def test_handle_lightbulb_get_on_dispatches_read_event(
        self, mock_module, mock_accessory
    ):
        """Test handle_lightbulb_get_on dispatches ReadDatapointEvent."""
        event = LightBulbGetOnEvent(
            serial_number="1234567890",
            output_number=2,
            module=mock_module,
            accessory=mock_accessory,
        )

        self.service.handle_lightbulb_get_on(event)

        self.event_bus.dispatch.assert_called_once()
        dispatched_event = self.event_bus.dispatch.call_args[0][0]
        assert isinstance(dispatched_event, ReadDatapointEvent)
        assert dispatched_event.serial_number == "1234567890"
        assert dispatched_event.datapoint_type == DataPointType.MODULE_OUTPUT_STATE

    def test_handle_lightbulb_set_on(self, mock_module, mock_accessory):
        """Test handle_lightbulb_set_on dispatches SendActionEvent."""
        event = LightBulbSetOnEvent(
            serial_number="1234567890",
            output_number=5,
            module=mock_module,
            accessory=mock_accessory,
            value=True,
        )

        self.service.handle_lightbulb_set_on(event)

        self.event_bus.dispatch.assert_called_once()
        dispatched_event = self.event_bus.dispatch.call_args[0][0]
        assert isinstance(dispatched_event, SendActionEvent)
        assert dispatched_event.serial_number == "1234567890"
        assert dispatched_event.output_number == 5
        assert dispatched_event.value is True


class TestHomeKitOutletService:
    """Test cases for HomeKitOutletService."""

    def setup_method(self):
        """Set up test fixtures."""
        self.event_bus = Mock(spec=EventBus)
        self.service = HomeKitOutletService(self.event_bus)

    def test_init(self):
        """Test service initialization."""
        event_bus = Mock(spec=EventBus)
        service = HomeKitOutletService(event_bus)

        assert service.event_bus == event_bus
        assert service.logger is not None

        # Verify event handlers are registered
        assert event_bus.on.call_count == 3
        event_bus.on.assert_any_call(OutletGetOnEvent, service.handle_outlet_get_on)
        event_bus.on.assert_any_call(OutletSetOnEvent, service.handle_outlet_set_on)
        event_bus.on.assert_any_call(
            OutletGetInUseEvent, service.handle_outlet_get_in_use
        )

    def test_handle_outlet_get_on(self, mock_module, mock_accessory):
        """Test handle_outlet_get_on dispatches ReadDatapointEvent."""
        event = OutletGetOnEvent(
            serial_number="1234567890",
            output_number=1,
            module=mock_module,
            accessory=mock_accessory,
        )

        self.service.handle_outlet_get_on(event)

        self.event_bus.dispatch.assert_called_once()
        dispatched_event = self.event_bus.dispatch.call_args[0][0]
        assert isinstance(dispatched_event, ReadDatapointEvent)
        assert dispatched_event.datapoint_type == DataPointType.MODULE_OUTPUT_STATE

    def test_handle_outlet_set_on(self, mock_module, mock_accessory):
        """Test handle_outlet_set_on."""
        event = OutletSetOnEvent(
            serial_number="1234567890",
            output_number=3,
            module=mock_module,
            accessory=mock_accessory,
            value=False,
        )

        self.service.handle_outlet_set_on(event)

        dispatched_event = self.event_bus.dispatch.call_args[0][0]
        assert isinstance(dispatched_event, SendActionEvent)
        assert dispatched_event.value is False

    def test_handle_outlet_get_in_use(self, mock_module, mock_accessory):
        """Test handle_outlet_get_in_use dispatches ReadDatapointEvent."""
        event = OutletGetInUseEvent(
            serial_number="1234567890",
            output_number=0,
            module=mock_module,
            accessory=mock_accessory,
        )

        self.service.handle_outlet_get_in_use(event)

        self.event_bus.dispatch.assert_called_once()
        dispatched_event = self.event_bus.dispatch.call_args[0][0]
        assert isinstance(dispatched_event, ReadDatapointEvent)
        assert dispatched_event.datapoint_type == DataPointType.MODULE_STATE


class TestHomeKitDimmingLightService:
    """Test cases for HomeKitDimmingLightService."""

    def setup_method(self):
        """Set up test fixtures."""
        self.event_bus = Mock(spec=EventBus)
        self.service = HomeKitDimmingLightService(self.event_bus)

    def test_init(self):
        """Test service initialization."""
        event_bus = Mock(spec=EventBus)
        service = HomeKitDimmingLightService(event_bus)

        assert service.event_bus == event_bus
        assert service.logger is not None

        # Verify event handlers are registered
        assert event_bus.on.call_count == 4

    def test_handle_dimminglight_get_on(self, mock_module, mock_accessory):
        """Test handle_dimminglight_get_on dispatches ReadDatapointEvent."""
        event = DimmingLightGetOnEvent(
            serial_number="1234567890",
            output_number=0,
            module=mock_module,
            accessory=mock_accessory,
        )

        self.service.handle_dimminglight_get_on(event)

        self.event_bus.dispatch.assert_called_once()
        dispatched_event = self.event_bus.dispatch.call_args[0][0]
        assert isinstance(dispatched_event, ReadDatapointEvent)
        assert dispatched_event.datapoint_type == DataPointType.MODULE_OUTPUT_STATE

    def test_handle_dimminglight_set_on_true(self, mock_module, mock_accessory):
        """Test handle_dimminglight_set_on with value=True sets brightness to the provided brightness."""
        event = DimmingLightSetOnEvent(
            serial_number="1234567890",
            output_number=2,
            module=mock_module,
            accessory=mock_accessory,
            value=True,
            brightness=60,
        )

        self.service.handle_dimminglight_set_on(event)

        dispatched_event = self.event_bus.dispatch.call_args[0][0]
        assert isinstance(dispatched_event, SendWriteConfigEvent)
        # When value is True, it should use the provided brightness
        assert dispatched_event.value == 60

    def test_handle_dimminglight_set_on_false(self, mock_module, mock_accessory):
        """Test handle_dimminglight_set_on with value=False sets brightness to 0."""
        event = DimmingLightSetOnEvent(
            serial_number="1234567890",
            output_number=2,
            module=mock_module,
            accessory=mock_accessory,
            value=False,
            brightness=75,
        )

        self.service.handle_dimminglight_set_on(event)

        dispatched_event = self.event_bus.dispatch.call_args[0][0]
        # When value is False, brightness should be set to 0
        assert dispatched_event.value == 0

    def test_handle_dimminglight_set_brightness(self, mock_module, mock_accessory):
        """Test handle_dimminglight_set_brightness dispatches SendWriteConfigEvent."""
        event = DimmingLightSetBrightnessEvent(
            serial_number="1234567890",
            output_number=1,
            module=mock_module,
            accessory=mock_accessory,
            brightness=75,
        )

        self.service.handle_dimminglight_set_brightness(event)

        self.event_bus.dispatch.assert_called_once()
        dispatched_event = self.event_bus.dispatch.call_args[0][0]
        assert isinstance(dispatched_event, SendWriteConfigEvent)
        assert dispatched_event.value == 75

    def test_handle_dimminglight_get_brightness(self, mock_module, mock_accessory):
        """Test handle_dimminglight_get_brightness dispatches ReadDatapointEvent."""
        event = DimmingLightGetBrightnessEvent(
            serial_number="1234567890",
            output_number=1,
            module=mock_module,
            accessory=mock_accessory,
        )

        self.service.handle_dimminglight_get_brightness(event)

        self.event_bus.dispatch.assert_called_once()
        dispatched_event = self.event_bus.dispatch.call_args[0][0]
        assert isinstance(dispatched_event, ReadDatapointEvent)
        assert dispatched_event.datapoint_type == DataPointType.MODULE_LIGHT_LEVEL


class TestHomeKitConbusService:
    """Test cases for HomeKitConbusService."""

    def setup_method(self):
        """Set up test fixtures."""
        self.event_bus = Mock(spec=EventBus)
        self.telegram_protocol = Mock(spec=TelegramProtocol)
        self.service = HomeKitConbusService(self.event_bus, self.telegram_protocol)

    def test_init(self):
        """Test service initialization."""
        event_bus = Mock(spec=EventBus)
        telegram_protocol = Mock(spec=TelegramProtocol)
        service = HomeKitConbusService(event_bus, telegram_protocol)

        assert service.event_bus == event_bus
        assert service.telegram_protocol == telegram_protocol
        assert service.logger is not None

        # Verify event handlers are registered
        assert event_bus.on.call_count == 3
        event_bus.on.assert_any_call(
            ReadDatapointFromProtocolEvent, service.handle_read_datapoint_request
        )
        event_bus.on.assert_any_call(SendActionEvent, service.handle_send_action_event)
        event_bus.on.assert_any_call(
            SendWriteConfigEvent, service.handle_send_write_config_event
        )

    def test_handle_send_write_config_event(self, mock_module, mock_accessory):
        """Test handle_send_write_config_event formats telegram correctly."""
        event = SendWriteConfigEvent(
            serial_number="1234567890",
            output_number=3,
            datapoint_type=DataPointType.MODULE_LIGHT_LEVEL,
            value=75,
        )

        self.service.handle_send_write_config_event(event)

        sent_data = self.telegram_protocol.sendFrame.call_args[0][0]
        assert sent_data == b"S1234567890F04D1503:075"

    def test_handle_send_action_event_on(self, mock_module, mock_accessory):
        """Test handle_send_action_event for turning on."""
        event = SendActionEvent(
            serial_number="1234567890",
            output_number=2,
            value=True,
            on_action="E00L04I02",
            off_action="E00L04I06",
        )

        self.service.handle_send_action_event(event)

        sent_data = self.telegram_protocol.sendFrame.call_args[0][0]
        assert sent_data == b"E00L04I02B"  # ON action code

    def test_handle_send_action_event_off(self, mock_module, mock_accessory):
        """Test handle_send_action_event for turning off."""
        event = SendActionEvent(
            serial_number="1234567890",
            output_number=5,
            value=False,
            on_action="E00L05I05",
            off_action="E00L05I09",
        )

        self.service.handle_send_action_event(event)

        sent_data = self.telegram_protocol.sendFrame.call_args[0][0]
        assert sent_data == b"E00L05I09B"  # OFF action code


class TestHomeKitService:
    """Test cases for HomeKitService."""

    def setup_method(self):
        """Set up test fixtures."""
        self.cli_config = Mock(spec=ConbusClientConfig)
        self.cli_config.conbus = (
            Mock()
        )  # Add the conbus attribute that HomeKitService expects
        self.event_bus = Mock(spec=EventBus)
        self.telegram_factory = Mock(spec=TelegramFactory)
        self.telegram_protocol = Mock(spec=TelegramProtocol)
        self.telegram_factory.telegram_protocol = self.telegram_protocol
        self.reactor = Mock(spec=PosixReactorBase)
        self.lightbulb_service = Mock(spec=HomeKitLightbulbService)
        self.outlet_service = Mock(spec=HomeKitOutletService)
        self.dimminglight_service = Mock(spec=HomeKitDimmingLightService)
        self.cache_service = Mock(spec=HomeKitCacheService)
        self.conbus_service = Mock(spec=HomeKitConbusService)
        self.module_factory = Mock(spec=HomekitHapService)
        self.telegram_service = Mock(spec=TelegramService)

        self.service = HomeKitService(
            self.cli_config,
            self.event_bus,
            self.telegram_factory,
            self.reactor,
            self.lightbulb_service,
            self.outlet_service,
            self.dimminglight_service,
            self.cache_service,
            self.conbus_service,
            self.module_factory,
            self.telegram_service,
        )

    def test_init(self):
        """Test service initialization."""
        assert self.service.cli_config == self.cli_config.conbus
        assert self.service.event_bus == self.event_bus
        assert self.service.telegram_factory == self.telegram_factory
        assert self.service.protocol == self.telegram_protocol
        assert self.service.reactor == self.reactor
        assert self.service.lightbulb_service == self.lightbulb_service
        assert self.service.outlet_service == self.outlet_service
        assert self.service.dimminglight_service == self.dimminglight_service
        assert self.service.cache_service == self.cache_service
        assert self.service.conbus_service == self.conbus_service
        assert self.service.module_factory == self.module_factory

        # Verify event handlers are registered
        assert self.event_bus.on.call_count == 5

    def test_handle_connection_made(self, mock_module, mock_accessory):
        """Test handle_connection_made sends initial discovery telegram."""
        protocol = Mock(spec=TelegramProtocol)
        event = ConnectionMadeEvent(protocol=protocol)

        self.service.handle_connection_made(event)

        protocol.sendFrame.assert_called_once_with(b"S0000000000F01D00")

    def test_handle_connection_failed(self, mock_module, mock_accessory):
        """Test handle_connection_failed logs the reason."""
        event = ConnectionFailedEvent(reason="Connection refused")

        # Should not raise
        self.service.handle_connection_failed(event)

    def test_handle_connection_lost(self, mock_module, mock_accessory):
        """Test handle_connection_lost logs the event."""
        event = ConnectionLostEvent(reason="Connection closed")

        # Should not raise
        self.service.handle_connection_lost(event)

    def test_handle_telegram_received_discovery(self, mock_module, mock_accessory):
        """Test handle_telegram_received dispatches ModuleDiscoveredEvent for discovery reply."""
        protocol = Mock(spec=TelegramProtocol)
        event = TelegramReceivedEvent(
            protocol=protocol,
            telegram="R1234567890F01D00XX",
            frame="<R1234567890F01D00XX>",
            payload="R1234567890F01D00",
            telegram_type="R",
            serial_number="1234567890",
            checksum="XX",
        )

        self.service.handle_telegram_received(event)

        self.event_bus.dispatch.assert_called_once()
        dispatched = self.event_bus.dispatch.call_args[0][0]
        assert isinstance(dispatched, ModuleDiscoveredEvent)
        assert dispatched.telegram == "R1234567890F01D00XX"
        assert dispatched.protocol == protocol

    def test_handle_module_discovered(self, mock_module, mock_accessory):
        """Test handle_module_discovered sends module type query."""
        protocol = Mock(spec=TelegramProtocol)
        event = ModuleDiscoveredEvent(
            telegram="R1234567890F01D00XX",
            protocol=protocol,
            frame="<R1234567890F01D00XX>",
            payload="R1234567890F01D00",
            telegram_type="R",
            serial_number="1234567890",
            checksum="XX",
        )

        self.service.handle_module_discovered(event)

        # Note: F01D00 becomes F02D0000 due to string replacement
        protocol.sendFrame.assert_called_once_with(b"S1234567890F02D0000XX")

    def test_start_module_factory(self):
        """Test _start_module_factory creates async task."""
        with patch("asyncio.create_task") as mock_create_task:
            mock_task = Mock()
            mock_create_task.return_value = mock_task

            self.service._start_module_factory()

            # Should have created an async task
            mock_create_task.assert_called_once()
            # Should have added a done callback to the task
            mock_task.add_done_callback.assert_called_once()


class TestHomekitHapServiceModuleRegistry:
    """Test cases for HomekitHapService module registry and state change handling."""

    def setup_method(self):
        """Set up test fixtures."""
        from unittest.mock import MagicMock, patch

        # Create mock event bus
        self.event_bus = Mock(spec=EventBus)

        # Create mock homekit config with proper nested structure
        self.homekit_config = MagicMock()
        self.homekit_config.homekit.port = 51826
        self.homekit_config.bridge.name = "Test Bridge"
        self.homekit_config.bridge.rooms = []
        self.homekit_config.accessories = []

        # Create mock module service
        from xp.services.homekit.homekit_module_service import HomekitModuleService

        self.module_service = Mock(spec=HomekitModuleService)

        # Patch AccessoryDriver to prevent actual HAP-python initialization
        with patch("xp.services.homekit.homekit_hap_service.AccessoryDriver"):
            # Create HAP service
            self.hap_service = HomekitHapService(
                self.homekit_config, self.module_service, self.event_bus
            )

    def test_module_registry_initialization(self):
        """Test that module_registry is initialized as empty dict."""
        assert self.hap_service.module_registry == {}
        assert self.hap_service.accessory_registry == {}

    def test_module_state_changed_event_subscription(self):
        """Test that HAP service subscribes to ModuleStateChangedEvent."""
        # Verify event handler is registered
        self.event_bus.on.assert_any_call(
            ModuleStateChangedEvent, self.hap_service.handle_module_state_changed
        )

    def test_output_state_received_event_subscription(self):
        """Test that HAP service subscribes to OutputStateReceivedEvent."""
        # Verify event handler is registered
        self.event_bus.on.assert_any_call(
            OutputStateReceivedEvent, self.hap_service.handle_output_state_received
        )

    def test_light_level_received_event_subscription(self):
        """Test that HAP service subscribes to LightLevelReceivedEvent."""
        # Verify event handler is registered
        self.event_bus.on.assert_any_call(
            LightLevelReceivedEvent, self.hap_service.handle_light_level_received
        )

    def test_handle_module_state_changed_no_accessories(self):
        """Test handle_module_state_changed when no accessories are registered."""
        event = ModuleStateChangedEvent(
            module_type_code=24, link_number=1, input_number=0, telegram_event_type="M"
        )

        # Should not raise, should not dispatch any events
        self.hap_service.handle_module_state_changed(event)

        # Should not dispatch any events
        self.event_bus.dispatch.assert_not_called()

    def test_handle_module_state_changed_with_lightbulb(self):
        """Test handle_module_state_changed dispatches ReadDatapointEvent for lightbulb."""
        from xp.services.homekit.homekit_lightbulb import LightBulb

        # Create mock lightbulb accessory
        mock_module = ConsonModuleConfig(
            name="Test Module",
            serial_number="1234567890",
            module_type="XP24",
            module_type_code=24,
            link_number=1,
        )
        mock_lightbulb = Mock(spec=LightBulb)
        mock_lightbulb.module = mock_module
        mock_lightbulb.identifier = "1234567890.00"

        # Add to module_registry
        module_key = (24, 1)
        self.hap_service.module_registry[module_key] = [mock_lightbulb]

        # Create state changed event
        event = ModuleStateChangedEvent(
            module_type_code=24, link_number=1, input_number=0, telegram_event_type="M"
        )

        # Handle event
        self.hap_service.handle_module_state_changed(event)

        # Should dispatch ReadDatapointEvent with refresh_cache=True
        self.event_bus.dispatch.assert_called_once()
        dispatched_event = self.event_bus.dispatch.call_args[0][0]
        assert isinstance(dispatched_event, ReadDatapointEvent)
        assert dispatched_event.serial_number == "1234567890"
        assert dispatched_event.datapoint_type == DataPointType.MODULE_OUTPUT_STATE
        assert dispatched_event.refresh_cache is True

    def test_handle_module_state_changed_with_dimminglight(self):
        """Test handle_module_state_changed dispatches both OUTPUT_STATE and LIGHT_LEVEL for dimming light."""
        from xp.services.homekit.homekit_dimminglight import DimmingLight

        # Create mock dimming light accessory
        mock_module = ConsonModuleConfig(
            name="Test Module",
            serial_number="9876543210",
            module_type="XP24",
            module_type_code=24,
            link_number=2,
        )
        mock_dimming = Mock(spec=DimmingLight)
        mock_dimming.module = mock_module
        mock_dimming.identifier = "9876543210.00"

        # Add to module_registry
        module_key = (24, 2)
        self.hap_service.module_registry[module_key] = [mock_dimming]

        # Create state changed event
        event = ModuleStateChangedEvent(
            module_type_code=24, link_number=2, input_number=5, telegram_event_type="M"
        )

        # Handle event
        self.hap_service.handle_module_state_changed(event)

        # Should dispatch TWO ReadDatapointEvents: MODULE_OUTPUT_STATE and MODULE_LIGHT_LEVEL
        assert self.event_bus.dispatch.call_count == 2

        # First call: MODULE_OUTPUT_STATE
        first_call = self.event_bus.dispatch.call_args_list[0][0][0]
        assert isinstance(first_call, ReadDatapointEvent)
        assert first_call.serial_number == "9876543210"
        assert first_call.datapoint_type == DataPointType.MODULE_OUTPUT_STATE
        assert first_call.refresh_cache is True

        # Second call: MODULE_LIGHT_LEVEL
        second_call = self.event_bus.dispatch.call_args_list[1][0][0]
        assert isinstance(second_call, ReadDatapointEvent)
        assert second_call.serial_number == "9876543210"
        assert second_call.datapoint_type == DataPointType.MODULE_LIGHT_LEVEL
        assert second_call.refresh_cache is True

    def test_handle_module_state_changed_with_multiple_accessories(self):
        """Test handle_module_state_changed with multiple accessories on same module."""
        from xp.services.homekit.homekit_lightbulb import LightBulb
        from xp.services.homekit.homekit_outlet import Outlet

        # Create mock module
        mock_module = ConsonModuleConfig(
            name="Test Module",
            serial_number="1111111111",
            module_type="XP24",
            module_type_code=24,
            link_number=3,
        )

        # Create multiple accessories on same module
        mock_lightbulb = Mock(spec=LightBulb)
        mock_lightbulb.module = mock_module
        mock_lightbulb.identifier = "1111111111.00"

        mock_outlet = Mock(spec=Outlet)
        mock_outlet.module = mock_module
        mock_outlet.identifier = "1111111111.01"

        # Add both to module_registry
        module_key = (24, 3)
        self.hap_service.module_registry[module_key] = [mock_lightbulb, mock_outlet]

        # Create state changed event
        event = ModuleStateChangedEvent(
            module_type_code=24, link_number=3, input_number=2, telegram_event_type="M"
        )

        # Handle event
        self.hap_service.handle_module_state_changed(event)

        # Should dispatch ReadDatapointEvent for EACH accessory
        assert self.event_bus.dispatch.call_count == 2

        # Both should be MODULE_OUTPUT_STATE requests with refresh_cache=True
        for call in self.event_bus.dispatch.call_args_list:
            dispatched_event = call[0][0]
            assert isinstance(dispatched_event, ReadDatapointEvent)
            assert dispatched_event.serial_number == "1111111111"
            assert dispatched_event.datapoint_type == DataPointType.MODULE_OUTPUT_STATE
            assert dispatched_event.refresh_cache is True

    def test_module_registry_key_format(self):
        """Test that module_registry uses (module_type_code, link_number) tuple as key."""
        from xp.services.homekit.homekit_lightbulb import LightBulb

        # Create mock accessory
        mock_module = ConsonModuleConfig(
            name="Test Module",
            serial_number="5555555555",
            module_type="XP33",
            module_type_code=33,
            link_number=7,
        )
        mock_lightbulb = Mock(spec=LightBulb)
        mock_lightbulb.module = mock_module

        # Add to registry
        module_key = (33, 7)
        self.hap_service.module_registry[module_key] = [mock_lightbulb]

        # Verify key format
        assert (33, 7) in self.hap_service.module_registry
        assert self.hap_service.module_registry[(33, 7)] == [mock_lightbulb]
