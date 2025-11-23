"""XP24 Action Table models for input actions and settings."""

from typing import ClassVar, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator

from xp.models.telegram.input_action_type import InputActionType
from xp.models.telegram.timeparam_type import TimeParam


class InputAction(BaseModel):
    """Represents an input action with type and parameter.

    Attributes:
        model_config: Pydantic configuration to preserve enum objects.
        type: The input action type.
        param: Time parameter for the action.
    """

    model_config = ConfigDict(use_enum_values=False)

    type: InputActionType = InputActionType.TOGGLE
    param: TimeParam = TimeParam.NONE

    @field_validator("type", mode="before")
    @classmethod
    def validate_action_type(
        cls, v: Union[str, int, InputActionType]
    ) -> InputActionType:
        """Convert string or int to InputActionType enum.

        Args:
            v: Input value (can be string name, int value, or enum).

        Returns:
            InputActionType enum value.

        Raises:
            ValueError: If the value cannot be converted to InputActionType.
        """
        if isinstance(v, InputActionType):
            return v
        if isinstance(v, str):
            try:
                return InputActionType[v]
            except KeyError:
                raise ValueError(f"Invalid InputActionType: {v}")
        if isinstance(v, int):
            try:
                return InputActionType(v)
            except ValueError:
                raise ValueError(f"Invalid InputActionType value: {v}")
        raise ValueError(f"Invalid type for InputActionType: {type(v)}")

    @field_validator("param", mode="before")
    @classmethod
    def validate_time_param(cls, v: Union[str, int, TimeParam]) -> TimeParam:
        """Convert string or int to TimeParam enum.

        Args:
            v: Input value (can be string name, int value, or enum).

        Returns:
            TimeParam enum value.

        Raises:
            ValueError: If the value cannot be converted to TimeParam.
        """
        if isinstance(v, TimeParam):
            return v
        if isinstance(v, str):
            try:
                return TimeParam[v]
            except KeyError:
                raise ValueError(f"Invalid TimeParam: {v}")
        if isinstance(v, int):
            try:
                return TimeParam(v)
            except ValueError:
                raise ValueError(f"Invalid TimeParam value: {v}")
        raise ValueError(f"Invalid type for TimeParam: {type(v)}")


class Xp24MsActionTable(BaseModel):
    """XP24 Action Table for managing input actions and settings.

    Each input has an action type (TOGGLE, ON, LEVELSET, etc.)
    with an optional parameter string.

    Attributes:
        MS300: Timing constant for 300ms.
        MS500: Timing constant for 500ms.
        input1_action: Action configuration for input 1.
        input2_action: Action configuration for input 2.
        input3_action: Action configuration for input 3.
        input4_action: Action configuration for input 4.
        mutex12: Mutual exclusion between inputs 1-2.
        mutex34: Mutual exclusion between inputs 3-4.
        curtain12: Curtain setting for inputs 1-2.
        curtain34: Curtain setting for inputs 3-4.
        mutual_deadtime: Master timing (MS300=12 or MS500=20).
    """

    # MS timing constants
    MS300: ClassVar[int] = 12
    MS500: ClassVar[int] = 20

    # Input actions for each input (default to TOGGLE with None parameter)
    input1_action: InputAction = Field(default_factory=InputAction)
    input2_action: InputAction = Field(default_factory=InputAction)
    input3_action: InputAction = Field(default_factory=InputAction)
    input4_action: InputAction = Field(default_factory=InputAction)

    # Boolean settings
    mutex12: bool = False  # Mutual exclusion between inputs 1-2
    mutex34: bool = False  # Mutual exclusion between inputs 3-4
    curtain12: bool = False  # Curtain setting for inputs 1-2
    curtain34: bool = False  # Curtain setting for inputs 3-4
    mutual_deadtime: int = MS300  # Master timing (MS300=12 or MS500=20)
