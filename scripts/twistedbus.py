from typing import cast, Any

from twisted.internet import reactor, protocol
from twisted.internet.interfaces import IAddress, IConnector
from twisted.python.failure import Failure

from xp.utils.checksum import calculate_checksum

class TelegramProtocol(protocol.Protocol):
    buffer: bytes

    def __init__(self) -> None:
        self.buffer = b""

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
                print(f"Invalid frame: {frame.decode()} checksum: {payload_checksum}, expected {calculated_checksum}")
                return

            self.frameReceived(frame[:-2])

    def frameReceived(self, frame: bytes) -> None:

        print(f"Received: {frame.decode()}")

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
    def buildProtocol(self, addr: IAddress) -> TelegramProtocol:
        return TelegramProtocol()

    def clientConnectionFailed(self, connector: IConnector, reason: Failure) -> None:
        print(f"Connection failed: {reason}")
        reactor.stop()  # type: ignore

    def clientConnectionLost(self, connector: IConnector, reason: Failure) -> None:
        print(f"Connection lost: {reason}")
        reactor.stop()  # type: ignore

if __name__ == "__main__":
    reactor = cast(Any, reactor)
    reactor.connectTCP("10.0.3.26", 10001, TelegramFactory())  # type: ignore
    reactor.run()  # type: ignore