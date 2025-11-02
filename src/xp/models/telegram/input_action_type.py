"""Input action types for XP24 module based on Feature-Action-Table.md."""

from enum import Enum


class InputActionType(Enum):
    """Input action types for XP24 module (based on Feature-Action-Table.md).

    Attributes:
        VOID: No action.
        ON: Turn on action.
        OFF: Turn off action.
        TOGGLE: Toggle action.
        BLOCK: Block action.
        AUXRELAY: Auxiliary relay action.
        MUTUALEX: Mutual exclusion action.
        LEVELUP: Level up action.
        LEVELDOWN: Level down action.
        LEVELINC: Level increment action.
        LEVELDEC: Level decrement action.
        LEVELSET: Level set action.
        FADETIME: Fade time action.
        SCENESET: Scene set action.
        SCENENEXT: Scene next action.
        SCENEPREV: Scene previous action.
        CTRLMETHOD: Control method action.
        RETURNDATA: Return data action.
        DELAYEDON: Delayed on action.
        EVENTTIMER1: Event timer 1 action.
        EVENTTIMER2: Event timer 2 action.
        EVENTTIMER3: Event timer 3 action.
        EVENTTIMER4: Event timer 4 action.
        STEPCTRL: Step control action.
        STEPCTRLUP: Step control up action.
        STEPCTRLDOWN: Step control down action.
        LEVELSETINTERN: Level set internal action.
        FADE: Fade action.
        LEARN: Learn action.
    """

    VOID = 0
    ON = 1
    OFF = 2
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
