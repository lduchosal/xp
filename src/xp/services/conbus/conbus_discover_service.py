# Copyright (c) 2025 ldvchosal
"""Conbus Discover Service for TCP communication with Conbus servers.

This service implements a TCP client that connects to Conbus servers and sends discover
telegrams to find modules on the network.
"""

import asyncio
import logging
from types import TracebackType
from typing import Self

from psygnal import Signal

from xp.models import ConbusDiscoverResponse
from xp.models.conbus.conbus_discover import DiscoveredDevice
from xp.models.protocol.conbus_protocol import TelegramReceivedEvent
from xp.models.telegram.datapoint_type import DataPointType
from xp.models.telegram.module_type_code import MODULE_TYPE_REGISTRY
from xp.models.telegram.system_function import SystemFunction
from xp.models.telegram.telegram_type import TelegramType
from xp.services.protocol.conbus_event_protocol import ConbusEventProtocol

# Discovery reply payload: type char (1) + serial number (10) + "F01D" (4)
DISCOVER_REPLY_PAYLOAD_LENGTH = 15

# Module type reply payload: type char (1) + serial (10) + "F02Dxx" (6) + code (2)
MODULE_TYPE_REPLY_MIN_PAYLOAD_LENGTH = 19


class ConbusDiscoverService:
    """Service for discovering modules on Conbus servers.

    Uses ConbusEventProtocol to provide discovery functionality for finding
    modules connected to the Conbus network.

    Attributes:
        conbus_protocol: Protocol instance for Conbus communication.
        on_progress: Signal emitted on discovery progress (with serial number).
        on_finish: Signal emitted when discovery finishes (with result).
        on_device_discovered: Signal emitted when a device is discovered (with info).

    """

    conbus_protocol: ConbusEventProtocol
    on_progress: Signal = Signal(str)
    on_finish: Signal = Signal(DiscoveredDevice)
    on_device_discovered: Signal = Signal(ConbusDiscoverResponse)

    def __init__(self, conbus_protocol: ConbusEventProtocol) -> None:
        """Initialize the Conbus discover service.

        Args:
            conbus_protocol: ConbusEventProtocol instance for communication.

        """
        self.conbus_protocol: ConbusEventProtocol = conbus_protocol
        self.conbus_protocol.on_connection_made.connect(self.connection_made)
        self.conbus_protocol.on_telegram_sent.connect(self.telegram_sent)
        self.conbus_protocol.on_telegram_received.connect(self.telegram_received)
        self.conbus_protocol.on_timeout.connect(self.timeout)
        self.conbus_protocol.on_failed.connect(self.failed)

        self.discovered_device_result = ConbusDiscoverResponse(success=False)
        # Set up logging
        self.logger = logging.getLogger(__name__)

    def connection_made(self) -> None:
        """Handle connection established event."""
        self.logger.debug("Connection established")
        self.logger.debug("Sending discover telegram")
        self.conbus_protocol.send_telegram(
            telegram_type=TelegramType.SYSTEM,
            serial_number="0000000000",
            system_function=SystemFunction.DISCOVERY,
            data_value="00",
        )

    def telegram_sent(self, telegram_sent: str) -> None:
        """Handle telegram sent event.

        Args:
            telegram_sent: The telegram that was sent.

        """
        self.logger.debug("Telegram sent: %s", telegram_sent)
        self.discovered_device_result.sent_telegram = telegram_sent

    def telegram_received(self, telegram_received: TelegramReceivedEvent) -> None:
        """Handle telegram received event.

        Args:
            telegram_received: The telegram received event.

        """
        self.logger.debug("Telegram received: %s", telegram_received)
        if not self.discovered_device_result.received_telegrams:
            self.discovered_device_result.received_telegrams = []
        self.discovered_device_result.received_telegrams.append(telegram_received.frame)

        # Check for discovery response
        if (
            telegram_received.checksum_valid
            and telegram_received.telegram_type == TelegramType.REPLY.value
            and telegram_received.payload[11:15] == "F01D"
            and len(telegram_received.payload) == DISCOVER_REPLY_PAYLOAD_LENGTH
        ):
            self.handle_discovered_device(telegram_received.serial_number)

        # Check for module type response (F02D07)
        elif (
            telegram_received.checksum_valid
            and telegram_received.telegram_type == TelegramType.REPLY.value
            and telegram_received.payload[11:17] == "F02D07"
            and len(telegram_received.payload) >= MODULE_TYPE_REPLY_MIN_PAYLOAD_LENGTH
        ):
            self.handle_module_type_code_response(
                telegram_received.serial_number, telegram_received.payload[17:19]
            )
        # Check for module type response (F02D00)
        elif (
            telegram_received.checksum_valid
            and telegram_received.telegram_type == TelegramType.REPLY.value
            and telegram_received.payload[11:17] == "F02D00"
            and len(telegram_received.payload) >= MODULE_TYPE_REPLY_MIN_PAYLOAD_LENGTH
        ):
            self.handle_module_type_response(
                telegram_received.serial_number, telegram_received.payload[17:19]
            )

        else:
            self.logger.debug("Not a discover or module type response")

    def handle_discovered_device(self, serial_number: str) -> None:
        """Handle discovered device event.

        Args:
            serial_number: Serial number of the discovered device.

        """
        self.logger.info("discovered_device: %s", serial_number)
        if not self.discovered_device_result.discovered_devices:
            self.discovered_device_result.discovered_devices = []

        # Add device with module_type as None initially
        device: DiscoveredDevice = {
            "serial_number": serial_number,
            "module_type": None,
            "module_type_code": None,
            "module_type_name": None,
        }
        self.discovered_device_result.discovered_devices.append(device)
        self.on_device_discovered.emit(device)

        # Send READ_DATAPOINT telegram to query module type
        self.logger.debug("Sending module type query for %s", serial_number)
        self.conbus_protocol.send_telegram(
            telegram_type=TelegramType.SYSTEM,
            serial_number=serial_number,
            system_function=SystemFunction.READ_DATAPOINT,
            data_value=DataPointType.MODULE_TYPE.value,
        )
        self.on_progress.emit(serial_number)

    def handle_module_type_code_response(
        self, serial_number: str, module_type_code: str
    ) -> None:
        """Handle module type code response and update discovered device.

        Args:
            serial_number: Serial number of the device.
            module_type_code: Module type code from telegram (e.g., "07", "24").

        """
        self.logger.info(
            "Received module type code %s for %s", module_type_code, serial_number
        )

        # Convert module type code to name
        code = 0
        try:
            # The telegram format uses decimal values represented as strings
            code = int(module_type_code)
            module_info = MODULE_TYPE_REGISTRY.get(code)

            if module_info:
                module_type_name = module_info["name"]
                self.logger.debug(
                    "Module type code %s (%s) = %s",
                    module_type_code,
                    code,
                    module_type_name,
                )
            else:
                module_type_name = f"UNKNOWN_{module_type_code}"
                self.logger.warning(
                    "Unknown module type code %s (%s)", module_type_code, code
                )

        except ValueError:
            self.logger.exception(
                "Invalid module type code format: %s for %s",
                module_type_code,
                serial_number,
            )
            module_type_name = f"INVALID_{module_type_code}"

        # Find and update the device in discovered_devices
        if self.discovered_device_result.discovered_devices:
            for device in self.discovered_device_result.discovered_devices:
                if device["serial_number"] == serial_number:
                    device["module_type_code"] = code
                    device["module_type_name"] = module_type_name

                    self.on_device_discovered.emit(device)

                    self.logger.debug(
                        "Updated device %s with module_type %s",
                        serial_number,
                        module_type_name,
                    )
                    break

        if self.discovered_device_result.discovered_devices:
            for device in self.discovered_device_result.discovered_devices:
                if not (
                    device["serial_number"]
                    and device["module_type"]
                    # `is not None` : le code 0 (NOMOD) est une valeur complète.
                    and device["module_type_code"] is not None
                    and device["module_type_name"]
                ):
                    return

        self.succeed()

    def handle_module_type_response(self, serial_number: str, module_type: str) -> None:
        """Handle module type response and update discovered device.

        Args:
            serial_number: Serial number of the device.
            module_type: Module type code from telegram (e.g., "XP33", "XP24").

        """
        self.logger.info("Received module type %s for %s", module_type, serial_number)

        # Find and update the device in discovered_devices
        if self.discovered_device_result.discovered_devices:
            for device in self.discovered_device_result.discovered_devices:
                if device["serial_number"] == serial_number:
                    device["module_type"] = module_type
                    self.logger.debug(
                        "Updated device %s with module_type %s",
                        serial_number,
                        module_type,
                    )
                    self.on_device_discovered.emit(device)
                    break

        self.conbus_protocol.send_telegram(
            telegram_type=TelegramType.SYSTEM,
            serial_number=serial_number,
            system_function=SystemFunction.READ_DATAPOINT,
            data_value=DataPointType.MODULE_TYPE_CODE.value,
        )

    def timeout(self) -> None:
        """Handle timeout event to stop discovery."""
        timeout = self.conbus_protocol.timeout_seconds
        self.logger.info("Discovery stopped after: %ss", timeout)
        self.discovered_device_result.success = False
        self.discovered_device_result.error = "Discovered device timeout"
        self.on_finish.emit(self.discovered_device_result)

    def failed(self, message: str) -> None:
        """Handle failed connection event.

        Args:
            message: Failure message.

        """
        self.logger.debug("Failed: %s", message)
        self.discovered_device_result.success = False
        self.discovered_device_result.error = message
        self.on_finish.emit(self.discovered_device_result)

    def succeed(self) -> None:
        """Handle discovered device success event."""
        self.logger.debug("Succeed")
        self.discovered_device_result.success = True
        self.discovered_device_result.error = None
        self.on_finish.emit(self.discovered_device_result)

    def set_timeout(self, timeout_seconds: float) -> None:
        """Set the timeout for receiving telegrams.

        Args:
            timeout_seconds: Optional timeout in seconds.

        """
        self.logger.debug("Set timeout")
        self.conbus_protocol.timeout_seconds = timeout_seconds

    def set_event_loop(
        self,
        event_loop: asyncio.AbstractEventLoop,
    ) -> None:
        """Set the event loop used for async operations.

        Args:
            event_loop: Optional event loop to use for async operations.

        """
        self.logger.debug("Set eventloop")
        self.conbus_protocol.set_event_loop(event_loop)

    def start_reactor(self) -> None:
        """Start the reactor."""
        self.conbus_protocol.start_reactor()

    def stop_reactor(self) -> None:
        """Start the reactor."""
        self.conbus_protocol.stop_reactor()

    def __enter__(self) -> Self:
        """Enter context manager.

        Returns:
            Self for context manager protocol.

        """
        # Reset state for singleton reuse
        self.discovered_device_result = ConbusDiscoverResponse(success=False)
        return self

    def __exit__(
        self,
        _exc_type: type[BaseException] | None,
        _exc_val: BaseException | None,
        _exc_tb: TracebackType | None,
    ) -> None:
        """Exit context manager and disconnect signals."""
        self.conbus_protocol.on_connection_made.disconnect(self.connection_made)
        self.conbus_protocol.on_telegram_sent.disconnect(self.telegram_sent)
        self.conbus_protocol.on_telegram_received.disconnect(self.telegram_received)
        self.conbus_protocol.on_timeout.disconnect(self.timeout)
        self.conbus_protocol.on_failed.disconnect(self.failed)
        self.on_device_discovered.disconnect()
        self.on_progress.disconnect()
        self.on_finish.disconnect()
        self.stop_reactor()
