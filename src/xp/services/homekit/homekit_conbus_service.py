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
    """homeKitConbusService"""

    event_bus: EventBus

    def __init__(self, event_bus: EventBus, telegram_protocol: TelegramProtocol):
        self.logger = logging.getLogger(__name__)
        self.event_bus = event_bus
        self.telegram_protocol = telegram_protocol

        # Register event handlers
        self.event_bus.on(
            ReadDatapointFromProtocolEvent, self.handle_read_datapoint_event
        )
        self.event_bus.on(SendActionEvent, self.handle_send_action_event)
        self.event_bus.on(SendWriteConfigEvent, self.handle_send_write_config_event)

    def handle_read_datapoint_event(
        self, event: ReadDatapointFromProtocolEvent
    ) -> None:
        self.logger.debug(f"read_datapoint_event {event}")

        system_function = SystemFunction.READ_DATAPOINT.value
        datapoint_value = event.datapoint_type.value
        telegram = f"S{event.serial_number}F{system_function}D{datapoint_value}"
        self.telegram_protocol.sendFrame(telegram.encode())

    def handle_send_write_config_event(self, event: SendWriteConfigEvent) -> None:
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
        self.logger.debug(f"send_action_event {event}")

        action_value = (
            ActionType.ON_RELEASE.value if event.value else ActionType.OFF_PRESS.value
        )
        input_action = f"{event.output_number:02d}{action_value}"
        telegram = (
            f"S{event.serial_number}F{SystemFunction.ACTION.value}D{input_action}"
        )
        self.telegram_protocol.sendFrame(telegram.encode())
