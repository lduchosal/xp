"""Conbus protocol event models."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

from xp.models.config.conson_module_config import ConsonModuleConfig
from xp.models.homekit.homekit_config import HomekitAccessoryConfig
from xp.models.telegram.datapoint_type import DataPointType

if TYPE_CHECKING:
    from xp.services.protocol.conbus_event_protocol import ConbusEventProtocol


class ConnectionMadeEvent(BaseModel):
    """
    Event dispatched when TCP connection is established.

    Attributes:
        model_config: Pydantic model configuration.
        protocol: Reference to the ConbusEventProtocol instance.
    """

    model_config = {"arbitrary_types_allowed": True}

    protocol: ConbusEventProtocol = Field(
        description="Reference to the ConbusEventProtocol instance"
    )


class ConnectionFailedEvent(BaseModel):
    """
    Event dispatched when TCP connection fails.

    Attributes:
        reason: Failure reason.
    """

    reason: str = Field(description="Failure reason")


class SendWriteConfigEvent(BaseModel):
    """
    Event for sending write config commands.

    Attributes:
        serial_number: Serial number.
        output_number: Output number.
        datapoint_type: Datapoint type.
        value: Set brightness value.
    """

    serial_number: str = Field(description="Serial number")
    output_number: int = Field(description="Output number")
    datapoint_type: DataPointType = Field(description="Datapoint type")
    value: int = Field(description="Set brightness value")


class SendActionEvent(BaseModel):
    """
    Event for sending action commands.

    Attributes:
        serial_number: Serial number of the light bulb set.
        output_number: Output number of the light bulb set.
        value: Set light bulb On or Off (True/False).
        on_action: On action E00L00I00.
        off_action: On action E00L00I04.
    """

    serial_number: str = Field(description="Serial number of the light bulb set")
    output_number: int = Field(description="Output number of the light bulb set")
    value: bool = Field(description="Set light bulb On or Off (True/False)")
    on_action: str = Field(description="on action")
    off_action: str = Field(description="off action")


class DatapointEvent(BaseModel):
    """
    Base event for datapoint operations.

    Attributes:
        serial_number: Serial number of the light bulb set.
        datapoint_type: Datapoint type.
    """

    serial_number: str = Field(description="Serial number of the light bulb set")
    datapoint_type: DataPointType = Field(description="Datapoint type")


class OutputStateReceivedEvent(DatapointEvent):
    """
    Event when output state is received.

    Attributes:
        data_value: Data value.
    """

    data_value: str = Field(description="Data value")


class LightLevelReceivedEvent(DatapointEvent):
    """
    Event when light level is received.

    Attributes:
        data_value: Data value.
    """

    data_value: str = Field(description="Data value")


class ReadDatapointEvent(DatapointEvent):
    """
    Event to read datapoint.

    Attributes:
        refresh_cache: If True, force cache invalidation and fresh protocol query.
    """

    refresh_cache: bool = Field(
        default=False,
        description="If True, force cache invalidation and fresh protocol query",
    )


class ReadDatapointFromProtocolEvent(DatapointEvent):
    """Internal event for cache service to forward to protocol when cache misses."""

    pass


class ModuleEvent(BaseModel):
    """
    Event dispatched when light bulb set is on.

    Attributes:
        serial_number: Serial number of the light bulb set.
        output_number: Output number of the light bulb set.
        module: ConsonModuleConfig of the light bulb set.
        accessory: HomekitAccessoryConfig of the light bulb set.
    """

    serial_number: str = Field(description="Serial number of the light bulb set")
    output_number: int = Field(description="Output number of the light bulb set")
    module: ConsonModuleConfig = Field(
        description="ConsonModuleConfig of the light bulb set"
    )
    accessory: HomekitAccessoryConfig = Field(
        description="HomekitAccessoryConfig of the light bulb set"
    )


class LightBulbSetOnEvent(ModuleEvent):
    """
    Event dispatched when light bulb set is on.

    Attributes:
        value: On or Off the light bulb set.
    """

    value: bool = Field(description="On or Off the light bulb set")


class LightBulbGetOnEvent(ModuleEvent):
    """Event dispatched when getting light bulb on state."""

    pass


class OutletSetOnEvent(ModuleEvent):
    """
    Event dispatched when outlet set is on.

    Attributes:
        value: On or Off the light bulb set.
    """

    value: bool = Field(description="On or Off the light bulb set")


class OutletGetOnEvent(ModuleEvent):
    """Event dispatched when getting outlet on state."""

    pass


class OutletGetInUseEvent(ModuleEvent):
    """Event dispatched when getting outlet in-use state."""

    pass


class OutletSetInUseEvent(ModuleEvent):
    """
    Event dispatched when outlet set is on.

    Attributes:
        value: On or Off the light bulb set.
    """

    value: bool = Field(description="On or Off the light bulb set")


class DimmingLightSetOnEvent(ModuleEvent):
    """
    Event dispatched when dimming light set is on.

    Attributes:
        value: On or Off the light bulb set.
        brightness: Brightness of the light bulb set.
    """

    value: bool = Field(description="On or Off the light bulb set")
    brightness: int = Field(description="Brightness of the light bulb set")


class DimmingLightGetOnEvent(ModuleEvent):
    """Event dispatched when getting dimming light on state."""

    pass


class DimmingLightSetBrightnessEvent(ModuleEvent):
    """
    Event dispatched when dimming light set is on.

    Attributes:
        brightness: Level of brightness of the dimming light.
    """

    brightness: int = Field(description="Level of brightness of the dimming light")


class DimmingLightGetBrightnessEvent(ModuleEvent):
    """Event dispatched when getting dimming light brightness."""

    pass


class ConnectionLostEvent(BaseModel):
    """
    Event dispatched when TCP connection is lost.

    Attributes:
        reason: Disconnection reason.
    """

    reason: str = Field(description="Disconnection reason")


class TelegramEvent(BaseModel):
    """
    Event for telegram operations.

    Attributes:
        model_config: Pydantic model configuration.
        protocol: ConbusEventProtocol instance.
        frame: Frame <S0123450001F02D12FK>.
        telegram: Telegram S0123450001F02D12FK.
        payload: Payload S0123450001F02D12.
        telegram_type: Telegram type S.
        serial_number: Serial number 0123450001 or empty.
        checksum: Checksum FK.
        checksum_valid: Checksum valid true or false.
    """

    model_config = {"arbitrary_types_allowed": True}

    protocol: ConbusEventProtocol = Field(description="ConbusEventProtocol instance")
    frame: str = Field(description="Frame <S0123450001F02D12FK>")
    telegram: str = Field(description="Telegram: S0123450001F02D12FK")
    payload: str = Field(description="Payload: S0123450001F02D12")
    telegram_type: str = Field(description="Telegram type: S")
    serial_number: str = Field(description="Serial number: 0123450001 or empty")
    checksum: str = Field(description="Checksum: FK")
    checksum_valid: bool = Field(
        default=True, description="Checksum valid: true, or false"
    )


class ModuleStateChangedEvent(BaseModel):
    """
    Event dispatched when a module's state changes (from event telegram).

    Attributes:
        module_type_code: Module type code from event telegram.
        link_number: Link number from event telegram.
        input_number: Input number that triggered the event.
        telegram_event_type: Event type (M=press, B=release).
    """

    module_type_code: int = Field(description="Module type code from event telegram")
    link_number: int = Field(description="Link number from event telegram")
    input_number: int = Field(description="Input number that triggered the event")
    telegram_event_type: str = Field(description="Event type (M=press, B=release)")


class EventTelegramReceivedEvent(TelegramEvent):
    """Event telegram received."""

    pass


class ModuleDiscoveredEvent(TelegramEvent):
    """Event dispatched when module is discovered."""

    pass


class TelegramReceivedEvent(TelegramEvent):
    """Event dispatched when a telegram frame is received."""

    pass


class InvalidTelegramReceivedEvent(BaseModel):
    """
    Event dispatched when an invalid telegram frame is received.

    Attributes:
        model_config: Pydantic model configuration.
        protocol: ConbusEventProtocol instance.
        frame: Frame <S0123450001F02D12FK>.
        error: Error with the received telegram.
    """

    model_config = {"arbitrary_types_allowed": True}

    protocol: ConbusEventProtocol = Field(description="ConbusEventProtocol instance")
    frame: str = Field(description="Frame <S0123450001F02D12FK>")
    error: str = Field(description="Error with the received telegram")
