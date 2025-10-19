"""Time parameter enumeration for telegram actions."""

from enum import IntEnum


class TimeParam(IntEnum):
    """Time parameter values for action timing.

    Attributes:
        NONE: No time parameter.
        T05SEC: 0.5 second delay.
        T1SEC: 1 second delay.
        T2SEC: 2 second delay.
        T5SEC: 5 second delay.
        T10SEC: 10 second delay.
        T15SEC: 15 second delay.
        T20SEC: 20 second delay.
        T30SEC: 30 second delay.
        T45SEC: 45 second delay.
        T1MIN: 1 minute delay.
        T2MIN: 2 minute delay.
        T5MIN: 5 minute delay.
        T10MIN: 10 minute delay.
        T15MIN: 15 minute delay.
        T20MIN: 20 minute delay.
        T30MIN: 30 minute delay.
        T45MIN: 45 minute delay.
        T60MIN: 60 minute delay.
        T120MIN: 120 minute delay.
    """

    NONE = 0
    T05SEC = 1
    T1SEC = 2
    T2SEC = 3
    T5SEC = 4
    T10SEC = 5
    T15SEC = 6
    T20SEC = 7
    T30SEC = 8
    T45SEC = 9
    T1MIN = 10
    T2MIN = 11
    T5MIN = 12
    T10MIN = 13
    T15MIN = 14
    T20MIN = 15
    T30MIN = 16
    T45MIN = 17
    T60MIN = 18
    T120MIN = 19
