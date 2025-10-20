"""HomeKit Dimming Light Service.

This module provides service implementation for dimming light accessories.
"""

import logging

from bubus import EventBus

from xp.models.protocol.conbus_protocol import (
    DimmingLightGetBrightnessEvent,
    DimmingLightGetOnEvent,
    DimmingLightSetBrightnessEvent,
    DimmingLightSetOnEvent,
    ReadDatapointEvent,
    SendWriteConfigEvent,
)
from xp.models.telegram.datapoint_type import DataPointType


class HomeKitDimmingLightService:
    """Dimming light service for HomeKit.

    Attributes:
        event_bus: Event bus for inter-service communication.
        logger: Logger instance.
    """

    event_bus: EventBus

    def __init__(self, event_bus: EventBus) -> None:
        """Initialize the dimming light service.

        Args:
            event_bus: Event bus instance.
        """
        self.logger = logging.getLogger(__name__)
        self.event_bus = event_bus

        # Register event handlers
        self.event_bus.on(DimmingLightGetOnEvent, self.handle_dimminglight_get_on)
        self.event_bus.on(DimmingLightSetOnEvent, self.handle_dimminglight_set_on)
        self.event_bus.on(
            DimmingLightSetBrightnessEvent, self.handle_dimminglight_set_brightness
        )
        self.event_bus.on(
            DimmingLightGetBrightnessEvent, self.handle_dimminglight_get_brightness
        )

    def handle_dimminglight_get_on(self, event: DimmingLightGetOnEvent) -> None:
        """Handle dimming light get on event.

        Args:
            event: Dimming light get on event.
        """
        self.logger.info(
            f"Getting dimming light state for serial {event.serial_number}, output {event.output_number}"
        )
        self.logger.debug(f"dimminglight_get_on {event}")

        read_datapoint = ReadDatapointEvent(
            serial_number=event.serial_number,
            datapoint_type=DataPointType.MODULE_OUTPUT_STATE,
        )
        self.logger.debug(f"Dispatching ReadDatapointEvent for {event.serial_number}")
        self.event_bus.dispatch(read_datapoint)
        self.logger.debug(f"Dispatched ReadDatapointEvent for {event.serial_number}")

    def handle_dimminglight_set_on(self, event: DimmingLightSetOnEvent) -> None:
        """Handle dimming light set on event.

        Args:
            event: Dimming light set on event.
        """
        brightness = event.brightness if event.value else 0
        self.logger.debug(
            f"Setting on light for "
            f"serial {event.serial_number}, "
            f"output {event.output_number}, "
            f"event_value: {event.value}, "
            f"state: {'ON' if event.value else 'OFF'}, "
            f"brightness: {brightness}"
        )
        self.logger.debug(f"dimminglight_set_on {event}")

        datapoint_type = DataPointType.MODULE_LIGHT_LEVEL
        send_action = SendWriteConfigEvent(
            serial_number=event.serial_number,
            output_number=event.output_number,
            datapoint_type=datapoint_type,
            value=brightness,
        )

        self.logger.debug(f"Dispatching SendWriteConfigEvent for {event.serial_number}")
        self.event_bus.dispatch(send_action)
        self.logger.debug(f"Dispatched SendWriteConfigEvent for {event.serial_number}")

    def handle_dimminglight_set_brightness(
        self, event: DimmingLightSetBrightnessEvent
    ) -> None:
        """Handle dimming light set brightness event.

        Args:
            event: Dimming light set brightness event.
        """
        self.logger.info(
            f"Setting dimming light brightness"
            f"serial {event.serial_number}, "
            f"output {event.output_number} "
            f"to {event.brightness}"
        )
        self.logger.debug(f"dimminglight_set_brightness {event}")

        datapoint_type = DataPointType.MODULE_LIGHT_LEVEL
        send_action = SendWriteConfigEvent(
            serial_number=event.serial_number,
            output_number=event.output_number,
            datapoint_type=datapoint_type,
            value=event.brightness,
        )

        self.logger.debug(f"Dispatching SendWriteConfigEvent for {event.serial_number}")
        self.event_bus.dispatch(send_action)
        self.logger.debug(f"Dispatched SendWriteConfigEvent for {event.serial_number}")

    def handle_dimminglight_get_brightness(
        self, event: DimmingLightGetBrightnessEvent
    ) -> None:
        """Handle dimming light get brightness event.

        Args:
            event: Dimming light get brightness event.
        """
        self.logger.info(
            f"Getting dimming light brightness "
            f"for serial {event.serial_number}, "
            f"output {event.output_number}"
        )
        self.logger.debug(f"dimminglight_get_brightness {event}")

        datapoint_type = DataPointType.MODULE_LIGHT_LEVEL
        read_datapoint = ReadDatapointEvent(
            serial_number=event.serial_number, datapoint_type=datapoint_type
        )

        self.logger.debug(f"Dispatching ReadDatapointEvent for {event.serial_number}")
        self.event_bus.dispatch(read_datapoint)
        self.logger.debug(f"Dispatched ReadDatapointEvent for {event.serial_number}")
