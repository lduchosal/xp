import logging

from twisted.internet import protocol
from twisted.internet.interfaces import IConnector
from twisted.python.failure import Failure

from xp.models.protocol.conbus_protocol import (
    TelegramReceivedEvent,
)
from xp.models.telegram.system_function import SystemFunction
from xp.models.telegram.telegram_type import TelegramType
from xp.utils import calculate_checksum


class ConbusProtocol(protocol.Protocol):
    """
    Twisted protocol for XP telegram communication.
    """

    buffer: bytes

    def __init__(self) -> None:
        self.buffer = b""
        self.logger = logging.getLogger(__name__)

    def connectionMade(self) -> None:
        self.logger.debug("connectionMade")
        self.connection_established()

    def dataReceived(self, data: bytes) -> None:
        self.logger.debug("dataReceived")
        self.buffer += data

        while True:
            start = self.buffer.find(b"<")
            if start == -1:
                break

            end = self.buffer.find(b">", start)
            if end == -1:
                break

            # <S0123450001F02D12FK>
            # <R0123450001F02D12FK>
            # <E12L01I08MAK>
            frame = self.buffer[start : end + 1]  # <S0123450001F02D12FK>
            self.buffer = self.buffer[end + 1 :]
            telegram = frame[1:-1]  # S0123450001F02D12FK
            telegram_type = telegram[0:1].decode()  # S
            payload = telegram[:-2]  # S0123450001F02D12
            checksum = telegram[-2:].decode()  # FK
            serial_number = (
                telegram[1:11] if telegram_type in ("S", "R") else b""
            )  # 0123450001
            calculated_checksum = calculate_checksum(payload.decode(encoding="latin-1"))

            checksum_valid = checksum == calculated_checksum
            if not checksum_valid:
                self.logger.debug(
                    f"Invalid checksum: {checksum}, calculated: {calculated_checksum}"
                )

            self.logger.debug(
                f"frameReceived payload: {payload.decode()}, checksum: {checksum}"
            )
            # Dispatch event to bubus with await
            telegram_received = TelegramReceivedEvent(
                protocol=self,
                frame=frame.decode(),
                telegram=telegram.decode(),
                payload=payload.decode(),
                telegram_type=telegram_type,
                serial_number=serial_number,
                checksum=checksum,
                checksum_valid=checksum_valid,
            )
            self.telegram_received(telegram_received)

    def sendFrame(self, data: bytes) -> None:
        """
        Send telegram frame

        Args:
            data: Raw telegram payload (without checksum/framing)
        """
        # Calculate full frame (add checksum and brackets)
        checksum = calculate_checksum(data.decode())
        frame_data = data.decode() + checksum
        frame = b"<" + frame_data.encode() + b">"

        if not self.transport:
            self.logger.info("Invalid transport")
            raise IOError("Transport is not open")

        self.logger.debug(f"Sending frame: {frame.decode()}")
        self.transport.write(frame)  # type: ignore

    def send_telegram(
        self,
        telegram_type: TelegramType,
        serial_number: str,
        system_function: SystemFunction,
        data_value: str,
    ) -> None:
        payload = f"{telegram_type.value}{serial_number}F{system_function.value}D{data_value}".encode()
        self.sendFrame(payload)

    def telegram_received(self, telegram_received: TelegramReceivedEvent) -> None:
        pass

    def connection_established(self) -> None:
        pass

    def client_connection_failed(self, connector: IConnector, reason: Failure) -> None:
        self.logger.debug(f"Client connection failed: {reason}")
        connector.stop()

    def client_connection_lost(self, connector: IConnector, reason: Failure) -> None:
        self.logger.debug(f"Client connection failed: {reason}")
        connector.stop()
