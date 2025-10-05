import logging

from bubus import EventBus

from xp.models.protocol.conbus_protocol import (
    LightBulbGetOnEvent,
    ReadDatapointEvent,
    DatapointReceivedEvent,
    LightBulbSetOnEvent,
    SendActionEvent
)
from xp.models.telegram.datapoint_type import DataPointType

class HomeKitLightbulbService:
    """ Lightbulb service for HomeKit """
    event_bus: EventBus

    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.logger = logging.getLogger(__name__)

        # Register event handlers
        self.event_bus.on(LightBulbGetOnEvent, self.handle_lightbulb_get_on)
        self.event_bus.on(LightBulbSetOnEvent, self.handle_lightbulb_set_on)


    async def handle_lightbulb_get_on(self, event: LightBulbGetOnEvent) -> bool:
        self.logger.debug(f"lightbulb_get_on {event}")
        datapoint_type = DataPointType.MODULE_OUTPUT_STATE
        read_datapoint = ReadDatapointEvent(
            serial_number=event.serial_number,
            datapoint_type=datapoint_type
        )
        await self.event_bus.dispatch(read_datapoint)

        is_our_response = lambda response_event: (
                response_event.serial_number == read_datapoint.serial_number
                and response_event.datapoint_type == datapoint_type
        )
        response_event: DatapointReceivedEvent = await self.event_bus.expect(
            DatapointReceivedEvent,
            include=lambda e: is_our_response(e),
            timeout=2,  # raises asyncio.TimeoutError if no match is seen within 30sec
        )
        return response_event.data_value[event.output_number] == "1"

    async def handle_lightbulb_set_on(self, event: LightBulbSetOnEvent) -> None:
        self.logger.debug(f"lightbulb_set_on {event}")
        send_action = SendActionEvent(
            serial_number=event.serial_number,
            output_number=event.output_number,
            value=event.value
        )
        await self.event_bus.dispatch(send_action)

