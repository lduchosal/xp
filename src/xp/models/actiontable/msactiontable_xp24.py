"""XP24 Action Table models for input actions and settings."""

from typing import Any, ClassVar, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator

from xp.models.telegram.input_action_type import InputActionType
from xp.models.telegram.timeparam_type import TimeParam


class InputAction(BaseModel):
    """
    Represents an input action with type and parameter.

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
        """
        Convert string or int to InputActionType enum.

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
        """
        Convert string or int to TimeParam enum.

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
    """
    XP24 Action Table for managing input actions and settings.

    Each input has an action type (TOGGLE, ON, LEVELSET, etc.)
    with an optional parameter string.

    Attributes:
        MS300: Timing constant for 300ms.
        MS500: Timing constant for 500ms.
        ACTION_SHORT_CODES: Mapping from InputActionType to short code strings.
        SHORT_CODE_TO_ACTION: Reverse mapping from short codes to InputActionType.
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

    # Short format mapping for InputActionType
    ACTION_SHORT_CODES: ClassVar[dict[InputActionType, str]] = {
        InputActionType.VOID: "V",
        InputActionType.ON: "ON",
        InputActionType.OFF: "OF",
        InputActionType.TOGGLE: "T",
        InputActionType.BLOCK: "BL",
        InputActionType.AUXRELAY: "AX",
        InputActionType.MUTUALEX: "MX",
        InputActionType.LEVELUP: "LU",
        InputActionType.LEVELDOWN: "LD",
        InputActionType.LEVELINC: "LI",
        InputActionType.LEVELDEC: "LC",
        InputActionType.LEVELSET: "LS",
        InputActionType.FADETIME: "FT",
        InputActionType.SCENESET: "SS",
        InputActionType.SCENENEXT: "SN",
        InputActionType.SCENEPREV: "SP",
        InputActionType.CTRLMETHOD: "CM",
        InputActionType.RETURNDATA: "RD",
        InputActionType.DELAYEDON: "DO",
        InputActionType.EVENTTIMER1: "E1",
        InputActionType.EVENTTIMER2: "E2",
        InputActionType.EVENTTIMER3: "E3",
        InputActionType.EVENTTIMER4: "E4",
        InputActionType.STEPCTRL: "SC",
        InputActionType.STEPCTRLUP: "SU",
        InputActionType.STEPCTRLDOWN: "SD",
        InputActionType.LEVELSETINTERN: "LN",
        InputActionType.FADE: "FD",
        InputActionType.LEARN: "LR",
    }

    # Reverse mapping for parsing
    SHORT_CODE_TO_ACTION: ClassVar[dict[str, InputActionType]] = {
        v: k for k, v in ACTION_SHORT_CODES.items()
    }

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

    def to_short_format(self) -> list[str]:
        """
        Convert action table to short format string.

        Returns:
            Short format string with settings (e.g., "XP24 T:1 T:2 T:0 T:0 | M12:0 M34:0 C12:0 C34:0 DT:12").
        """
        # Format input actions
        actions = [
            self.input1_action,
            self.input2_action,
            self.input3_action,
            self.input4_action,
        ]

        action_parts = []
        for action in actions:
            short_code = self.ACTION_SHORT_CODES.get(action.type, "??")
            param_value = action.param.value
            action_parts.append(f"{short_code}:{param_value}")

        result = " ".join(action_parts)

        # Add settings
        settings = (
            f"M12:{1 if self.mutex12 else 0} "
            f"M34:{1 if self.mutex34 else 0} "
            f"C12:{1 if self.curtain12 else 0} "
            f"C34:{1 if self.curtain34 else 0} "
            f"DT:{self.mutual_deadtime}"
        )
        result = f"{result} | {settings}"

        return [result]

    @classmethod
    def from_short_format(cls, short_str: list[str]) -> "Xp24MsActionTable":
        """
        Parse short format string into action table.

        Args:
            short_str: Short format string.

        Returns:
            Xp24MsActionTable instance.

        Raises:
            ValueError: If format is invalid.
        """
        # Split by pipe to separate actions from settings
        parts = short_str[0].split("|")
        action_part = parts[0].strip()
        settings_part = parts[1].strip()

        # Parse action part
        tokens = action_part.split()
        if len(tokens) != 4:
            raise ValueError(
                f"Invalid short format: expected '<a1> <a2> <a3> <a4>', got '{action_part}'"
            )

        # Parse input actions
        input_actions = []
        for i, token in enumerate(tokens[0:4], 1):
            if ":" not in token:
                raise ValueError(f"Invalid action format at position {i}: '{token}'")

            code, param_str = token.split(":", 1)

            # Look up action type
            if code not in cls.SHORT_CODE_TO_ACTION:
                raise ValueError(f"Unknown action code: '{code}'")

            action_type = cls.SHORT_CODE_TO_ACTION[code]

            # Parse param
            try:
                param_value = int(param_str)
                param_type = TimeParam(param_value)
            except (ValueError, KeyError):
                raise ValueError(f"Invalid time param: '{param_str}'")

            input_actions.append(InputAction(type=action_type, param=param_type))

        # Parse settings if present
        kwargs: dict[str, Any] = {
            "input1_action": input_actions[0],
            "input2_action": input_actions[1],
            "input3_action": input_actions[2],
            "input4_action": input_actions[3],
        }

        # Parse settings: M12:0 M34:1 C12:0 C34:1 DT:12
        for setting in settings_part.split():
            if ":" not in setting:
                continue

            key, value = setting.split(":", 1)

            if key == "M12":
                kwargs["mutex12"] = value == "1"
            elif key == "M34":
                kwargs["mutex34"] = value == "1"
            elif key == "C12":
                kwargs["curtain12"] = value == "1"
            elif key == "C34":
                kwargs["curtain34"] = value == "1"
            elif key == "DT":
                kwargs["mutual_deadtime"] = int(value)

        return cls(**kwargs)
