"""XP20 Action Table models for input actions and settings."""

from dataclasses import dataclass, field

from xp.models import ModuleTypeCode
from xp.models.input_action_type import InputActionType
from xp.models.timeparam_type import TimeParam


# CP20 0 0 > 1 OFF;
# CP20 0 0 > 1 ~ON;
@dataclass
class ActionTableEntry:
    module_type: ModuleTypeCode = ModuleTypeCode.CP20
    link_number: int = 0
    module_input: int = 0
    module_output: int = 1
    command: InputActionType = InputActionType.TURNOFF
    parameter: TimeParam = TimeParam.NONE
    inverted: bool = False


@dataclass
class ActionTable:
    """Action Table for managing action on events."""

    entries: list[ActionTableEntry] = field(default_factory=list)
