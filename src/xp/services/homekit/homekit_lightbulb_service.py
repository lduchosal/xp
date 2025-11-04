"""HomeKit Light Bulb Service.

This module provides service implementation for light bulb accessories.
"""

import logging

from bubus import EventBus

from xp.models.protocol.conbus_protocol import (
    LightBulbGetOnEvent,
    LightBulbSetOnEvent,
    ReadDatapointEvent,
    SendActionEvent,
)
from xp.models.telegram.datapoint_type import DataPointType


class HomeKitLightbulbService:
    """Lightbulb service for HomeKit.

    Attributes:
        event_bus: Event bus for inter-service communication.
        logger: Logger instance.
    """

    event_bus: EventBus

    def __init__(self, event_bus: EventBus):
        """Initialize the lightbulb service.

        Args:
            event_bus: Event bus instance.
        """
        self.event_bus = event_bus
        self.logger = logging.getLogger(__name__)

        # Register event handlers
        self.event_bus.on(LightBulbGetOnEvent, self.handle_lightbulb_get_on)
        self.event_bus.on(LightBulbSetOnEvent, self.handle_lightbulb_set_on)

    def handle_lightbulb_get_on(self, event: LightBulbGetOnEvent) -> None:
        """Handle lightbulb get on event.

        Args:
            event: Lightbulb get on event.
        """
        self.logger.info(
            f"Getting lightbulb state for serial {event.serial_number}, output {event.output_number}"
        )
        self.logger.debug(f"lightbulb_get_on {event}")

        datapoint_type = DataPointType.MODULE_OUTPUT_STATE
        read_datapoint = ReadDatapointEvent(
            serial_number=event.serial_number, datapoint_type=datapoint_type
        )

        self.logger.debug(f"Dispatching ReadDatapointEvent for {event.serial_number}")
        self.event_bus.dispatch(read_datapoint)
        self.logger.debug(f"Dispatched ReadDatapointEvent for {event.serial_number}")

    def handle_lightbulb_set_on(self, event: LightBulbSetOnEvent) -> None:
        """Handle lightbulb set on event.

        Args:
            event: Lightbulb set on event.
        """
        self.logger.info(
            f"Setting lightbulb "
            f"for serial {event.serial_number}, "
            f"output {event.output_number} "
            f"to {'ON' if event.value else 'OFF'}"
        )
        self.logger.debug(f"lightbulb_set_on {event}")

        send_action = SendActionEvent(
            serial_number=event.serial_number,
            output_number=event.output_number,
            value=event.value,
            on_action=event.accessory.on_action,
            off_action=event.accessory.off_action,
        )

        self.logger.debug(f"Dispatching SendActionEvent for {event.serial_number}")
        self.event_bus.dispatch(send_action)
        self.logger.debug(f"Dispatched SendActionEvent for {event.serial_number}")
