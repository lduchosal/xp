"""Input action types for XP24 module based on Feature-Action-Table.md"""

from enum import IntEnum


class InputActionType(IntEnum):
    """Input action types for XP24 module (based on Feature-Action-Table.md)"""

    VOID = 0
    TURNON = 1
    TURNOFF = 2
    TOGGLE = 3
    BLOCK = 4
    AUXRELAY = 5
    MUTUALEX = 6
    LEVELUP = 7
    LEVELDOWN = 8
    LEVELINC = 9
    LEVELDEC = 10
    LEVELSET = 11
    FADETIME = 12
    SCENESET = 13
    SCENENEXT = 14
    SCENEPREV = 15
    CTRLMETHOD = 16
    RETURNDATA = 17
    DELAYEDON = 18
    EVENTTIMER1 = 19
    EVENTTIMER2 = 20
    EVENTTIMER3 = 21
    EVENTTIMER4 = 22
    STEPCTRL = 23
    STEPCTRLUP = 24
    STEPCTRLDOWN = 25
    LEVELSETINTERN = 29
    FADE = 30
    LEARN = 31
