"""Integration tests for event-driven cache refresh flow"""

import asyncio
from unittest.mock import MagicMock, Mock, patch

import pytest
import pytest_asyncio
from bubus import EventBus

from xp.models.homekit.homekit_conson_config import ConsonModuleConfig
from xp.models.protocol.conbus_protocol import (
    EventTelegramReceivedEvent,
    LightLevelReceivedEvent,
    ModuleStateChangedEvent,
    OutputStateReceivedEvent,
    ReadDatapointEvent,
    ReadDatapointFromProtocolEvent,
)
from xp.models.telegram.datapoint_type import DataPointType
from xp.models.telegram.event_telegram import EventTelegram, EventType
from xp.services import TelegramService
from xp.services.homekit.homekit_cache_service import HomeKitCacheService
from xp.services.homekit.homekit_dimminglight import DimmingLight
from xp.services.homekit.homekit_hap_service import HomekitHapService
from xp.services.homekit.homekit_lightbulb import LightBulb
from xp.services.homekit.homekit_outlet import Outlet
from xp.services.protocol.telegram_protocol import TelegramProtocol


class TestEndToEndCacheRefresh:
    """Integration tests for end-to-end event-driven cache refresh"""

    @pytest_asyncio.fixture(autouse=True)
    async def setup_method(self):
        """Setup test fixtures with real services"""
        # Create real EventBus
        self.event_bus = EventBus()

        # Create real cache service
        self.cache_service = HomeKitCacheService(self.event_bus)

        # Create mock HAP service components
        self.homekit_config = MagicMock()
        self.homekit_config.homekit.port = 51826
        self.homekit_config.bridge.name = "Test Bridge"
        self.homekit_config.bridge.rooms = []
        self.homekit_config.accessories = []

        from xp.services.homekit.homekit_module_service import HomekitModuleService

        self.module_service = Mock(spec=HomekitModuleService)

        # Create HAP service with patched AccessoryDriver
        with patch("xp.services.homekit.homekit_hap_service.AccessoryDriver"):
            self.hap_service = HomekitHapService(
                self.homekit_config, self.module_service, self.event_bus
            )

        # Track dispatched events for verification
        self.dispatched_events = []

        # Wrap dispatch to capture events
        original_dispatch = self.event_bus.dispatch

        def capture_dispatch(event):
            self.dispatched_events.append(event)
            return original_dispatch(event)

        self.event_bus.dispatch = capture_dispatch

    @pytest.mark.asyncio
    async def test_end_to_end_cache_refresh_flow(self):
        """Test complete flow from event telegram to cache refresh and state update"""
        # Setup: Create module and accessory
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
        mock_lightbulb.is_on = False  # Initially OFF

        # Add to HAP service registries
        self.hap_service.accessory_registry["1234567890.00"] = mock_lightbulb
        self.hap_service.module_registry[(24, 1)] = [mock_lightbulb]

        # Pre-populate cache with old state (OFF)
        old_state_event = OutputStateReceivedEvent(
            serial_number="1234567890",
            datapoint_type=DataPointType.MODULE_OUTPUT_STATE,
            data_value="0x",  # All outputs OFF
        )
        self.cache_service.handle_output_state_received_event(old_state_event)

        # Verify cache is populated
        cache_key = ("1234567890", DataPointType.MODULE_OUTPUT_STATE)
        assert cache_key in self.cache_service.cache
        assert self.cache_service.cache[cache_key]["event"] == old_state_event

        # Clear dispatched events from cache population
        self.dispatched_events.clear()

        # Action: Dispatch ModuleStateChangedEvent (simulating button press)
        state_changed_event = ModuleStateChangedEvent(
            module_type_code=24, link_number=1, input_number=0, telegram_event_type="M"
        )
        await self.event_bus.dispatch(state_changed_event)

        # Verify: ReadDatapointEvent with refresh_cache=True was dispatched
        read_events = [e for e in self.dispatched_events if isinstance(e, ReadDatapointEvent)]
        assert len(read_events) == 1
        assert read_events[0].serial_number == "1234567890"
        assert read_events[0].datapoint_type == DataPointType.MODULE_OUTPUT_STATE
        assert read_events[0].refresh_cache is True

        # Verify: Cache was invalidated
        assert cache_key not in self.cache_service.cache

        # Verify: ReadDatapointFromProtocolEvent was dispatched (cache miss)
        protocol_events = [
            e for e in self.dispatched_events if isinstance(e, ReadDatapointFromProtocolEvent)
        ]
        assert len(protocol_events) == 1
        assert protocol_events[0].serial_number == "1234567890"
        assert protocol_events[0].datapoint_type == DataPointType.MODULE_OUTPUT_STATE

        # Simulate: Fresh state received from protocol (now ON)
        fresh_state_event = OutputStateReceivedEvent(
            serial_number="1234567890",
            datapoint_type=DataPointType.MODULE_OUTPUT_STATE,
            data_value="1x",  # Output 0 is ON
        )
        await self.event_bus.dispatch(fresh_state_event)

        # Verify: Cache was updated with fresh state
        assert cache_key in self.cache_service.cache
        assert self.cache_service.cache[cache_key]["event"] == fresh_state_event
        assert self.cache_service.cache[cache_key]["event"].data_value == "1x"

    @pytest.mark.asyncio
    async def test_multi_accessory_scenario(self):
        """Test that only accessories for the affected module get refresh requests"""
        # Setup: Create multiple modules with accessories
        module_a = ConsonModuleConfig(
            name="Module A",
            serial_number="1111111111",
            module_type="XP24",
            module_type_code=24,
            link_number=1,
        )

        module_b = ConsonModuleConfig(
            name="Module B",
            serial_number="2222222222",
            module_type="XP24",
            module_type_code=24,
            link_number=2,
        )

        # Create accessories for both modules
        lightbulb_a = Mock(spec=LightBulb)
        lightbulb_a.module = module_a
        lightbulb_a.identifier = "1111111111.00"

        outlet_a = Mock(spec=Outlet)
        outlet_a.module = module_a
        outlet_a.identifier = "1111111111.01"

        lightbulb_b = Mock(spec=LightBulb)
        lightbulb_b.module = module_b
        lightbulb_b.identifier = "2222222222.00"

        # Add to HAP service registries
        self.hap_service.accessory_registry["1111111111.00"] = lightbulb_a
        self.hap_service.accessory_registry["1111111111.01"] = outlet_a
        self.hap_service.accessory_registry["2222222222.00"] = lightbulb_b

        self.hap_service.module_registry[(24, 1)] = [lightbulb_a, outlet_a]
        self.hap_service.module_registry[(24, 2)] = [lightbulb_b]

        # Clear dispatched events
        self.dispatched_events.clear()

        # Action: Dispatch ModuleStateChangedEvent for module A only
        state_changed_event = ModuleStateChangedEvent(
            module_type_code=24, link_number=1, input_number=2, telegram_event_type="M"
        )
        await self.event_bus.dispatch(state_changed_event)

        # Verify: Only module A accessories got refresh requests
        read_events = [e for e in self.dispatched_events if isinstance(e, ReadDatapointEvent)]

        # Should have 2 requests (one for each accessory on module A)
        assert len(read_events) == 2

        # Both should be for module A's serial number
        for event in read_events:
            assert event.serial_number == "1111111111"
            assert event.refresh_cache is True

        # Verify: No requests for module B
        assert not any(e.serial_number == "2222222222" for e in read_events)

    @pytest.mark.asyncio
    async def test_dimming_light_refreshes_both_datapoints(self):
        """Test that DimmingLight accessories refresh both OUTPUT_STATE and LIGHT_LEVEL"""
        # Setup: Create module with dimming light
        mock_module = ConsonModuleConfig(
            name="Dimmer Module",
            serial_number="5555555555",
            module_type="XP24",
            module_type_code=24,
            link_number=5,
        )

        mock_dimmer = Mock(spec=DimmingLight)
        mock_dimmer.module = mock_module
        mock_dimmer.identifier = "5555555555.00"
        mock_dimmer.brightness = 50

        # Add to HAP service registries
        self.hap_service.accessory_registry["5555555555.00"] = mock_dimmer
        self.hap_service.module_registry[(24, 5)] = [mock_dimmer]

        # Clear dispatched events
        self.dispatched_events.clear()

        # Action: Dispatch ModuleStateChangedEvent
        state_changed_event = ModuleStateChangedEvent(
            module_type_code=24, link_number=5, input_number=0, telegram_event_type="M"
        )
        await self.event_bus.dispatch(state_changed_event)

        # Verify: Two ReadDatapointEvents dispatched
        read_events = [e for e in self.dispatched_events if isinstance(e, ReadDatapointEvent)]
        assert len(read_events) == 2

        # Verify: One for OUTPUT_STATE, one for LIGHT_LEVEL
        datapoint_types = {e.datapoint_type for e in read_events}
        assert DataPointType.MODULE_OUTPUT_STATE in datapoint_types
        assert DataPointType.MODULE_LIGHT_LEVEL in datapoint_types

        # Both should have refresh_cache=True
        assert all(e.refresh_cache is True for e in read_events)
        assert all(e.serial_number == "5555555555" for e in read_events)

    @pytest.mark.asyncio
    async def test_cache_isolation_between_modules(self):
        """Test that cache refresh for one module doesn't affect other modules"""
        # Setup: Create two modules with cached states
        module_1 = ConsonModuleConfig(
            name="Module 1",
            serial_number="1111111111",
            module_type="XP24",
            module_type_code=24,
            link_number=1,
        )

        module_2 = ConsonModuleConfig(
            name="Module 2",
            serial_number="2222222222",
            module_type="XP24",
            module_type_code=24,
            link_number=2,
        )

        lightbulb_1 = Mock(spec=LightBulb)
        lightbulb_1.module = module_1
        lightbulb_1.identifier = "1111111111.00"

        lightbulb_2 = Mock(spec=LightBulb)
        lightbulb_2.module = module_2
        lightbulb_2.identifier = "2222222222.00"

        # Add to HAP service registries
        self.hap_service.accessory_registry["1111111111.00"] = lightbulb_1
        self.hap_service.accessory_registry["2222222222.00"] = lightbulb_2
        self.hap_service.module_registry[(24, 1)] = [lightbulb_1]
        self.hap_service.module_registry[(24, 2)] = [lightbulb_2]

        # Pre-populate cache for both modules
        state_1 = OutputStateReceivedEvent(
            serial_number="1111111111",
            datapoint_type=DataPointType.MODULE_OUTPUT_STATE,
            data_value="0x",
        )
        state_2 = OutputStateReceivedEvent(
            serial_number="2222222222",
            datapoint_type=DataPointType.MODULE_OUTPUT_STATE,
            data_value="1x",
        )
        self.cache_service.handle_output_state_received_event(state_1)
        self.cache_service.handle_output_state_received_event(state_2)

        # Verify both are cached
        cache_key_1 = ("1111111111", DataPointType.MODULE_OUTPUT_STATE)
        cache_key_2 = ("2222222222", DataPointType.MODULE_OUTPUT_STATE)
        assert cache_key_1 in self.cache_service.cache
        assert cache_key_2 in self.cache_service.cache

        # Clear dispatched events
        self.dispatched_events.clear()

        # Action: Trigger refresh for module 1 only
        state_changed_event = ModuleStateChangedEvent(
            module_type_code=24, link_number=1, input_number=0, telegram_event_type="M"
        )
        await self.event_bus.dispatch(state_changed_event)

        # Verify: Module 1's cache was invalidated
        assert cache_key_1 not in self.cache_service.cache

        # Verify: Module 2's cache was NOT affected
        assert cache_key_2 in self.cache_service.cache
        assert self.cache_service.cache[cache_key_2]["event"] == state_2

    @pytest.mark.asyncio
    async def test_no_refresh_when_no_accessories_registered(self):
        """Test that no refresh occurs when module has no registered accessories"""
        # Clear dispatched events
        self.dispatched_events.clear()

        # Action: Dispatch ModuleStateChangedEvent for unregistered module
        state_changed_event = ModuleStateChangedEvent(
            module_type_code=99, link_number=99, input_number=0, telegram_event_type="M"
        )
        await self.event_bus.dispatch(state_changed_event)

        # Verify: No ReadDatapointEvent dispatched
        read_events = [e for e in self.dispatched_events if isinstance(e, ReadDatapointEvent)]
        assert len(read_events) == 0

        # Verify: No protocol requests
        protocol_events = [
            e for e in self.dispatched_events if isinstance(e, ReadDatapointFromProtocolEvent)
        ]
        assert len(protocol_events) == 0


