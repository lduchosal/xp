"""System function enumeration for system telegrams."""

from enum import Enum
from typing import Optional


class SystemFunction(str, Enum):
    """System function codes for system telegrams.

    Attributes:
        NONE: Undefined function.
        DISCOVERY: Discover function.
        READ_DATAPOINT: Read datapoint.
        READ_CONFIG: Read configuration.
        WRITE_CONFIG: Write configuration.
        BLINK: Blink LED function.
        UNBLINK: Unblink LED function.
        UPLOAD_FIRMWARE_START: Start upload firmware.
        UPLOAD_FIRMWARE_STOP: Stop upload firmware.
        UPLOAD_FIRMWARE: Upload firmware.
        UPLOAD_ACTIONTABLE: Upload ActionTable to module.
        DOWNLOAD_ACTIONTABLE: Download ActionTable.
        UPLOAD_MSACTIONTABLE: Upload module specific action table to module.
        DOWNLOAD_MSACTIONTABLE: Download module specific action table.
        TELEGRAM_WRITE_START: Start writing telegram.
        TELEGRAM_READ_START: Start reading telegram.
        EOF: End of msactiontable response.
        TELEGRAM: Module specific telegram response.
        MSACTIONTABLE: Module specific action table response.
        ACTIONTABLE: Module specific action table response.
        ACK: Acknowledge response.
        NAK: Not acknowledge response.
        UPLOAD_TOP_FIRMWARE_START: Start upload firmware (TOP).
        UPLOAD_TOP_FIRMWARE_STOP: Stop upload firmware (TOP).
        UPLOAD_TOP_FIRMWARE: Upload firmware (TOP).
        ROTATE_ENABLE: Enable rotate.
        ROTATE_DISABLE: Disable rotate.
        UNKNOWN_26: Used after discover, unknown purpose.
        ACTION: Action function.
    """

    NONE = "00"  # F00D Undefined
    DISCOVERY = "01"  # F01D Discover function
    READ_DATAPOINT = "02"  # F02D Read datapoint
    READ_CONFIG = "03"  # F03D Read configuration
    WRITE_CONFIG = "04"  # F04D Write configuration
    BLINK = "05"  # F05D Blink LED function
    UNBLINK = "06"  # F06D Unblink LED function

    UPLOAD_FIRMWARE_START = "07"  # F07D Start Upload firmware
    UPLOAD_FIRMWARE_STOP = "08"  # F08D Stop Upload firmware
    UPLOAD_FIRMWARE = "09"  # F09D Upload firmware

    UPLOAD_ACTIONTABLE = "10"  # F10D Upload ActionTable
    DOWNLOAD_ACTIONTABLE = "11"  # F11D Download ActionTable
    UPLOAD_MSACTIONTABLE = "12"  # F12D Upload MsActionTable to module
    DOWNLOAD_MSACTIONTABLE = "13"  # F13D Download MsActionTable

    TELEGRAM_WRITE_START = "14"  # F14D Start writing telegram
    TELEGRAM_READ_START = "15"  # F15D Start reading telegram
    EOF = "16"  # F16D End of msactiontable response
    TELEGRAM = "17"  # F17D module specific Telegram response
    MSACTIONTABLE = "17"  # F17D module specific ms action table (Telegram) response
    ACTIONTABLE = "17"  # F17D module specific action table (Telegram) response
    ACK = "18"  # F18D Acknowledge / continue response
    NAK = "19"  # F19D Not acknowledge response

    UPLOAD_TOP_FIRMWARE_START = "20"  # F20D Start Upload firmware (TOP)
    UPLOAD_TOP_FIRMWARE_STOP = "21"  # F21D Stop Upload firmware (TOP)
    UPLOAD_TOP_FIRMWARE = "22"  # F22D Upload firmware (TOP)

    ROTATE_ENABLE = "23"  # F23D Enable rotate
    ROTATE_DISABLE = "24"  # F24D Disable rotate

    UNKNOWN_26 = "26"  # F26D Used after discover, but don't know what it is
    ACTION = "27"  # F27D Action function

    def get_description(self) -> str:
        """Get the description of the SystemFunction.

        Returns:
            Human-readable description of the function.
        """
        return (
            {
                self.DISCOVERY: "Discover function",
                self.READ_DATAPOINT: "Read datapoint",
                self.READ_CONFIG: "Read configuration",
                self.WRITE_CONFIG: "Write configuration",
                self.BLINK: "Blink LED function",
                self.DOWNLOAD_MSACTIONTABLE: "Download the msactiontable",
                self.DOWNLOAD_ACTIONTABLE: "Download ActionTable",
                self.EOF: "End of msactiontable response",
                self.ACTIONTABLE: "Actiontable response",
                self.MSACTIONTABLE: "Msactiontable response",
                self.UNBLINK: "Unblink LED function",
                self.ACK: "Acknowledge response",
                self.NAK: "Not acknowledge response",
                self.ACTION: "Action function",
            }
        ).get(self, "Unknown function")

    @classmethod
    def from_code(cls, code: str) -> Optional["SystemFunction"]:
        """Get SystemFunction from code string.

        Args:
            code: Function code string.

        Returns:
            SystemFunction instance if found, None otherwise.
        """
        for func in cls:
            if func.value.lower() == code.lower():
                return func
        return None
