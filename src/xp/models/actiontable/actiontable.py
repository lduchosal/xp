"""XP20 Action Table models for input actions and settings."""

from dataclasses import dataclass, field

from xp.models import ModuleTypeCode
from xp.models.telegram.input_action_type import InputActionType
from xp.models.telegram.timeparam_type import TimeParam


# CP20 0 0 > 1 OFF;
# CP20 0 0 > 1 ~ON;
@dataclass
class ActionTableEntry:
    """Entry in an action table mapping input events to output actions.

    Attributes:
        module_type: Type code of the module.
        link_number: Link number for the action.
        module_input: Input number on the module.
        module_output: Output number on the module.
        command: Action type to perform.
        parameter: Time parameter for the action.
        inverted: Whether the action is inverted.
    """

    module_type: ModuleTypeCode = ModuleTypeCode.CP20
    link_number: int = 0
    module_input: int = 0
    module_output: int = 1
    command: InputActionType = InputActionType.OFF
    parameter: TimeParam = TimeParam.NONE
    inverted: bool = False


@dataclass
class ActionTable:
    """Action Table for managing action on events.

    Attributes:
        entries: List of action table entries.
    """

    entries: list[ActionTableEntry] = field(default_factory=list)
