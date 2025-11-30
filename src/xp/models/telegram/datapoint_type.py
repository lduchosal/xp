"""Datapoint type enumeration for system telegrams."""

from enum import Enum
from typing import Optional


class DataPointType(str, Enum):
    """
    Data point types for system telegrams.

    Attributes:
        MODULE_TYPE: Module type (XP24, XP33, etc).
        HW_VERSION: Hardware version information.
        SW_VERSION: Software version information.
        SERIAL_NUMBER: Serial number.
        LINK_NUMBER: Link number.
        MODULE_NUMBER: Module number.
        SYSTEM_TYPE: System type.
        MODULE_TYPE_CODE: Module type code.
        MODULE_TYPE_ID: Module type ID.
        MODULE_STATE: Module state.
        MODULE_ERROR_CODE: Status query data point.
        MODULE_INPUT_STATE: Module input state.
        MODULE_OUTPUT_STATE: Channel states (XP33).
        MODULE_FW_CRC: Module firmware CRC.
        MODULE_ACTION_TABLE_CRC: Module action table CRC.
        MODULE_LIGHT_LEVEL: Module light level.
        MODULE_OPERATING_HOURS: Module operating hours.
        MODULE_ENERGY_LEVEL: Current data point.
        TEMPERATURE: Temperature data point.
        SW_TOP_VERSION: Software top version.
        VOLTAGE: Voltage data point.
        AUTO_REPORT_STATUS: Auto report status.

    Sample telegram datapoint request:
       <S0020044966F02D30FL>

    Sample telegram datapoint reply:
       <R0020044966F02D00XP24FH>
       <R0020044966F02D01XP24FG>
       <R0020044966F02D02XP24_V0.34.03GI>
       <R0020044966F02D030020044966FB>
       <R0020044966F02D0406FL>
       <R0020044966F02D050007FL>
       <R0020044966F02D0601FO>
       <R0020044966F02D0707FJ>
       <R0020044966F02D08MIFF>
       <R0020044966F02D09OFFBP>
       <R0020044966F02D1000FI>
       <R0020044966F02D11xxxx0000FJ>
       <R0020044966F02D12xxxx0000FK>
       <R0020044966F02D1500:000[%],01:000[%],02:000[%],03:000[%]HB>
       <R0020044966F02D1600:000[H],01:000[H],02:000[H],03:000[H]HC>
       <R0020044966F02D1700:00000[NA],01:00000[NA],02:00000[NA],03:00000[NA]HD>
       <R0020044966F02D18+28,5§CIM>
       <R0020044966F02D19??FB>
       <R0020044966F02D20??FL>
       <R0020044966F02D21PPFK>
       <R0020044966F02D22PLLKMDINEM>
       <R0020044966F02D23AAFI>
       <R0020044966F02D24AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAFP>
       <R0020044966F02D25AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAFO>
       <R0020044966F02D26??FN>
    """

    MODULE_TYPE = "00"  # Module type (XP24, XP33, ..)
    HW_VERSION = "01"  # Hardware version information
    SW_VERSION = "02"  # Software version information
    SERIAL_NUMBER = "03"  # Serial number
    LINK_NUMBER = "04"  # Link number
    MODULE_NUMBER = "05"  # Module number
    SYSTEM_TYPE = "06"  # System type
    MODULE_TYPE_CODE = "07"  # Module type code
    MODULE_TYPE_ID = "08"  # Module type id
    MODULE_STATE = "09"  # Module state
    MODULE_ERROR_CODE = "10"  # Status query data point
    MODULE_INPUT_STATE = "11"  # Module input state
    MODULE_OUTPUT_STATE = "12"  # Channel states (XP33)
    MODULE_FW_CRC = "13"  # Module Firmware CRC
    MODULE_ACTION_TABLE_CRC = "14"  # Module Action Table CRC

    # XP24 00:000[%],01:000[%],02:000[%],03:000[%]
    # XP33 00:000[%],01:000[%],02:000[%]
    MODULE_LIGHT_LEVEL = "15"  # Module Light Level

    # XP24 00:000[H],01:000[H],02:000[H],03:000[H]
    MODULE_OPERATING_HOURS = "16"  # Module Operating Hours

    # XP24 00:00000[NA],01:00000[NA],02:00000[NA],03:00000[NA]
    MODULE_ENERGY_LEVEL = "17"  # Current data point

    # XP24 +34,0C
    # XP33 -20,0C
    TEMPERATURE = "18"  # Temperature data point

    SW_TOP_VERSION = "19"  # Software Top Version
    VOLTAGE = "20"  # VOLTAGE data point
    AUTO_REPORT_STATUS = "21"  # Auto Report Status

    @classmethod
    def from_code(cls, code: str) -> Optional["DataPointType"]:
        """
        Get DataPointType from code string.

        Args:
            code: Datapoint type code string.

        Returns:
            DataPointType instance if found, None otherwise.
        """
        for dp_type in cls:
            if dp_type.value == code:
                return dp_type
        return None
