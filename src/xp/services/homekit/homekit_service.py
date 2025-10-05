# Install asyncio reactor before importing reactor

import asyncio
import logging
import threading

from bubus import EventBus
from twisted.internet.posixbase import PosixReactorBase

from xp.models.protocol.conbus_protocol import (
    ConnectionFailedEvent,
    ConnectionLostEvent,
    ConnectionMadeEvent,
    DatapointReceivedEvent,
    ModuleDiscoveredEvent,
    TelegramReceivedEvent,
)
from xp.services import TelegramService
from xp.services.homekit.homekit_conbus_service import HomeKitConbusService
from xp.services.homekit.homekit_dimminglight_service import HomeKitDimmingLightService
from xp.services.homekit.homekit_hap_service import HomekitHapService
from xp.services.homekit.homekit_lightbulb_service import HomeKitLightbulbService
from xp.services.homekit.homekit_outlet_service import HomeKitOutletService
from xp.services.protocol.protocol_factory import TelegramFactory


class HomeKitService:

    def __init__(
        self,
        event_bus: EventBus,
        telegram_factory: TelegramFactory,
        reactor: PosixReactorBase,
        lightbulb_service: HomeKitLightbulbService,
        outlet_service: HomeKitOutletService,
        dimminglight_service: HomeKitDimmingLightService,
        conbus_service: HomeKitConbusService,
        module_factory: HomekitHapService,
        telegram_service: TelegramService,
    ):

        self.reactor = reactor
        self.telegram_factory = telegram_factory
        self.protocol = telegram_factory.telegram_protocol
        self.event_bus = event_bus
        self.lightbulb_service = lightbulb_service
        self.dimminglight_service = dimminglight_service
        self.outlet_service = outlet_service
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
        self.logger.info("Starting HomeKit service...")
        self.logger.debug("start")

        # Run reactor in its own dedicated thread
        self.logger.info("Starting reactor in dedicated thread...")
        reactor_thread = threading.Thread(
            target=self._run_reactor_in_thread, daemon=True, name="ReactorThread"
        )
        reactor_thread.start()

        # Keep MainThread alive while reactor thread runs
        self.logger.info("Reactor thread started, MainThread waiting...")
        reactor_thread.join()

    def _run_reactor_in_thread(self) -> None:
        """Run reactor in dedicated thread with its own event loop"""
        self.logger.info("Reactor thread starting...")

        # The asyncio reactor already has an event loop set up
        # We just need to use it

        # Connect to TCP server
        self.logger.info("Connecting to TCP server 10.0.3.26:10001")
        self.reactor.connectTCP("10.0.3.26", 10001, self.telegram_factory)

        # Schedule module factory to start after reactor is running
        # Use callLater(0) to ensure event loop is actually running
        self.reactor.callLater(0, self._start_module_factory)

        # Run the reactor (which now uses asyncio underneath)
        self.logger.info("Starting reactor event loop...")
        self.reactor.run()

    def _start_module_factory(self) -> None:
        """Start module factory after reactor starts"""
        self.logger.info("Starting module factory...")
        self.logger.debug("callWhenRunning executed, scheduling async task")

        # Run HAP-python driver asynchronously in the reactor's event loop
        async def async_start() -> None:
            self.logger.info("async_start executing...")
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
        """Handle connection established - send initial telegram"""
        self.logger.debug("Connection established successfully")
        self.logger.debug("Sending initial discovery telegram: S0000000000F01D00")
        event.protocol.sendFrame(b"S0000000000F01D00")

    def handle_connection_failed(self, event: ConnectionFailedEvent) -> None:
        """Handle connection failed"""
        self.logger.error(f"Connection failed: {event.reason}")

    def handle_connection_lost(self, event: ConnectionLostEvent) -> None:
        """Handle connection lost"""
        self.logger.warning(
            f"Connection lost: {event.reason if hasattr(event, 'reason') else 'Unknown reason'}"
        )

    def handle_telegram_received(self, event: TelegramReceivedEvent) -> str:
        """Handle received telegram events"""
        self.logger.debug(
            f"handle_telegram_received ENTERED with telegram: {event.telegram}"
        )

        # Check if telegram is Reply (R) with Discover function (F01D)
        if event.telegram.startswith("R") and "F01D" in event.telegram:
            self.logger.debug("Module discovered, dispatching ModuleDiscoveredEvent")
            self.event_bus.dispatch(
                ModuleDiscoveredEvent(
                    frame=event.frame,
                    telegram=event.telegram,
                    payload=event.payload,
                    serial_number=event.serial_number,
                    checksum=event.checksum,
                    protocol=event.protocol,
                )
            )
            self.logger.debug("ModuleDiscoveredEvent dispatched successfully")
            return event.frame

        # Check if telegram is Reply (R) with Read Datapoint (F02D)
        if event.telegram.startswith("R") and "F02D" in event.telegram:
            self.logger.debug("Module Read Datapoint, parsing telegram...")
            reply_telegram = self.telegram_service.parse_reply_telegram(event.frame)
            self.logger.debug(
                f"Parsed telegram: serial={reply_telegram.serial_number}, type={reply_telegram.datapoint_type}, value={reply_telegram.data_value}"
            )
            self.logger.debug("About to dispatch DatapointReceivedEvent")
            self.event_bus.dispatch(
                DatapointReceivedEvent(
                    serial_number=reply_telegram.serial_number,
                    datapoint_type=reply_telegram.datapoint_type,
                    data_value=reply_telegram.data_value,
                )
            )
            self.logger.debug("DatapointReceivedEvent dispatched successfully")
            return event.frame

        self.logger.warning(f"Unhandled telegram received: {event.telegram}")
        self.logger.info(f"telegram_received unhandled event {event}")
        return event.frame

    def handle_module_discovered(self, event: ModuleDiscoveredEvent) -> str:
        self.logger.debug("Handling module discovered event")

        # Replace R with S and F01D with F02D00
        new_telegram = event.telegram.replace("R", "S", 1).replace(
            "F01D", "F02D00", 1
        )  # module type

        self.logger.debug(f"Sending module type request: {new_telegram}")
        event.protocol.sendFrame(new_telegram.encode())
        return event.serial_number
