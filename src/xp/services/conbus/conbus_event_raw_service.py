"""Conbus Event Raw Service for sending raw event telegrams.

This service implements a TCP client that connects to Conbus servers and sends
raw event telegrams to simulate button presses on Conbus modules.
"""

import logging
from typing import Callable, Optional

from twisted.internet.base import DelayedCall

from xp.models import ConbusEventRawResponse
from xp.models.protocol.conbus_protocol import TelegramReceivedEvent
from xp.services.protocol.conbus_event_protocol import ConbusEventProtocol


class ConbusEventRawService:
    """Service for sending raw event telegrams to Conbus servers.

    Uses ConbusEventProtocol to send MAKE/BREAK event sequences to
    simulate button presses on Conbus modules.

    Attributes:
        conbus_protocol: Protocol instance for Conbus communication.
    """

    conbus_protocol: ConbusEventProtocol

    def __init__(self, conbus_protocol: ConbusEventProtocol) -> None:
        """Initialize the Conbus event raw service.

        Args:
            conbus_protocol: ConbusEventProtocol instance.
        """
        self.progress_callback: Optional[Callable[[str], None]] = None
        self.finish_callback: Optional[Callable[[ConbusEventRawResponse], None]] = None

        self.conbus_protocol: ConbusEventProtocol = conbus_protocol
        self.conbus_protocol.on_connection_made.connect(self.connection_made)
        self.conbus_protocol.on_telegram_sent.connect(self.telegram_sent)
        self.conbus_protocol.on_telegram_received.connect(self.telegram_received)
        self.conbus_protocol.on_timeout.connect(self.timeout)
        self.conbus_protocol.on_failed.connect(self.failed)

        self.event_result = ConbusEventRawResponse(success=False)
        self.logger = logging.getLogger(__name__)

        # Event parameters
        self.module_type_code: int = 0
        self.link_number: int = 0
        self.input_number: int = 0
        self.time_ms: int = 1000
        self.break_event_call: Optional[DelayedCall] = None

    def connection_made(self) -> None:
        """Handle connection established event."""
        self.logger.debug("Connection established")
        self.logger.debug("Sending MAKE event telegram")
        self._send_make_event()

    def _send_make_event(self) -> None:
        """Send MAKE event telegram."""
        payload = f"E{self.module_type_code:02d}L{self.link_number:02d}I{self.input_number:02d}M"
        self.logger.debug(f"Sending MAKE event: {payload}")
        self.conbus_protocol.telegram_queue.put_nowait(payload.encode())
        self.conbus_protocol.call_later(0.0, self.conbus_protocol.start_queue_manager)

        # Schedule BREAK event after delay
        delay_seconds = self.time_ms / 1000.0
        self.break_event_call = self.conbus_protocol.call_later(
            delay_seconds, self._send_break_event
        )

    def _send_break_event(self) -> None:
        """Send BREAK event telegram."""
        payload = f"E{self.module_type_code:02d}L{self.link_number:02d}I{self.input_number:02d}B"
        self.logger.debug(f"Sending BREAK event: {payload}")
        self.conbus_protocol.telegram_queue.put_nowait(payload.encode())
        self.conbus_protocol.call_later(0.0, self.conbus_protocol.start_queue_manager)

    def telegram_sent(self, telegram_sent: str) -> None:
        """Handle telegram sent event.

        Args:
            telegram_sent: The telegram that was sent.
        """
        self.logger.debug(f"Telegram sent: {telegram_sent}")
        if self.event_result.sent_telegrams is None:
            self.event_result.sent_telegrams = []
        self.event_result.sent_telegrams.append(telegram_sent)

    def telegram_received(self, telegram_received: TelegramReceivedEvent) -> None:
        """Handle telegram received event.

        Args:
            telegram_received: The telegram received event.
        """
        self.logger.debug(f"Telegram received: {telegram_received.frame}")
        if self.event_result.received_telegrams is None:
            self.event_result.received_telegrams = []
        self.event_result.received_telegrams.append(telegram_received.frame)

        # Display progress - show ALL received telegrams
        if self.progress_callback:
            self.progress_callback(telegram_received.frame)

    def timeout(self) -> None:
        """Handle timeout event.

        Timeout is the normal/expected way to finish this service.
        """
        timeout_seconds = self.conbus_protocol.timeout_seconds
        self.logger.info("Event raw finished after timeout: %ss", timeout_seconds)
        self.event_result.success = True
        self.event_result.error = None
        if self.finish_callback:
            self.finish_callback(self.event_result)

        self.stop_reactor()

    def failed(self, message: str) -> None:
        """Handle failed connection event.

        Args:
            message: Failure message.
        """
        self.logger.debug(f"Failed: {message}")
        self.event_result.success = False
        self.event_result.error = message
        if self.finish_callback:
            self.finish_callback(self.event_result)

        self.stop_reactor()

    def stop_reactor(self) -> None:
        """Stop reactor."""
        self.logger.info("Stopping reactor")
        # Cancel break event call if it's still pending
        if self.break_event_call and self.break_event_call.active():
            self.break_event_call.cancel()
        self.conbus_protocol.stop_reactor()

    def start_reactor(self) -> None:
        """Start reactor."""
        self.logger.info("Starting reactor")
        self.conbus_protocol.start_reactor()

    def run(
        self,
        module_type_code: int,
        link_number: int,
        input_number: int,
        time_ms: int,
        progress_callback: Optional[Callable[[str], None]],
        finish_callback: Callable[[ConbusEventRawResponse], None],
        timeout_seconds: int = 5,
    ) -> None:
        """Run reactor in dedicated thread with its own event loop.

        Args:
            module_type_code: Module type code (numeric, e.g., 2 for CP20, 33 for XP33).
            link_number: Link number (0-99).
            input_number: Input number (0-9).
            time_ms: Delay in milliseconds between MAKE and BREAK events.
            progress_callback: Callback for progress updates (received telegrams).
            finish_callback: Callback when operation completes.
            timeout_seconds: Timeout in seconds (default: 5).
        """
        self.logger.info(
            f"Starting event raw: module={module_type_code}, "
            f"link={link_number}, input={input_number}, time={time_ms}ms"
        )

        self.module_type_code = module_type_code
        self.link_number = link_number
        self.input_number = input_number
        self.time_ms = time_ms

        self.conbus_protocol.timeout_seconds = timeout_seconds
        self.progress_callback = progress_callback
        self.finish_callback = finish_callback
