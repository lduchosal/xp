"""XP24 Action Table models for input actions and settings."""

from dataclasses import dataclass, field

from xp.models.telegram.input_action_type import InputActionType
from xp.models.telegram.timeparam_type import TimeParam


@dataclass
class InputAction:
    """Represents an input action with type and parameter.

    Attributes:
        type: The input action type.
        param: Time parameter for the action.
    """

    type: InputActionType = InputActionType.TOGGLE
    param: TimeParam = TimeParam.NONE


@dataclass
class Xp24MsActionTable:
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
    MS300 = 12
    MS500 = 20

    # Input actions for each input (default to TOGGLE with None parameter)
    input1_action: InputAction = field(default_factory=InputAction)
    input2_action: InputAction = field(default_factory=InputAction)
    input3_action: InputAction = field(default_factory=InputAction)
    input4_action: InputAction = field(default_factory=InputAction)

    # Boolean settings
    mutex12: bool = False  # Mutual exclusion between inputs 1-2
    mutex34: bool = False  # Mutual exclusion between inputs 3-4
    curtain12: bool = False  # Curtain setting for inputs 1-2
    curtain34: bool = False  # Curtain setting for inputs 3-4
    mutual_deadtime: int = MS300  # Master timing (MS300=12 or MS500=20)
