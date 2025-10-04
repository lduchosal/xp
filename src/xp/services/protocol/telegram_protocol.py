from bubus import EventBus
from twisted.internet import protocol

from xp.models.protocol.conbus_protocol import ConnectionMadeEvent, InvalidTelegramReceivedEvent, TelegramReceivedEvent
from xp.utils import calculate_checksum

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
                event = self.event_bus.dispatch(
                    InvalidTelegramReceivedEvent(protocol=self, telegram=self.buffer)
                )
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

