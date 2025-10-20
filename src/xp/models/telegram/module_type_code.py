"""Module type code enumeration for XP system modules."""

from enum import Enum
from typing import Dict


class ModuleTypeCode(Enum):
    """Enum representing all XP system module type codes.

    Attributes:
        NOMOD: No module (code 0).
        ALLMOD: Matches every module type (code 1).
        CP20: CP switch link module (code 2).
        CP70A: CP 38kHz IR link module (code 3).
        CP70B: CP B&O IR link module (code 4).
        CP70C: CP UHF link module (code 5).
        CP70D: CP timer link module (code 6).
        XP24: XP relay module (code 7).
        XP31UNI: XP universal load light dimmer (code 8).
        XP31BCU: XP ballast controller 0-10V (code 9).
        XP31DD: XP ballast controller DSI/DALI (code 10).
        XP33: XP 3-channel light dimmer (code 11).
        CP485: CP RS485 interface module (code 12).
        XP130: Ethernet/TCP/IP interface module (code 13).
        XP2606: 5-way push button panel with sesam (code 14).
        XP2606A: 5-way push button with IR receiver (code 15).
        XP2606B: 5-way push button with B&O IR (code 16).
        XP26X1: Reserved (code 17).
        XP26X2: Reserved (code 18).
        XP2506: 5-way push button panel with sesam Conson design (code 19).
        XP2506A: 5-way push button panel with sesam and 38kHz IR Conson design (code 20).
        XP2506B: 5-way push button panel with sesam and B&O IR Conson design (code 21).
        XPX1_8: 8-way push button panel interface (code 22).
        XP134: Junctionbox interlink (code 23).
        XP24P: XP24P module (code 24).
        XP28A: XP28A module (code 25).
        XP28B: XP28B module (code 26).
        CONTOOL: CONTOOL module (code 27).
        XP28: XP28 module (code 28).
        XP31LR: XP 1-channel lightdimmer (code 29).
        XP33LR: XP 33 3-channel lightdimmer (code 30).
        XP31CR: XP 31 1-channel dimmer (code 31).
        XP31BC: XP 31 1-channel dimmer (code 32).
        XP20: XP switch link module (code 33).
        XP230: Ethernet/TCPIP interface module (code 34).
        XP33LED: XP 3-channel LED dimmer (code 35).
        XP31LED: XP 1-channel LED dimmer (code 36).
    """

    NOMOD = 0  # No module
    ALLMOD = 1  # Code matching every moduletype
    CP20 = 2  # CP switch link module
    CP70A = 3  # CP 38kHz IR link module
    CP70B = 4  # CP B&O IR link module
    CP70C = 5  # CP UHF link module
    CP70D = 6  # CP timer link module
    XP24 = 7  # XP relay module
    XP31UNI = 8  # XP universal load light dimmer
    XP31BCU = 9  # XP ballast controller, 0-10VActions
    XP31DD = 10  # XP ballast controller DSI/DALI
    XP33 = 11  # XP 33 3 channel lightdimmer
    CP485 = 12  # CP RS485 interface module
    XP130 = 13  # Ethernet/TCPIP interface module
    XP2606 = 14  # 5 way push button panel with sesam, L-Team design
    XP2606A = 15  # 5 way push button panel with sesam,
    # L-Team design and 38kHz IR receiver
    XP2606B = 16  # 5 way push button panel with sesam,
    # L-Team design and B&O IR receiver
    XP26X1 = 17  # Reserved
    XP26X2 = 18  # Reserved
    XP2506 = 19  # 5 way push button panel with sesam, Conson design
    XP2506A = 20  # 5 way push button panel with sesam and 38kHz IR, Conson design
    XP2506B = 21  # 5 way push button panel with sesam and B&O IR, Conson design
    XPX1_8 = 22  # 8 way push button panel interface
    XP134 = 23  # Junctionbox interlink
    XP24P = 24  # XP24P module
    XP28A = 25  #
    XP28B = 26  #
    CONTOOL = 27  #
    XP28 = 28  #
    XP31LR = 29  # XP 1 channel lightdimmer
    XP33LR = 30  # XP 33 3 channel lightdimmer
    XP31CR = 31  # XP 31 1 channel dimmer
    XP31BC = 32  # XP 31 1 channel dimmer
    XP20 = 33  # XP switch link module
    XP230 = 34  # Ethernet/TCPIP interface module
    XP33LED = 35  # XP 3 channel LED dimmer
    XP31LED = 36  # XP 1 channel LED dimmer


