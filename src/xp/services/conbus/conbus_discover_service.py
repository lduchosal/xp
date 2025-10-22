"""Conbus Discover Service for TCP communication with Conbus servers.

This service implements a TCP client that connects to Conbus servers and sends
discover telegrams to find modules on the network.
"""

import logging
from typing import Callable, Optional

from twisted.internet.posixbase import PosixReactorBase

from xp.models import ConbusClientConfig, ConbusDiscoverResponse
from xp.models.conbus.conbus_discover import DiscoveredDevice
from xp.models.protocol.conbus_protocol import TelegramReceivedEvent
from xp.models.telegram.datapoint_type import DataPointType
from xp.models.telegram.module_type_code import MODULE_TYPE_REGISTRY
from xp.models.telegram.system_function import SystemFunction
from xp.models.telegram.telegram_type import TelegramType
from xp.services.protocol.conbus_protocol import ConbusProtocol


class ConbusDiscoverService(ConbusProtocol):
    """
    Service for discovering modules on Conbus servers.

    Uses ConbusProtocol to provide discovery functionality for finding
    modules connected to the Conbus network.
    """

    def __init__(
        self,
        cli_config: ConbusClientConfig,
        reactor: PosixReactorBase,
    ) -> None:
        """Initialize the Conbus discover service.

        Args:
            cli_config: Conbus client configuration.
            reactor: Twisted reactor instance.
        """
        super().__init__(cli_config, reactor)
        self.progress_callback: Optional[Callable[[str], None]] = None
        self.finish_callback: Optional[Callable[[ConbusDiscoverResponse], None]] = None

        self.discovered_device_result = ConbusDiscoverResponse(success=False)
        # Set up logging
        self.logger = logging.getLogger(__name__)

    def connection_established(self) -> None:
        """Handle connection established event."""
        self.logger.debug("Connection established, sending discover telegram")
        self.send_telegram(
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
            self.discovered_device(telegram_received.serial_number)

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

    def discovered_device(self, serial_number: str) -> None:
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

        # Send READ_DATAPOINT telegram to query module type
        self.logger.debug(f"Sending module type query for {serial_number}")
        self.send_telegram(
            telegram_type=TelegramType.SYSTEM,
            serial_number=serial_number,
            system_function=SystemFunction.READ_DATAPOINT,
            data_value=DataPointType.MODULE_TYPE.value,
        )

        self.send_telegram(
            telegram_type=TelegramType.SYSTEM,
            serial_number=serial_number,
            system_function=SystemFunction.READ_DATAPOINT,
            data_value=DataPointType.MODULE_TYPE_CODE.value,
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
                    self.logger.debug(
                        f"Updated device {serial_number} with module_type {module_type_name}"
                    )
                    break

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
                    break

    def timeout(self) -> bool:
        """Handle timeout event to stop discovery.

        Returns:
            False to stop the reactor.
        """
        self.logger.info("Discovery stopped after: %ss", self.timeout_seconds)
        self.discovered_device_result.success = True
        if self.finish_callback:
            self.finish_callback(self.discovered_device_result)
        return False

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

    def start(
        self,
        progress_callback: Callable[[str], None],
        finish_callback: Callable[[ConbusDiscoverResponse], None],
        timeout_seconds: Optional[float] = None,
    ) -> None:
        """Run reactor in dedicated thread with its own event loop.

        Args:
            progress_callback: Callback for each discovered device.
            finish_callback: Callback when discovery completes.
            timeout_seconds: Optional timeout in seconds.
        """
        self.logger.info("Starting discovery")
        if timeout_seconds:
            self.timeout_seconds = timeout_seconds
        self.progress_callback = progress_callback
        self.finish_callback = finish_callback
        self.start_reactor()
