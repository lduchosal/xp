"""HomeKit Outlet Service.

This module provides service implementation for outlet accessories.
"""

import logging

from bubus import EventBus

from xp.models.protocol.conbus_protocol import (
    OutletGetInUseEvent,
    OutletGetOnEvent,
    OutletSetOnEvent,
    ReadDatapointEvent,
    SendActionEvent,
)
from xp.models.telegram.datapoint_type import DataPointType


class HomeKitOutletService:
    """Outlet service for HomeKit.

    Attributes:
        event_bus: Event bus for inter-service communication.
        logger: Logger instance.
    """

    event_bus: EventBus

    def __init__(self, event_bus: EventBus):
        """Initialize the outlet service.

        Args:
            event_bus: Event bus instance.
        """
        self.event_bus = event_bus
        self.logger = logging.getLogger(__name__)

        # Register event handlers
        self.event_bus.on(OutletGetOnEvent, self.handle_outlet_get_on)
        self.event_bus.on(OutletSetOnEvent, self.handle_outlet_set_on)
        self.event_bus.on(OutletGetInUseEvent, self.handle_outlet_get_in_use)

    def handle_outlet_get_on(self, event: OutletGetOnEvent) -> bool:
        """Handle outlet get on event.

        Args:
            event: Outlet get on event.

        Returns:
            True if request was dispatched successfully.
        """
        self.logger.debug(
            f"Getting outlet state for serial {event.serial_number}, output {event.output_number}"
        )

        datapoint_type = DataPointType.MODULE_OUTPUT_STATE
        read_datapoint = ReadDatapointEvent(
            serial_number=event.serial_number, datapoint_type=datapoint_type
        )

        self.logger.debug(f"Dispatching ReadDatapointEvent for {event.serial_number}")
        self.event_bus.dispatch(read_datapoint)
        self.logger.debug(f"Dispatched ReadDatapointEvent for {event.serial_number}")
        return True

    def handle_outlet_set_on(self, event: OutletSetOnEvent) -> bool:
        """Handle outlet set on event.

        Args:
            event: Outlet set on event.

        Returns:
            True if command was sent successfully.
        """
        self.logger.info(
            f"Setting outlet "
            f"for serial {event.serial_number}, "
            f"output {event.output_number} "
            f"to {'ON' if event.value else 'OFF'}"
        )
        self.logger.debug(f"outlet_set_on {event}")

        send_action = SendActionEvent(
            serial_number=event.serial_number,
            output_number=event.output_number,
            value=event.value,
            on_action=event.accessory.on_action,
            off_action=event.accessory.off_action,
        )

        self.logger.debug(f"Dispatching SendActionEvent for {event.serial_number}")
        self.event_bus.dispatch(send_action)
        self.logger.info(
            f"Outlet set command sent successfully for {event.serial_number}"
        )
        return True

    def handle_outlet_get_in_use(self, event: OutletGetInUseEvent) -> bool:
        """Handle outlet get in-use event.

        Args:
            event: Outlet get in-use event.

        Returns:
            True if request was dispatched successfully.
        """
        self.logger.info(
            f"Getting outlet in-use status for serial {event.serial_number}"
        )
        self.logger.debug(f"outlet_get_in_use {event}")

        datapoint_type = DataPointType.MODULE_STATE
        read_datapoint = ReadDatapointEvent(
            serial_number=event.serial_number, datapoint_type=datapoint_type
        )

        self.logger.debug(f"Dispatching ReadDatapointEvent for {event.serial_number}")
        self.event_bus.dispatch(read_datapoint)
        self.logger.debug("Dispatching ReadDatapointEvent (timeout: 2s)")
        return True