# Registry mapping module codes to their information
MODULE_TYPE_REGISTRY: Dict[int, Dict[str, str]] = {
    ModuleTypeCode.NOMOD.value: {"name": "NOMOD", "description": "No module"},
    ModuleTypeCode.ALLMOD.value: {
        "name": "ALLMOD",
        "description": "Code matching every moduletype",
    },
    ModuleTypeCode.CP20.value: {"name": "CP20", "description": "CP switch link module"},
    ModuleTypeCode.CP70A.value: {
        "name": "CP70A",
        "description": "CP 38kHz IR link module",
    },
    ModuleTypeCode.CP70B.value: {
        "name": "CP70B",
        "description": "CP B&O IR link module",
    },
    ModuleTypeCode.CP70C.value: {"name": "CP70C", "description": "CP UHF link module"},
    ModuleTypeCode.CP70D.value: {
        "name": "CP70D",
        "description": "CP timer link module",
    },
    ModuleTypeCode.XP24.value: {"name": "XP24", "description": "XP relay module"},
    ModuleTypeCode.XP31UNI.value: {
        "name": "XP31UNI",
        "description": "XP universal load light dimmer",
    },
    ModuleTypeCode.XP31BCU.value: {
        "name": "XP31BC",
        "description": "XP ballast controller, 0-10VActions",
    },
    ModuleTypeCode.XP31DD.value: {
        "name": "XP31DD",
        "description": "XP ballast controller DSI/DALI",
    },
    ModuleTypeCode.XP33.value: {
        "name": "XP33",
        "description": "XP 33 3 channel lightdimmer",
    },
    ModuleTypeCode.CP485.value: {
        "name": "CP485",
        "description": "CP RS485 interface module",
    },
    ModuleTypeCode.XP130.value: {
        "name": "XP130",
        "description": "Ethernet/TCPIP interface module",
    },
    ModuleTypeCode.XP2606.value: {
        "name": "XP2606",
        "description": "5 way push button panel with sesam, L-Team design",
    },
    ModuleTypeCode.XP2606A.value: {
        "name": "XP2606A",
        "description": "5 way push button panel with sesam, L-Team design and 38kHz IR receiver",
    },
    ModuleTypeCode.XP2606B.value: {
        "name": "XP2606B",
        "description": "5 way push button panel with sesam, L-Team design and B&O IR receiver",
    },
    ModuleTypeCode.XP26X1.value: {"name": "XP26X1", "description": "Reserved"},
    ModuleTypeCode.XP26X2.value: {"name": "XP26X2", "description": "Reserved"},
    ModuleTypeCode.XP2506.value: {
        "name": "XP2506",
        "description": "5 way push button panel with sesam, Conson design",
    },
    ModuleTypeCode.XP2506A.value: {
        "name": "XP2506A",
        "description": "5 way push button panel with sesam and 38kHz IR, Conson design",
    },
    ModuleTypeCode.XP2506B.value: {
        "name": "XP2506B",
        "description": "5 way push button panel with sesam and B&O IR, Conson design",
    },
    ModuleTypeCode.XPX1_8.value: {
        "name": "XPX1_8",
        "description": "8 way push button panel interface",
    },
    ModuleTypeCode.XP134.value: {
        "name": "XP134",
        "description": "Junctionbox interlink",
    },
    ModuleTypeCode.XP24P.value: {"name": "XP24P", "description": "XP24P module"},
    ModuleTypeCode.XP28A.value: {"name": "XP28A", "description": "XP28A module"},
    ModuleTypeCode.XP28B.value: {"name": "XP28B", "description": "XP28B module"},
    ModuleTypeCode.CONTOOL.value: {"name": "CONTOOL", "description": "CONTOOL module"},
    ModuleTypeCode.XP28.value: {"name": "XP28", "description": "XP28 module"},
    ModuleTypeCode.XP31LR.value: {
        "name": "XP31LR",
        "description": "XP 1 channel lightdimmer",
    },
    ModuleTypeCode.XP33LR.value: {
        "name": "XP33LR",
        "description": "XP 33 3 channel lightdimmer",
    },
    ModuleTypeCode.XP31CR.value: {
        "name": "XP31CR",
        "description": "XP 31 1 channel dimmer",
    },
    ModuleTypeCode.XP31BC.value: {
        "name": "XP31BC",
        "description": "XP 31 1 channel dimmer",
    },
    ModuleTypeCode.XP20.value: {"name": "XP20", "description": "XP switch link module"},
    ModuleTypeCode.XP230.value: {
        "name": "XP230",
        "description": "Ethernet/TCPIP interface module",
    },
    ModuleTypeCode.XP33LED.value: {
        "name": "XP33LED",
        "description": "XP 3 channel LED dimmer",
    },
    ModuleTypeCode.XP31LED.value: {
        "name": "XP31LED",
        "description": "XP 1 channel LED dimmer",
    },
}
