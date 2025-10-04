import logging

from bubus import EventBus

from xp.models.protocol.conbus_protocol import (
    OutletGetOnEvent,
    ReadDatapointEvent,
    DatapointReceivedEvent,
    OutletSetOnEvent,
    SendActionEvent,
    OutletGetInUseEvent
)
from xp.models.telegram.datapoint_type import DataPointType

class HomeKitOutletService:
    """ Outlet service for HomeKit """
    event_bus: EventBus

    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.logger = logging.getLogger(__name__)

        # Register event handlers
        self.event_bus.on(OutletGetOnEvent, self.handle_outlet_get_on)
        self.event_bus.on(OutletSetOnEvent, self.handle_outlet_set_on)
        self.event_bus.on(OutletGetInUseEvent, self.handle_outlet_get_in_use)


    def handle_outlet_get_on(self, event: OutletGetOnEvent) -> bool:
        self.logger.debug(f"outlet_get_on {event}")
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

    def handle_outlet_set_on(self, event: OutletSetOnEvent) -> None:
        self.logger.debug(f"outlet_set_on {event}")
        send_action = SendActionEvent(
            serial_number=event.serial_number,
            output_number=event.output_number,
            value=event.value
        )
        self.event_bus.dispatch(send_action)

    def handle_outlet_get_in_use(self, event: OutletGetInUseEvent) -> bool:
        self.logger.debug(f"outlet_get_in_use {event}")
        datapoint_type = DataPointType.MODULE_STATE
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
        return response_event.data_value == "ON"
