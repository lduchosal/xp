"""HomeKit Conbus Service for protocol communication.

This module bridges HomeKit events with the Conbus protocol for device control.
"""

import logging

from bubus import EventBus

from xp.models.protocol.conbus_protocol import (
    ReadDatapointFromProtocolEvent,
    SendActionEvent,
    SendWriteConfigEvent,
)
from xp.models.telegram.action_type import ActionType
from xp.models.telegram.datapoint_type import DataPointType
from xp.models.telegram.system_function import SystemFunction
from xp.services.protocol.telegram_protocol import TelegramProtocol


class HomeKitConbusService:
    """Service for bridging HomeKit events with Conbus protocol.

    Attributes:
        event_bus: Event bus for inter-service communication.
        telegram_protocol: Protocol for sending telegrams.
        logger: Logger instance.
    """

    event_bus: EventBus

    def __init__(self, event_bus: EventBus, telegram_protocol: TelegramProtocol):
        """Initialize the HomeKit Conbus service.

        Args:
            event_bus: Event bus instance.
            telegram_protocol: Telegram protocol instance.
        """
        self.logger = logging.getLogger(__name__)
        self.event_bus = event_bus
        self.telegram_protocol = telegram_protocol

        # Register event handlers
        self.event_bus.on(
            ReadDatapointFromProtocolEvent, self.handle_read_datapoint_request
        )
        self.event_bus.on(SendActionEvent, self.handle_send_action_event)
        self.event_bus.on(SendWriteConfigEvent, self.handle_send_write_config_event)

    def handle_read_datapoint_request(
        self, event: ReadDatapointFromProtocolEvent
    ) -> None:
        """Handle request to read datapoint from protocol.

        Args:
            event: Read datapoint event with serial number and datapoint type.
        """
        self.logger.debug(f"read_datapoint_request {event}")

        system_function = SystemFunction.READ_DATAPOINT.value
        datapoint_value = event.datapoint_type.value
        telegram = f"S{event.serial_number}F{system_function}D{datapoint_value}"
        self.telegram_protocol.sendFrame(telegram.encode())

    def handle_send_write_config_event(self, event: SendWriteConfigEvent) -> None:
        """Handle send write config event.

        Args:
            event: Write config event with configuration data.
        """
        self.logger.debug(f"send_write_config_event {event}")

        # Format data as output_number:level (e.g., "02:050")
        system_function = SystemFunction.WRITE_CONFIG.value
        datapoint_type = DataPointType.MODULE_LIGHT_LEVEL.value
        config_data = f"{event.output_number:02d}:{event.value:03d}"
        telegram = (
            f"S{event.serial_number}F{system_function}D{datapoint_type}{config_data}"
        )
        self.telegram_protocol.sendFrame(telegram.encode())

    def handle_send_action_event(self, event: SendActionEvent) -> None:
        """Handle send action event.

        Args:
            event: Send action event with action data.
        """
        self.logger.debug(f"send_action_event {event}")

        action_value = (
            ActionType.ON_RELEASE.value if event.value else ActionType.OFF_PRESS.value
        )
        input_action = f"{event.output_number:02d}{action_value}"
        telegram = (
            f"S{event.serial_number}F{SystemFunction.ACTION.value}D{input_action}"
        )
        self.telegram_protocol.sendFrame(telegram.encode())
