from __future__ import annotations

from typing import TYPE_CHECKING

from bubus import BaseEvent
from pydantic import Field

from xp.models.homekit.homekit_config import HomekitAccessoryConfig
from xp.models.homekit.homekit_conson_config import ConsonModuleConfig
from xp.models.telegram.datapoint_type import DataPointType

if TYPE_CHECKING:
    from xp.services.protocol.telegram_protocol import TelegramProtocol


class ConnectionMadeEvent(BaseEvent):
    """Event dispatched when TCP connection is established"""

    protocol: TelegramProtocol = Field(
        description="Reference to the TelegramProtocol instance"
    )


class ConnectionFailedEvent(BaseEvent):
    """Event dispatched when TCP connection fails"""

    reason: str = Field(description="Failure reason")


class SendWriteConfigEvent(BaseEvent):
    serial_number: str = Field(description="Serial number")
    output_number: int = Field(description="Output number")
    datapoint_type: DataPointType = Field(description="Datapoint type")
    value: int = Field(description="Set brightness value")


class SendActionEvent(BaseEvent):
    serial_number: str = Field(description="Serial number of the light bulb set")
    output_number: int = Field(description="Output number of the light bulb set")
    value: bool = Field(description="Set light bulb On or Off (True/False)")


class DatapointEvent(BaseEvent):
    serial_number: str = Field(description="Serial number of the light bulb set")
    datapoint_type: DataPointType = Field(description="Datapoint type")


class OutputStateReceivedEvent(DatapointEvent):
    data_value: str = Field(description="Data value")


class LightLevelReceivedEvent(DatapointEvent):
    data_value: str = Field(description="Data value")


class ReadDatapointEvent(DatapointEvent):
    refresh_cache: bool = Field(
        default=False,
        description="If True, force cache invalidation and fresh protocol query",
    )


class ReadDatapointFromProtocolEvent(DatapointEvent):
    """Internal event for cache service to forward to protocol when cache misses"""

    pass


class ModuleEvent(BaseEvent):
    """Event dispatched when light bulb set is on"""

    serial_number: str = Field(description="Serial number of the light bulb set")
    output_number: int = Field(description="Output number of the light bulb set")
    module: ConsonModuleConfig = Field(
        description="ConsonModuleConfig of the light bulb set"
    )
    accessory: HomekitAccessoryConfig = Field(
        description="HomekitAccessoryConfig of the light bulb set"
    )


class LightBulbSetOnEvent(ModuleEvent):
    """Event dispatched when light bulb set is on"""

    value: bool = Field(description="On or Off the light bulb set")


class LightBulbGetOnEvent(ModuleEvent, BaseEvent[bool]):
    """Event dispatched when light bulb set is on"""

    pass


class OutletSetOnEvent(ModuleEvent):
    """Event dispatched when outlet set is on"""

    value: bool = Field(description="On or Off the light bulb set")


class OutletGetOnEvent(ModuleEvent):
    """Event dispatched when outlet set is on"""

    pass


class OutletGetInUseEvent(ModuleEvent):
    """Event dispatched when outlet set is on"""

    pass


class OutletSetInUseEvent(ModuleEvent, BaseEvent[bool]):
    """Event dispatched when outlet set is on"""

    value: bool = Field(description="On or Off the light bulb set")


class DimmingLightSetOnEvent(ModuleEvent):
    """Event dispatched when dimming light set is on"""

    value: bool = Field(description="On or Off the light bulb set")
    brightness: int = Field(description="Brightness of the light bulb set")


class DimmingLightGetOnEvent(ModuleEvent):
    """Event dispatched when dimming light set is on"""

    pass


class DimmingLightSetBrightnessEvent(ModuleEvent):
    """Event dispatched when dimming light set is on"""

    brightness: int = Field(description="Level of brightness of the dimming light")


class DimmingLightGetBrightnessEvent(ModuleEvent):
    """Event dispatched when dimming light set is on"""

    pass


class ConnectionLostEvent(BaseEvent):
    """Event dispatched when TCP connection is lost"""

    reason: str = Field(description="Disconnection reason")


class TelegramEvent(BaseEvent):
    protocol: TelegramProtocol = Field(description="TelegramProtocol instance")
    frame: str = Field(description="Frame <S0123450001F02D12FK>")
    telegram: str = Field(description="Telegram: S0123450001F02D12FK")
    payload: str = Field(description="Payload: S0123450001F02D12")
    telegram_type: str = Field(description="Telegram type: S")
    serial_number: str = Field(description="Serial number: 0123450001 or empty")
    checksum: str = Field(description="Checksum: FK")


class ModuleStateChangedEvent(BaseEvent):
    """Event dispatched when a module's state changes (from event telegram)"""

    module_type_code: int = Field(description="Module type code from event telegram")
    link_number: int = Field(description="Link number from event telegram")
    input_number: int = Field(description="Input number that triggered the event")
    telegram_event_type: str = Field(description="Event type (M=press, B=release)")


class EventTelegramReceivedEvent(TelegramEvent):
    """Event telegram received"""

    pass


class ModuleDiscoveredEvent(TelegramEvent):
    """Event dispatched when module is discovered"""

    pass


class TelegramReceivedEvent(TelegramEvent):
    """Event dispatched when a telegram frame is received"""

    pass


class InvalidTelegramReceivedEvent(BaseEvent):
    """Event dispatched when an invalid telegram frame is received"""

    protocol: TelegramProtocol = Field(description="TelegramProtocol instance")
    frame: str = Field(description="Frame <S0123450001F02D12FK>")
    error: str = Field(description="Error with the received telegram")
    pass
