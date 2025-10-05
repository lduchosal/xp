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


    async def handle_outlet_get_on(self, event: OutletGetOnEvent) -> bool:
        self.logger.info(f"Getting outlet state for serial {event.serial_number}, output {event.output_number}")
        self.logger.debug(f"outlet_get_on {event}")

        datapoint_type = DataPointType.MODULE_OUTPUT_STATE
        read_datapoint = ReadDatapointEvent(
            serial_number=event.serial_number,
            datapoint_type=datapoint_type
        )

        self.logger.debug(f"Dispatching ReadDatapointEvent for {event.serial_number}")
        received_event = await self.event_bus.dispatch(read_datapoint)

        is_our_response = lambda response_event: (
                response_event.serial_number == read_datapoint.serial_number
                and response_event.datapoint_type == datapoint_type
        )

        self.logger.debug(f"Waiting for DatapointReceivedEvent (timeout: 2s)")
        try:
            response_event: DatapointReceivedEvent = await self.event_bus.expect(
                DatapointReceivedEvent,
                include=lambda e: is_our_response(e),
                timeout=2,  # raises asyncio.TimeoutError if no match is seen within 2sec
            )
            state = response_event.data_value[event.output_number] == "1"
            self.logger.info(f"Outlet state for {event.serial_number} output {event.output_number}: {'ON' if state else 'OFF'}")
            return state
        except Exception as e:
            self.logger.error(f"Error getting outlet state: {e}", exc_info=True)
            raise

    async def handle_outlet_set_on(self, event: OutletSetOnEvent) -> None:
        self.logger.info(f"Setting outlet for serial {event.serial_number}, output {event.output_number} to {'ON' if event.value else 'OFF'}")
        self.logger.debug(f"outlet_set_on {event}")

        send_action = SendActionEvent(
            serial_number=event.serial_number,
            output_number=event.output_number,
            value=event.value
        )

        self.logger.debug(f"Dispatching SendActionEvent for {event.serial_number}")
        try:
            await self.event_bus.dispatch(send_action)
            self.logger.info(f"Outlet set command sent successfully for {event.serial_number}")
        except Exception as e:
            self.logger.error(f"Error setting outlet state: {e}", exc_info=True)
            raise

    async def handle_outlet_get_in_use(self, event: OutletGetInUseEvent) -> bool:
        self.logger.info(f"Getting outlet in-use status for serial {event.serial_number}")
        self.logger.debug(f"outlet_get_in_use {event}")

        datapoint_type = DataPointType.MODULE_STATE
        read_datapoint = ReadDatapointEvent(
            serial_number=event.serial_number,
            datapoint_type=datapoint_type
        )

        self.logger.debug(f"Dispatching ReadDatapointEvent for {event.serial_number}")
        received_event = await self.event_bus.dispatch(read_datapoint)

        is_our_response = lambda response_event: (
                response_event.serial_number == read_datapoint.serial_number
                and response_event.datapoint_type == datapoint_type
        )

        self.logger.debug(f"Waiting for DatapointReceivedEvent (timeout: 2s)")
        try:
            response_event: DatapointReceivedEvent = await self.event_bus.expect(
                DatapointReceivedEvent,
                include=lambda e: is_our_response(e),
                timeout=2,  # raises asyncio.TimeoutError if no match is seen within 2sec
            )
            in_use = response_event.data_value == "ON"
            self.logger.info(f"Outlet in-use status for {event.serial_number}: {in_use}")
            return in_use
        except Exception as e:
            self.logger.error(f"Error getting outlet in-use status: {e}", exc_info=True)
            raise
