import logging

from bubus import EventBus

from xp.models.protocol.conbus_protocol import (
    DimmingLightGetOnEvent,
    DimmingLightSetOnEvent,
    DimmingLightSetBrightnessEvent,
    DimmingLightGetBrightnessEvent,
    SendWriteConfigEvent,
    DatapointReceivedEvent,
    ReadDatapointEvent
)
from xp.models.telegram.datapoint_type import DataPointType


class HomeKitDimmingLightService:

    """ Dimming light service for HomeKit """
    event_bus: EventBus

    def __init__(self, event_bus: EventBus) -> None:
        self.logger = logging.getLogger(__name__)
        self.event_bus = event_bus

        # Register event handlers
        self.event_bus.on(DimmingLightGetOnEvent, self.handle_dimminglight_get_on)
        self.event_bus.on(DimmingLightSetOnEvent, self.handle_dimminglight_set_on)
        self.event_bus.on(DimmingLightSetBrightnessEvent, self.handle_dimminglight_set_brightness)
        self.event_bus.on(DimmingLightGetBrightnessEvent, self.handle_dimminglight_get_brightness)


    def handle_dimminglight_get_on(self, event: DimmingLightGetOnEvent) -> bool:
        self.logger.debug(f"dimminglight_get_on {event}")
        datapoint_type = DataPointType.MODULE_OUTPUT_STATE
        read_datapoint = ReadDatapointEvent(
            serial_number=event.serial_number,
            datapoint_type=datapoint_type
        )
        self.event_bus.dispatch(read_datapoint)

        is_our_response = lambda response_event: (
                response_event.serial_number == read_datapoint.serial_number
                and response_event.datapoint_type == datapoint_type
        )
        response_event: DatapointReceivedEvent = self.event_bus.expect(
            DatapointReceivedEvent,
            include=lambda e: is_our_response(e),
            timeout=2,  # raises asyncio.TimeoutError if no match is seen within 30sec
        )
        return response_event.data_value[event.output_number] == "1"

    def handle_dimminglight_set_on(self, event: DimmingLightSetOnEvent) -> None:
        self.logger.debug(f"dimminglight_set_on {event}")
        datapoint_type = DataPointType.MODULE_LIGHT_LEVEL
        value = 0 if event.value else 60
        send_action = SendWriteConfigEvent(
            serial_number=event.serial_number,
            output_number=event.output_number,
            datapoint_type=datapoint_type,
            value=value
        )
        self.event_bus.dispatch(send_action)

    def handle_dimminglight_set_brightness(self, event: DimmingLightSetBrightnessEvent) -> None:
        self.logger.debug(f"dimminglight_set_brightness {event}")
        datapoint_type = DataPointType.MODULE_LIGHT_LEVEL
        send_action = SendWriteConfigEvent(
            serial_number=event.serial_number,
            output_number=event.output_number,
            datapoint_type=datapoint_type,
            value=event.value
        )
        self.event_bus.dispatch(send_action)


    def handle_dimminglight_get_brightness(self, event: DimmingLightGetBrightnessEvent) -> int:
        self.logger.debug(f"dimminglight_get_brightness {event}")
        datapoint_type = DataPointType.MODULE_LIGHT_LEVEL
        read_datapoint = ReadDatapointEvent(
            serial_number=event.serial_number,
            datapoint_type=datapoint_type
        )
        self.event_bus.dispatch(read_datapoint)

        is_our_response = lambda response_event: (
                response_event.serial_number == read_datapoint.serial_number
                and response_event.datapoint_type == datapoint_type
        )
        response_event: DatapointReceivedEvent = self.event_bus.expect(
            DatapointReceivedEvent,
            include=lambda e: is_our_response(e),
            timeout=2,  # raises asyncio.TimeoutError if no match is seen within 30sec
        )

        # Parse response format like "00:050,01:025,02:100"
        data_value = str(response_event.data_value)
        level = 0
        for output_data in data_value.split(","):
            if ":" in output_data:
                output_str, level_str = output_data.split(":")
                if int(output_str) == event.output_number:
                    level = int(level_str)
                    break

        return level
