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


    async def handle_dimminglight_get_on(self, event: DimmingLightGetOnEvent) -> bool:
        self.logger.info(f"Getting dimming light state for serial {event.serial_number}, output {event.output_number}")
        self.logger.debug(f"dimminglight_get_on {event}")

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
            self.logger.info(f"Dimming light state for {event.serial_number} output {event.output_number}: {'ON' if state else 'OFF'}")
            return state
        except Exception as e:
            self.logger.error(f"Error getting dimming light state: {e}", exc_info=True)
            raise

    async def handle_dimminglight_set_on(self, event: DimmingLightSetOnEvent) -> None:
        value = 0 if event.value else 60
        self.logger.info(f"Setting dimming light for serial {event.serial_number}, output {event.output_number} to {'ON' if event.value else 'OFF'} (brightness: {value})")
        self.logger.debug(f"dimminglight_set_on {event}")

        datapoint_type = DataPointType.MODULE_LIGHT_LEVEL
        send_action = SendWriteConfigEvent(
            serial_number=event.serial_number,
            output_number=event.output_number,
            datapoint_type=datapoint_type,
            value=value
        )

        self.logger.debug(f"Dispatching SendWriteConfigEvent for {event.serial_number}")
        try:
            await self.event_bus.dispatch(send_action)
            self.logger.info(f"Dimming light set command sent successfully for {event.serial_number}")
        except Exception as e:
            self.logger.error(f"Error setting dimming light state: {e}", exc_info=True)
            raise

    async def handle_dimminglight_set_brightness(self, event: DimmingLightSetBrightnessEvent) -> None:
        self.logger.info(f"Setting dimming light brightness for serial {event.serial_number}, output {event.output_number} to {event.value}")
        self.logger.debug(f"dimminglight_set_brightness {event}")

        datapoint_type = DataPointType.MODULE_LIGHT_LEVEL
        send_action = SendWriteConfigEvent(
            serial_number=event.serial_number,
            output_number=event.output_number,
            datapoint_type=datapoint_type,
            value=event.value
        )

        self.logger.debug(f"Dispatching SendWriteConfigEvent for {event.serial_number}")
        try:
            await self.event_bus.dispatch(send_action)
            self.logger.info(f"Dimming light brightness set successfully for {event.serial_number}")
        except Exception as e:
            self.logger.error(f"Error setting dimming light brightness: {e}", exc_info=True)
            raise


    async def handle_dimminglight_get_brightness(self, event: DimmingLightGetBrightnessEvent) -> int:
        self.logger.info(f"Getting dimming light brightness for serial {event.serial_number}, output {event.output_number}")
        self.logger.debug(f"dimminglight_get_brightness {event}")

        datapoint_type = DataPointType.MODULE_LIGHT_LEVEL
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

            # Parse response format like "00:050,01:025,02:100"
            data_value = str(response_event.data_value)
            self.logger.debug(f"Parsing brightness from response: {data_value}")
            level = 0
            for output_data in data_value.split(","):
                if ":" in output_data:
                    output_str, level_str = output_data.split(":")
                    if int(output_str) == event.output_number:
                        level = int(level_str)
                        break

            self.logger.info(f"Dimming light brightness for {event.serial_number} output {event.output_number}: {level}")
            return level
        except Exception as e:
            self.logger.error(f"Error getting dimming light brightness: {e}", exc_info=True)
            raise