class TestEventTelegramToCacheRefreshFlow:
    """Integration tests for complete flow from event telegram parsing to cache refresh"""

    @pytest_asyncio.fixture(autouse=True)
    async def setup_method(self):
        """Setup test fixtures"""
        self.event_bus = EventBus()
        self.cache_service = HomeKitCacheService(self.event_bus)
        self.telegram_service = TelegramService()

        # Create mock HAP service
        self.homekit_config = MagicMock()
        self.homekit_config.homekit.port = 51826
        self.homekit_config.bridge.name = "Test Bridge"
        self.homekit_config.bridge.rooms = []
        self.homekit_config.accessories = []

        from xp.services.homekit.homekit_module_service import HomekitModuleService

        self.module_service = Mock(spec=HomekitModuleService)

        with patch("xp.services.homekit.homekit_hap_service.AccessoryDriver"):
            self.hap_service = HomekitHapService(
                self.homekit_config, self.module_service, self.event_bus
            )

        # Track dispatched events
        self.dispatched_events = []
        original_dispatch = self.event_bus.dispatch

        def capture_dispatch(event):
            self.dispatched_events.append(event)
            return original_dispatch(event)

        self.event_bus.dispatch = capture_dispatch

    @pytest.mark.asyncio
    async def test_parse_event_telegram_and_trigger_cache_refresh(self):
        """Test parsing event telegram and triggering cache refresh"""
        # Setup: Create module and accessory
        mock_module = ConsonModuleConfig(
            name="Test Module",
            serial_number="1234567890",
            module_type="XP24",
            module_type_code=14,  # Module type from telegram
            link_number=1,
        )

        mock_lightbulb = Mock(spec=LightBulb)
        mock_lightbulb.module = mock_module
        mock_lightbulb.identifier = "1234567890.00"

        # Add to registries
        self.hap_service.accessory_registry["1234567890.00"] = mock_lightbulb
        self.hap_service.module_registry[(14, 1)] = [mock_lightbulb]

        # Clear dispatched events
        self.dispatched_events.clear()

        # Action: Parse event telegram
        event_telegram_frame = "<E14L01I02MAK>"
        parsed = self.telegram_service.parse_event_telegram(event_telegram_frame)

        # Verify parsing worked
        assert parsed.module_type == 14
        assert parsed.link_number == 1
        assert parsed.input_number == 2
        assert parsed.event_type == EventType.BUTTON_PRESS

        # Dispatch ModuleStateChangedEvent based on parsed data
        state_changed = ModuleStateChangedEvent(
            module_type_code=parsed.module_type,
            link_number=parsed.link_number,
            input_number=parsed.input_number,
            telegram_event_type=parsed.event_type.value,
        )
        await self.event_bus.dispatch(state_changed)

        # Verify: ReadDatapointEvent with refresh_cache=True was dispatched
        read_events = [e for e in self.dispatched_events if isinstance(e, ReadDatapointEvent)]
        assert len(read_events) == 1
        assert read_events[0].serial_number == "1234567890"
        assert read_events[0].refresh_cache is True
