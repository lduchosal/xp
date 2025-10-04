from typing import cast, Any

from twisted.internet import reactor, protocol
from twisted.internet.interfaces import IAddress, IConnector
from twisted.python.failure import Failure

class TelegramProtocol(protocol.Protocol):
    buffer: bytes

    def __init__(self) -> None:
        self.buffer = b""

    def connectionMade(self) -> None:
        print("Connected to 10.0.3.26:10001")
        self.sendFrame(b"S0000000000F01D00FA")

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

            self.frameReceived(frame)

    def frameReceived(self, frame: bytes) -> None:
        print(f"Received: {frame.decode()}")

    def sendFrame(self, data: bytes) -> None:
        frame = b"<" + data + b">"
        print(f"Sending: {data.decode()}")
        if self.transport:
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