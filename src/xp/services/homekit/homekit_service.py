# Install asyncio reactor before importing reactor
from typing import Any

from bubus import EventBus
from twisted.internet.posixbase import PosixReactorBase

from xp.models.protocol.conbus_protocol import (
    ConnectionFailedEvent,
    ConnectionLostEvent,
    ConnectionMadeEvent,
    ModuleDiscoveredEvent,
    ModuleErrorCodeReadEvent,
    ModuleTypeReadEvent,
    TelegramReceivedEvent,
)
from xp.services.protocol.protocol_factory import TelegramFactory

class HomeKitService:

    def __init__(
            self,
            event_bus: EventBus,
            telegram_factory: TelegramFactory,
            reactor: PosixReactorBase
    ):

        self.reactor = reactor
        self.telegram_factory = telegram_factory
        self.event_bus = event_bus

        # Register event handlers
        event_bus.on(ConnectionMadeEvent, self.handle_connection_made)
        event_bus.on(ConnectionFailedEvent, self.handle_connection_failed)
        event_bus.on(ConnectionLostEvent, self.handle_connection_lost)
        event_bus.on(TelegramReceivedEvent, self.handle_telegram_received)
        event_bus.on(ModuleDiscoveredEvent, self.handle_module_discovered)
        event_bus.on(ModuleTypeReadEvent, self.handle_module_type_read)
        event_bus.on(ModuleErrorCodeReadEvent, self.handle_module_error_code_read)

    def run(self) -> None:

        # Connect to TCP server
        self.reactor.connectTCP("10.0.3.26", 10001, self.telegram_factory)
        self.reactor.run()

    # Event handlers
    def handle_connection_made(self, event: ConnectionMadeEvent) -> None:
        """Handle connection established - send initial telegram"""
        print("[connection_made] : sending initial telegram")
        event.protocol.sendFrame(b"S0000000000F01D00")

    def handle_connection_failed(self, event: ConnectionFailedEvent) -> None:
        """Handle connection failed"""
        print(f"[connection_failed] : {event.reason}")

    def handle_connection_lost(self, event: ConnectionLostEvent) -> None:
        """Handle connection lost"""
        print(f"[connection_lost] : {event.reason}")

    def handle_telegram_received(self, event: TelegramReceivedEvent) -> None:
        """Handle received telegram events"""
        print(f"[telegram_received] Telegram: {event.telegram}")

        # Check if telegram is Reply (R) with Discover function (F01D)
        if event.telegram.startswith("R") and "F01D" in event.telegram:
            event.event_bus.dispatch(
                ModuleDiscoveredEvent(telegram=event.telegram, protocol=event.protocol)
            )

        # Check if telegram is Reply (R) with Read (F02) for ModuleType (D00)
        if event.telegram.startswith("R") and "F02D00" in event.telegram:
            event.event_bus.dispatch(
                ModuleTypeReadEvent(telegram=event.telegram, protocol=event.protocol)
            )

        # Check if telegram is Reply (R) with Read (F02) for ModuleErrorCode (D10)
        if event.telegram.startswith("R") and "F02D10" in event.telegram:
            event.event_bus.dispatch(
                ModuleErrorCodeReadEvent(
                    telegram=event.telegram, protocol=event.protocol
                )
            )

    def handle_module_discovered(self, event: ModuleDiscoveredEvent) -> None:

        # Replace R with S and F01D with F02D00
        new_telegram = event.telegram.replace("R", "S", 1).replace(
            "F01D", "F02D00", 1
        )  # module type

        print(f"[module_discovered] Sending follow-up: {new_telegram}")
        event.protocol.sendFrame(new_telegram.encode())

    def handle_module_type_read(self, event: ModuleTypeReadEvent) -> None:

        # Replace R with S and F01D with F02D00
        new_telegram = event.telegram.replace("R", "S", 1).replace(
            "F02D00", "F02D10", 1
        )  # error code

        print(f"[moduletype_read] Sending follow-up: {new_telegram}")
        event.protocol.sendFrame(new_telegram.encode())

    def handle_module_error_code_read(self, event: ModuleTypeReadEvent) -> None:

        print("[module_error_code] finished")
