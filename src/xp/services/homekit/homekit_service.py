"""HomeKit Service for Apple HomeKit integration.

This module provides the main service for HomeKit integration.
"""

# Install asyncio reactor before importing reactor

import asyncio
import logging
import threading

from bubus import EventBus
from twisted.internet.posixbase import PosixReactorBase

from xp.models import ConbusClientConfig
from xp.models.protocol.conbus_protocol import (
    ConnectionFailedEvent,
    ConnectionLostEvent,
    ConnectionMadeEvent,
    LightLevelReceivedEvent,
    ModuleDiscoveredEvent,
    ModuleStateChangedEvent,
    OutputStateReceivedEvent,
    TelegramReceivedEvent,
)
from xp.services import TelegramService
from xp.services.homekit.homekit_cache_service import HomeKitCacheService
from xp.services.homekit.homekit_conbus_service import HomeKitConbusService
from xp.services.homekit.homekit_dimminglight_service import HomeKitDimmingLightService
from xp.services.homekit.homekit_hap_service import HomekitHapService
from xp.services.homekit.homekit_lightbulb_service import HomeKitLightbulbService
from xp.services.homekit.homekit_outlet_service import HomeKitOutletService
from xp.services.protocol.protocol_factory import TelegramFactory


class HomeKitService:
    """Main HomeKit service for Apple HomeKit integration.

    Attributes:
        cli_config: Conbus client configuration.
        reactor: Twisted reactor instance.
        telegram_factory: Telegram factory for protocol.
        protocol: Telegram protocol instance.
        event_bus: Event bus for inter-service communication.
        lightbulb_service: Lightbulb service instance.
        dimminglight_service: Dimming light service instance.
        outlet_service: Outlet service instance.
        cache_service: Cache service instance.
        conbus_service: Conbus service instance.
        module_factory: HAP service instance.
        telegram_service: Telegram service instance.
        logger: Logger instance.
    """

    def __init__(
        self,
        cli_config: ConbusClientConfig,
        event_bus: EventBus,
        telegram_factory: TelegramFactory,
        reactor: PosixReactorBase,
        lightbulb_service: HomeKitLightbulbService,
        outlet_service: HomeKitOutletService,
        dimminglight_service: HomeKitDimmingLightService,
        cache_service: HomeKitCacheService,
        conbus_service: HomeKitConbusService,
        module_factory: HomekitHapService,
        telegram_service: TelegramService,
    ):
        """Initialize the HomeKit service.

        Args:
            cli_config: Conbus client configuration.
            event_bus: Event bus instance.
            telegram_factory: Telegram factory instance.
            reactor: Twisted reactor instance.
            lightbulb_service: Lightbulb service instance.
            outlet_service: Outlet service instance.
            dimminglight_service: Dimming light service instance.
            cache_service: Cache service instance.
            conbus_service: Conbus service instance.
            module_factory: HAP service instance.
            telegram_service: Telegram service instance.
        """
        self.cli_config = cli_config.conbus
        self.reactor = reactor
        self.telegram_factory = telegram_factory
        self.protocol = telegram_factory.telegram_protocol
        self.event_bus = event_bus
        self.lightbulb_service = lightbulb_service
        self.dimminglight_service = dimminglight_service
        self.outlet_service = outlet_service
        self.cache_service = cache_service
        self.conbus_service = conbus_service
        self.module_factory = module_factory
        self.telegram_service = telegram_service
        self.logger = logging.getLogger(__name__)

        # Register event handlers
        self.event_bus.on(ConnectionMadeEvent, self.handle_connection_made)
        self.event_bus.on(ConnectionFailedEvent, self.handle_connection_failed)
        self.event_bus.on(ConnectionLostEvent, self.handle_connection_lost)
        self.event_bus.on(TelegramReceivedEvent, self.handle_telegram_received)
        self.event_bus.on(ModuleDiscoveredEvent, self.handle_module_discovered)

    def start(self) -> None:
        """Start the HomeKit service."""
        self.logger.info("Starting HomeKit service.")
        self.logger.debug("start")

        # Run reactor in its own dedicated thread
        self.logger.info("Starting reactor in dedicated thread.")
        reactor_thread = threading.Thread(
            target=self._run_reactor_in_thread, daemon=True, name="ReactorThread"
        )
        reactor_thread.start()

        # Keep MainThread alive while reactor thread runs
        self.logger.info("Reactor thread started, MainThread waiting.")
        reactor_thread.join()

    def _run_reactor_in_thread(self) -> None:
        """Run reactor in dedicated thread with its own event loop."""
        self.logger.info("Reactor thread starting.")

        # The asyncio reactor already has an event loop set up
        # We just need to use it

        # Connect to TCP server
        self.logger.info(
            f"Connecting to TCP server {self.cli_config.ip}:{self.cli_config.port}"
        )
        self.reactor.connectTCP(
            self.cli_config.ip, self.cli_config.port, self.telegram_factory
        )

        # Schedule module factory to start after reactor is running
        # Use callLater(0) to ensure event loop is actually running
        self.reactor.callLater(0, self._start_module_factory)

        # Run the reactor (which now uses asyncio underneath)
        self.logger.info("Starting reactor event loop.")
        self.reactor.run()

    def _start_module_factory(self) -> None:
        """Start module factory after reactor starts.

        Creates and schedules an async task to start the HAP service.
        """
        self.logger.info("Starting module factory.")
        self.logger.debug("callWhenRunning executed, scheduling async task")

        # Run HAP-python driver asynchronously in the reactor's event loop
        async def async_start() -> None:
            """Start the HAP service asynchronously."""
            self.logger.info("async_start executing.")
            try:
                await self.module_factory.async_start()
                self.logger.info("Module factory started successfully")
            except Exception as e:
                self.logger.error(f"Error starting module factory: {e}", exc_info=True)

        # Schedule on reactor's event loop (which is asyncio)
        try:
            task = asyncio.create_task(async_start())
            self.logger.debug(f"Created module factory task: {task}")
            task.add_done_callback(
                lambda t: self.logger.debug(f"Module factory task completed: {t}")
            )
        except Exception as e:
            self.logger.error(f"Error creating async task: {e}", exc_info=True)

    # Event handlers
    def handle_connection_made(self, event: ConnectionMadeEvent) -> None:
        """Handle connection established - send initial telegram.

        Args:
            event: Connection made event.
        """
        self.logger.debug("Connection established successfully")
        self.logger.debug("Sending initial discovery telegram: S0000000000F01D00")
        event.protocol.sendFrame(b"S0000000000F01D00")

    def handle_connection_failed(self, event: ConnectionFailedEvent) -> None:
        """Handle connection failed.

        Args:
            event: Connection failed event.
        """
        self.logger.error(f"Connection failed: {event.reason}")

    def handle_connection_lost(self, event: ConnectionLostEvent) -> None:
        """Handle connection lost.

        Args:
            event: Connection lost event.
        """
        self.logger.warning(
            f"Connection lost: {event.reason if hasattr(event, 'reason') else 'Unknown reason'}"
        )

    def handle_telegram_received(self, event: TelegramReceivedEvent) -> str:
        """Handle received telegram events.

        Args:
            event: Telegram received event.

        Returns:
            Frame data from the event.
        """
        self.logger.debug(
            f"handle_telegram_received ENTERED with telegram: {event.telegram}"
        )

        # Check if telegram is Reply (R) with Discover function (F01D)
        if event.telegram_type in ("E"):
            self.dispatch_event_telegram_received_event(event)
            return event.frame

        # Check if telegram is Reply (R) with Discover function (F01D)
        if event.telegram_type in ("R") and "F01D" in event.telegram:
            self.dispatch_module_discovered_event(event)
            return event.frame

        # Check if telegram is Reply (R) with Read Datapoint (F02) OUTPUT_STATE (D12)
        if event.telegram_type in ("R") and "F02D12" in event.telegram:
            self.dispatch_output_state_event(event)
            return event.frame

        # Check if telegram is Reply (R) with Read Datapoint (F02) LIGHT_LEVEL (D15)
        if event.telegram_type in ("R") and "F02D15" in event.telegram:
            self.dispatch_light_level_event(event)
            return event.frame

        self.logger.warning(f"Unhandled telegram received: {event.telegram}")
        self.logger.info(f"telegram_received unhandled event {event}")
        return event.frame

    def dispatch_light_level_event(self, event: TelegramReceivedEvent) -> None:
        """Dispatch light level received event.

        Args:
            event: Telegram received event.
        """
        self.logger.debug("Light level Datapoint, parsing telegram.")
        reply_telegram = self.telegram_service.parse_reply_telegram(event.frame)
        self.logger.debug(
            f"Parsed telegram: "
            f"serial={reply_telegram.serial_number}, "
            f"type={reply_telegram.datapoint_type}, "
            f"value={reply_telegram.data_value}"
        )
        self.logger.debug("About to dispatch LightLevelReceivedEvent")
        self.event_bus.dispatch(
            LightLevelReceivedEvent(
                serial_number=reply_telegram.serial_number,
                datapoint_type=reply_telegram.datapoint_type,
                data_value=reply_telegram.data_value,
            )
        )
        self.logger.debug("LightLevelReceivedEvent dispatched successfully")

    def dispatch_output_state_event(self, event: TelegramReceivedEvent) -> None:
        """Dispatch output state received event.

        Args:
            event: Telegram received event.
        """
        self.logger.debug("Module Read Datapoint, parsing telegram.")
        reply_telegram = self.telegram_service.parse_reply_telegram(event.frame)
        self.logger.debug(
            f"Parsed telegram: "
            f"serial={reply_telegram.serial_number}, "
            f"type={reply_telegram.datapoint_type}, "
            f"value={reply_telegram.data_value}"
        )
        self.logger.debug("About to dispatch OutputStateReceivedEvent")
        self.event_bus.dispatch(
            OutputStateReceivedEvent(
                serial_number=reply_telegram.serial_number,
                datapoint_type=reply_telegram.datapoint_type,
                data_value=reply_telegram.data_value,
            )
        )
        self.logger.debug("OutputStateReceivedEvent dispatched successfully")

    def dispatch_event_telegram_received_event(
        self, event: TelegramReceivedEvent
    ) -> None:
        """Dispatch event telegram received event.

        Args:
            event: Telegram received event.
        """
        self.logger.debug("Event telegram received, parsing.")

        # Parse event telegram to extract module information
        event_telegram = self.telegram_service.parse_event_telegram(event.frame)

        self.logger.debug(
            f"Parsed event: "
            f"module_type={event_telegram.module_type}, "
            f"link={event_telegram.link_number}, "
            f"input={event_telegram.input_number}"
        )

        # Dispatch ModuleStateChangedEvent for cache refresh
        self.event_bus.dispatch(
            ModuleStateChangedEvent(
                module_type_code=event_telegram.module_type,
                link_number=event_telegram.link_number,
                input_number=event_telegram.input_number,
                telegram_event_type=(
                    event_telegram.event_type.value
                    if event_telegram.event_type
                    else "M"
                ),
            )
        )
        self.logger.debug("ModuleStateChangedEvent dispatched successfully")

    def dispatch_module_discovered_event(self, event: TelegramReceivedEvent) -> None:
        """Dispatch module discovered event.

        Args:
            event: Telegram received event.
        """
        self.logger.debug("Module discovered, dispatching ModuleDiscoveredEvent")
        self.event_bus.dispatch(
            ModuleDiscoveredEvent(
                frame=event.frame,
                telegram=event.telegram,
                payload=event.payload,
                telegram_type=event.telegram_type,
                serial_number=event.serial_number,
                checksum=event.checksum,
                protocol=event.protocol,
            )
        )
        self.logger.debug("ModuleDiscoveredEvent dispatched successfully")

    def handle_module_discovered(self, event: ModuleDiscoveredEvent) -> str:
        """Handle module discovered event.

        Args:
            event: Module discovered event.

        Returns:
            Serial number of the discovered module.
        """
        self.logger.debug("Handling module discovered event")

        # Replace R with S and F01D with F02D00
        new_telegram = event.telegram.replace("R", "S", 1).replace(
            "F01D", "F02D00", 1
        )  # module type

        self.logger.debug(f"Sending module type request: {new_telegram}")
        event.protocol.sendFrame(new_telegram.encode())
        return event.serial_number
