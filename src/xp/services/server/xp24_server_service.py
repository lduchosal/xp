"""XP24 Server Service for device emulation.

This service provides XP24-specific device emulation functionality,
including response generation and device configuration handling.
"""

from typing import Dict, Optional

from xp.models import ModuleTypeCode
from xp.models.actiontable.msactiontable_xp24 import InputAction, Xp24MsActionTable
from xp.models.telegram.datapoint_type import DataPointType
from xp.models.telegram.input_action_type import InputActionType
from xp.models.telegram.system_function import SystemFunction
from xp.models.telegram.system_telegram import SystemTelegram
from xp.models.telegram.timeparam_type import TimeParam
from xp.services.actiontable.msactiontable_xp24_serializer import (
    Xp24MsActionTableSerializer,
)
from xp.services.server.base_server_service import BaseServerService


class XP24ServerError(Exception):
    """Raised when XP24 server operations fail."""

    pass


class XP24Output:
    """Represents an XP24 output state.

    Attributes:
        state: Current state of the output (True=on, False=off).
    """

    state: bool = False


class XP24ServerService(BaseServerService):
    """
    XP24 device emulation service.

    Generates XP24-specific responses, handles XP24 device configuration,
    and implements XP24 telegram format.
    """

    def __init__(
        self,
        serial_number: str,
        _variant: str = "",
        msactiontable_serializer: Optional[Xp24MsActionTableSerializer] = None,
    ):
        """Initialize XP24 server service.

        Args:
            serial_number: The device serial number.
            _variant: Reserved parameter for consistency (unused).
            msactiontable_serializer: MsActionTable serializer (injected via DI).
        """
        super().__init__(serial_number)
        self.device_type = "XP24"
        self.module_type_code = ModuleTypeCode.XP24
        self.autoreport_status = True
        self.firmware_version = "XP24_V0.34.03"
        self.output_0: XP24Output = XP24Output()
        self.output_1: XP24Output = XP24Output()
        self.output_2: XP24Output = XP24Output()
        self.output_3: XP24Output = XP24Output()

        # MsActionTable support
        self.msactiontable_serializer = (
            msactiontable_serializer or Xp24MsActionTableSerializer()
        )
        self.msactiontable = self._get_default_msactiontable()

    def _handle_device_specific_action_request(
        self, request: SystemTelegram
    ) -> Optional[str]:
        """Handle XP24-specific data requests."""
        telegrams = self._handle_action_module_output_state(request.data)
        self.logger.debug(
            f"Generated {self.device_type} module type responses: {telegrams}"
        )
        return telegrams

    def _handle_action_module_output_state(self, data_value: str) -> str:
        """Handle XP24-specific module output state."""
        output_number = int(data_value[:2])
        output_state = data_value[2:]
        if output_number not in range(0, 4):
            return self._build_ack_nak_response_telegram(False)

        if output_state not in ("AA", "AB"):
            return self._build_ack_nak_response_telegram(False)

        output = (self.output_0, self.output_1, self.output_2, self.output_3)[
            output_number
        ]
        previous_state = output.state
        output.state = True if output_state == "AB" else False
        state_changed = previous_state != output.state

        telegrams = self._build_ack_nak_response_telegram(True)
        if state_changed and self.autoreport_status:
            telegrams += self._build_make_break_response_telegram(
                output.state, output_number
            )

        return telegrams

    def _build_ack_nak_response_telegram(self, ack_or_nak: bool) -> str:
        """Build a complete ACK or NAK response telegram with checksum.

        Args:
            ack_or_nak: true: ACK telegram response, false: NAK telegram response.

        Returns:
            The complete telegram with checksum enclosed in angle brackets.
        """
        data_value = (
            SystemFunction.ACK.value if ack_or_nak else SystemFunction.NAK.value
        )
        data_part = f"R{self.serial_number}" f"F{data_value:02}D"
        return self._build_response_telegram(data_part)

    def _build_make_break_response_telegram(
        self, make_or_break: bool, output_number: int
    ) -> str:
        """Build a complete ACK or NAK response telegram with checksum.

        Args:
            make_or_break: true: MAKE event response, false: BREAK event response.
            output_number: output concerned

        Returns:
            The complete event telegram with checksum enclosed in angle brackets.
        """
        data_value = "M" if make_or_break else "B"
        data_part = (
            f"E{self.module_type_code.value:02}"
            f"L{self.link_number:02}"
            f"I{output_number:02}"
            f"{data_value}"
        )
        return self._build_response_telegram(data_part)

    def _handle_device_specific_data_request(
        self, request: SystemTelegram
    ) -> Optional[str]:
        """Handle XP24-specific data requests."""
        if not request.datapoint_type:
            return None

        datapoint_type = request.datapoint_type
        handler = {
            DataPointType.MODULE_OUTPUT_STATE: self._handle_read_module_output_state,
            DataPointType.MODULE_STATE: self._handle_read_module_state,
            DataPointType.MODULE_OPERATING_HOURS: self._handle_read_module_operating_hours,
        }.get(datapoint_type)
        if not handler:
            return None

        data_value = handler()
        data_part = (
            f"R{self.serial_number}"
            f"F02D{datapoint_type.value}"
            f"{self.module_type_code.value:02}"
            f"{data_value}"
        )
        telegram = self._build_response_telegram(data_part)

        self.logger.debug(
            f"Generated {self.device_type} module type response: {telegram}"
        )
        return telegram

    def _handle_read_module_operating_hours(self) -> str:
        """Handle XP24-specific module operating hours."""
        return "00:000[H],01:000[H],02:000[H],03:000[H]"

    def _handle_read_module_state(self) -> str:
        """Handle XP24-specific module state."""
        for output in (self.output_0, self.output_1, self.output_2, self.output_3):
            if output.state:
                return "ON"
        return "OFF"

    def _handle_read_module_output_state(self) -> str:
        """Handle XP24-specific module output state."""
        return (
            f"xxxx"
            f"{1 if self.output_0.state else 0}"
            f"{1 if self.output_1.state else 0}"
            f"{1 if self.output_2.state else 0}"
            f"{1 if self.output_3.state else 0}"
        )

    def _get_msactiontable_serializer(self) -> Optional[Xp24MsActionTableSerializer]:
        """Get the MsActionTable serializer for XP24.

        Returns:
            The XP24 MsActionTable serializer instance.
        """
        return self.msactiontable_serializer

    def _get_msactiontable(self) -> Optional[Xp24MsActionTable]:
        """Get the MsActionTable for XP24.

        Returns:
            The XP24 MsActionTable instance.
        """
        return self.msactiontable

    def _get_default_msactiontable(self) -> Xp24MsActionTable:
        """Generate default MsActionTable configuration.

        Returns:
            Default XP24 MsActionTable with all inputs set to VOID.
        """
        return Xp24MsActionTable(
            input1_action=InputAction(type=InputActionType.VOID, param=TimeParam.NONE),
            input2_action=InputAction(type=InputActionType.VOID, param=TimeParam.NONE),
            input3_action=InputAction(type=InputActionType.VOID, param=TimeParam.NONE),
            input4_action=InputAction(type=InputActionType.VOID, param=TimeParam.NONE),
            mutex12=False,
            mutex34=False,
            curtain12=False,
            curtain34=False,
            mutual_deadtime=12,  # MS300
        )

    def get_device_info(self) -> Dict:
        """Get XP24 device information.

        Returns:
            Dictionary containing device information.
        """
        return {
            "serial_number": self.serial_number,
            "device_type": self.device_type,
            "module_type_code": self.module_type_code.value,
            "firmware_version": self.firmware_version,
            "status": self.device_status,
            "link_number": self.link_number,
            "autoreport_status": self.autoreport_status,
        }
