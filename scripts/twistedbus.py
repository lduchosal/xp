from typing import cast, Any

# Install asyncio reactor before importing reactor
from twisted.internet import asyncioreactor
asyncioreactor.install()

from bubus import EventBus, BaseEvent
from pydantic import Field
from twisted.internet import reactor, protocol
from twisted.internet.interfaces import IAddress, IConnector
from twisted.python.failure import Failure

from xp.utils.checksum import calculate_checksum

class TelegramProtocol(protocol.Protocol):
    buffer: bytes
    event_bus: EventBus

    def __init__(self, event_bus: EventBus) -> None:
        self.buffer = b""
        self.event_bus = event_bus

    def connectionMade(self) -> None:
        print("Connected to 10.0.3.26:10001")
        # Dispatch connection event to event bus
        self.event_bus.dispatch(ConnectionMadeEvent(protocol=self))

    def dataReceived(self, data: bytes) -> None:
        self.buffer += data

        while True:
            start = self.buffer.find(b"<")
            if start == -1:
                break

            end = self.buffer.find(b">", start)
            if end == -1:
                break

            frame = self.buffer[start + 1 : end]
            self.buffer = self.buffer[end + 1 :]
            payload = frame[:-2].decode()
            payload_checksum = frame[-2:].decode()
            calculated_checksum = calculate_checksum(payload)

            if payload_checksum != calculated_checksum:
                print(
                    f"Invalid frame: {frame.decode()} checksum: {payload_checksum}, expected {calculated_checksum}"
                )
                return

            self.frameReceived(frame[:-2])

    def frameReceived(self, frame: bytes) -> None:
        telegram = frame.decode()
        raw_frame = f"<{frame.decode()}>"
        print(f"Received: {telegram}")

        # Dispatch event to bubus
        event = self.event_bus.dispatch(
            TelegramReceivedEvent(protocol=self, telegram=telegram, raw_frame=raw_frame)
        )

    def sendFrame(self, data: bytes) -> None:
        print(f"Sending: {data.decode()}")

        checksum = calculate_checksum(data.decode())
        frame_data = data.decode() + checksum
        frame = b"<" + frame_data.encode() + b">"
        if not self.transport:
            print(f"Invalid transport")
            return
        self.transport.write(frame)  # type: ignore


class ConnectionMadeEvent(BaseEvent):
    """Event dispatched when TCP connection is established"""

    protocol: TelegramProtocol = Field(description="Reference to the TelegramProtocol instance")


class ConnectionFailedEvent(BaseEvent):
    """Event dispatched when TCP connection fails"""

    reason: str = Field(description="Failure reason")


class ConnectionLostEvent(BaseEvent):
    """Event dispatched when TCP connection is lost"""

    reason: str = Field(description="Disconnection reason")

class ModuleDiscoveredEvent(BaseEvent):
    """Event dispatched when TCP connection is lost"""

    protocol: TelegramProtocol = Field(description="Reference to the TelegramProtocol instance")
    telegram: str = Field(description="The received telegram payload")

class ModuleTypeReadEvent(BaseEvent):
    """Event dispatched when TCP connection is lost"""

    protocol: TelegramProtocol = Field(description="Reference to the TelegramProtocol instance")
    telegram: str = Field(description="The received telegram payload")

class ModuleErrorCodeReadEvent(BaseEvent):
    """Event dispatched when TCP connection is lost"""

    protocol: TelegramProtocol = Field(description="Reference to the TelegramProtocol instance")
    telegram: str = Field(description="The received telegram payload")

class TelegramReceivedEvent(BaseEvent):
    """Event dispatched when a telegram frame is received"""

    protocol: TelegramProtocol = Field(description="Reference to the TelegramProtocol instance")
    telegram: str = Field(description="The received telegram payload")
    raw_frame: str = Field(description="The raw frame with delimiters")


