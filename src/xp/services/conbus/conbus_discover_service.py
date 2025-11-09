"""Conbus Discover Service for TCP communication with Conbus servers.

This service implements a TCP client that connects to Conbus servers and sends
discover telegrams to find modules on the network.
"""

import logging
from typing import Callable, Optional

from xp.models import ConbusDiscoverResponse
from xp.models.conbus.conbus_discover import DiscoveredDevice
from xp.models.protocol.conbus_protocol import TelegramReceivedEvent
from xp.models.telegram.datapoint_type import DataPointType
from xp.models.telegram.module_type_code import MODULE_TYPE_REGISTRY
from xp.models.telegram.system_function import SystemFunction
from xp.models.telegram.telegram_type import TelegramType
from xp.services.protocol.conbus_event_protocol import ConbusEventProtocol


class ConbusDiscoverService:
    """
    Service for discovering modules on Conbus servers.

    Uses ConbusProtocol to provide discovery functionality for finding
    modules connected to the Conbus network.

    Attributes:
        conbus_protocol: Protocol instance for Conbus communication.
    """

    conbus_protocol: ConbusEventProtocol

    def __init__(self, conbus_protocol: ConbusEventProtocol) -> None:
        """Initialize the Conbus discover service.

        Args:
            conbus_protocol: ConbusProtocol.
        """
        self.progress_callback: Optional[Callable[[str], None]] = None
        self.device_discover_callback: Optional[Callable[[DiscoveredDevice], None]] = (
            None
        )
        self.finish_callback: Optional[Callable[[ConbusDiscoverResponse], None]] = None

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
        self.logger.debug(f"Telegram sent: {telegram_sent}")
        self.discovered_device_result.sent_telegram = telegram_sent

    def telegram_received(self, telegram_received: TelegramReceivedEvent) -> None:
        """Handle telegram received event.

        Args:
            telegram_received: The telegram received event.
        """
        self.logger.debug(f"Telegram received: {telegram_received}")
        if not self.discovered_device_result.received_telegrams:
            self.discovered_device_result.received_telegrams = []
        self.discovered_device_result.received_telegrams.append(telegram_received.frame)

        # Check for discovery response
        if (
            telegram_received.checksum_valid
            and telegram_received.telegram_type == TelegramType.REPLY.value
            and telegram_received.payload[11:16] == "F01D"
            and len(telegram_received.payload) == 15
        ):
            self.handle_discovered_device(telegram_received.serial_number)

        # Check for module type response (F02D07)
        elif (
            telegram_received.checksum_valid
            and telegram_received.telegram_type == TelegramType.REPLY.value
            and telegram_received.payload[11:17] == "F02D07"
            and len(telegram_received.payload) >= 19
        ):
            self.handle_module_type_code_response(
                telegram_received.serial_number, telegram_received.payload[17:19]
            )
        # Check for module type response (F02D00)
        elif (
            telegram_received.checksum_valid
            and telegram_received.telegram_type == TelegramType.REPLY.value
            and telegram_received.payload[11:17] == "F02D00"
            and len(telegram_received.payload) >= 19
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

        if self.device_discover_callback:
            self.device_discover_callback(device)

        # Send READ_DATAPOINT telegram to query module type
        self.logger.debug(f"Sending module type query for {serial_number}")
        self.conbus_protocol.send_telegram(
            telegram_type=TelegramType.SYSTEM,
            serial_number=serial_number,
            system_function=SystemFunction.READ_DATAPOINT,
            data_value=DataPointType.MODULE_TYPE.value,
        )
        if self.progress_callback:
            self.progress_callback(serial_number)

    def handle_module_type_code_response(
        self, serial_number: str, module_type_code: str
    ) -> None:
        """Handle module type code response and update discovered device.

        Args:
            serial_number: Serial number of the device.
            module_type_code: Module type code from telegram (e.g., "07", "24").
        """
        self.logger.info(
            f"Received module type code {module_type_code} for {serial_number}"
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
                    f"Module type code {module_type_code} ({code}) = {module_type_name}"
                )
            else:
                module_type_name = f"UNKNOWN_{module_type_code}"
                self.logger.warning(
                    f"Unknown module type code {module_type_code} ({code})"
                )

        except ValueError:
            self.logger.error(
                f"Invalid module type code format: {module_type_code} for {serial_number}"
            )
            module_type_name = f"INVALID_{module_type_code}"

        # Find and update the device in discovered_devices
        if self.discovered_device_result.discovered_devices:
            for device in self.discovered_device_result.discovered_devices:
                if device["serial_number"] == serial_number:
                    device["module_type_code"] = code
                    device["module_type_name"] = module_type_name

                    if self.device_discover_callback:
                        self.device_discover_callback(device)

                    self.logger.debug(
                        f"Updated device {serial_number} with module_type {module_type_name}"
                    )
                    break

        if self.discovered_device_result.discovered_devices:
            for device in self.discovered_device_result.discovered_devices:
                if not (
                    device["serial_number"]
                    and device["module_type"]
                    and device["module_type_code"]
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
        self.logger.info(f"Received module type {module_type} for {serial_number}")

        # Find and update the device in discovered_devices
        if self.discovered_device_result.discovered_devices:
            for device in self.discovered_device_result.discovered_devices:
                if device["serial_number"] == serial_number:
                    device["module_type"] = module_type
                    self.logger.debug(
                        f"Updated device {serial_number} with module_type {module_type}"
                    )
                    if self.device_discover_callback:
                        self.device_discover_callback(device)

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
        if self.finish_callback:
            self.finish_callback(self.discovered_device_result)

        self.stop_reactor()

    def failed(self, message: str) -> None:
        """Handle failed connection event.

        Args:
            message: Failure message.
        """
        self.logger.debug(f"Failed: {message}")
        self.discovered_device_result.success = False
        self.discovered_device_result.error = message
        if self.finish_callback:
            self.finish_callback(self.discovered_device_result)

        self.stop_reactor()

    def succeed(self) -> None:
        """Handle discovered device success event."""
        self.logger.debug("Succeed")
        self.discovered_device_result.success = True
        self.discovered_device_result.error = None
        if self.finish_callback:
            self.finish_callback(self.discovered_device_result)

        self.stop_reactor()

    def stop_reactor(self) -> None:
        """Stop reactor."""
        self.logger.info("Stopping reactor")
        self.conbus_protocol.stop_reactor()

    def start_reactor(self) -> None:
        """Start reactor."""
        self.logger.info("Starting reactor")
        self.conbus_protocol.start_reactor()

    def run(
        self,
        progress_callback: Callable[[str], None],
        device_discover_callback: Callable[[DiscoveredDevice], None],
        finish_callback: Callable[[ConbusDiscoverResponse], None],
        timeout_seconds: Optional[float] = None,
    ) -> None:
        """Run reactor in dedicated thread with its own event loop.

        Args:
            progress_callback: Callback for each discovered device.
            device_discover_callback: Callback for each discovered device.
            finish_callback: Callback when discovery completes.
            timeout_seconds: Optional timeout in seconds.
        """
        self.logger.info("Starting discovery")

        if timeout_seconds:
            self.conbus_protocol.timeout_seconds = timeout_seconds
        self.progress_callback = progress_callback
        self.device_discover_callback = device_discover_callback
        self.finish_callback = finish_callback
