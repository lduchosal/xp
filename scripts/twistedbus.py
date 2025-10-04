from typing import cast, Any

from bubus import EventBus, BaseEvent
from pydantic import Field
from twisted.internet import reactor, protocol
from twisted.internet.interfaces import IAddress, IConnector
from twisted.python.failure import Failure

from xp.utils.checksum import calculate_checksum


class OnConnectionMadeEvent(BaseEvent):
    """Event dispatched when TCP connection is established"""

    protocol: Any = Field(description="Reference to the TelegramProtocol instance")


class TelegramReceivedEvent(BaseEvent):
    """Event dispatched when a telegram frame is received"""

    telegram: str = Field(description="The received telegram payload")
    raw_frame: str = Field(description="The raw frame with delimiters")


class TelegramProtocol(protocol.Protocol):
    buffer: bytes
    event_bus: EventBus

    def __init__(self, event_bus: EventBus) -> None:
        self.buffer = b""
        self.event_bus = event_bus

    def connectionMade(self) -> None:
        print("Connected to 10.0.3.26:10001")
        self.sendFrame(b"S0000000000F01D00")

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
            TelegramReceivedEvent(telegram=telegram, raw_frame=raw_frame)
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

class TelegramFactory(protocol.ClientFactory):
    def __init__(self, event_bus: EventBus) -> None:
        self.event_bus = event_bus

    def buildProtocol(self, addr: IAddress) -> TelegramProtocol:
        return TelegramProtocol(self.event_bus)

    def clientConnectionFailed(self, connector: IConnector, reason: Failure) -> None:
        print(f"Connection failed: {reason}")
        reactor.stop()  # type: ignore

    def clientConnectionLost(self, connector: IConnector, reason: Failure) -> None:
        print(f"Connection lost: {reason}")
        reactor.stop()  # type: ignore


# Example event handler
def handle_telegram(event: TelegramReceivedEvent) -> None:
    """Handle received telegram events"""
    print(f"[Event Handler] Telegram: {event.telegram}")
    print(f"[Event Handler] Raw frame: {event.raw_frame}")


if __name__ == "__main__":
    # Create event bus
    bus = EventBus()

    # Register event handlers
    bus.on(TelegramReceivedEvent, handle_telegram)

    # Connect to TCP server
    reactor = cast(Any, reactor)
    reactor.connectTCP("10.0.3.26", 10001, TelegramFactory(bus))  # type: ignore
    reactor.run()  # type: ignore