class TelegramFactory(protocol.ClientFactory):
    def __init__(self, event_bus: EventBus) -> None:
        self.event_bus = event_bus

    def buildProtocol(self, addr: IAddress) -> TelegramProtocol:
        return TelegramProtocol(self.event_bus)

    def clientConnectionFailed(self, connector: IConnector, reason: Failure) -> None:
        self.event_bus.dispatch(ConnectionFailedEvent(reason=str(reason)))
        reactor.stop()  # type: ignore

    def clientConnectionLost(self, connector: IConnector, reason: Failure) -> None:
        self.event_bus.dispatch(ConnectionLostEvent(reason=str(reason)))
        reactor.stop()  # type: ignore


# Event handlers
def handle_connection_made(event: ConnectionMadeEvent) -> None:
    """Handle connection established - send initial telegram"""
    print("[Event Handler] Connection established, sending initial telegram")
    event.protocol.sendFrame(b"S0000000000F01D00")


def handle_connection_failed(event: ConnectionFailedEvent) -> None:
    """Handle connection failed"""
    print(f"[Event Handler] Connection failed: {event.reason}")


def handle_connection_lost(event: ConnectionLostEvent) -> None:
    """Handle connection lost"""
    print(f"[Event Handler] Connection lost: {event.reason}")


def handle_telegram_received(event: TelegramReceivedEvent) -> None:
    """Handle received telegram events"""
    print(f"[Event Handler] Telegram: {event.telegram}")

    # Check if telegram is Reply (R) with Discover function (F01D)
    if event.telegram.startswith("R") and "F01D" in event.telegram:
        event.event_bus.dispatch(ModuleDiscoveredEvent(telegram=event.telegram, protocol=event.protocol))

    # Check if telegram is Reply (R) with Read (F02) for ModuleType (D00)
    if event.telegram.startswith("R") and "F02D00" in event.telegram:
        event.event_bus.dispatch(ModuleTypeReadEvent(telegram=event.telegram, protocol=event.protocol))

    # Check if telegram is Reply (R) with Read (F02) for ModuleErrorCode (D10)
    if event.telegram.startswith("R") and "F02D10" in event.telegram:
        event.event_bus.dispatch(ModuleErrorCodeReadEvent(telegram=event.telegram, protocol=event.protocol))


def handle_module_discovered(event: ModuleDiscoveredEvent) -> None:

    # Replace R with S and F01D with F02D00
    new_telegram = event.telegram \
        .replace("R", "S", 1) \
        .replace("F01D", "F02D00", 1)  # module type

    print(f"[Event Handler] Sending follow-up: {new_telegram}")
    event.protocol.sendFrame(new_telegram.encode())

def handle_moduletype_read(event: ModuleTypeReadEvent) -> None:

    # Replace R with S and F01D with F02D00
    new_telegram = event.telegram \
        .replace("R", "S", 1) \
        .replace("F02D00", "F02D10", 1) # error code

    print(f"[Event Handler] Sending follow-up: {new_telegram}")
    event.protocol.sendFrame(new_telegram.encode())


def handle_moduleerrorcode_read(event: ModuleTypeReadEvent) -> None:

    print(f"[Event Handler] finished")



if __name__ == "__main__":


    # Create event bus
    bus = EventBus()

    # Register event handlers
    bus.on(ConnectionMadeEvent, handle_connection_made)
    bus.on(ConnectionFailedEvent, handle_connection_failed)
    bus.on(ConnectionLostEvent, handle_connection_lost)
    bus.on(TelegramReceivedEvent, handle_telegram_received)
    bus.on(ModuleDiscoveredEvent, handle_module_discovered)
    bus.on(ModuleTypeReadEvent, handle_moduletype_read)
    bus.on(ModuleErrorCodeReadEvent, handle_moduleerrorcode_read)


    # Connect to TCP server
    reactor = cast(Any, reactor)
    reactor.connectTCP("10.0.3.26", 10001, TelegramFactory(bus))  # type: ignore
    reactor.run()  # type: ignore