"""Serializer for XP24 Action Table telegram encoding/decoding."""

from typing import List

from ..models.input_action_type import InputActionType
from ..models.xp24_msactiontable import InputAction, Xp24MsActionTable
from ..utils.checksum import calculate_checksum


class Xp24MsActionTableSerializer:
    """Handles serialization/deserialization of XP24 action tables to/from telegrams."""

    @staticmethod
    def _denibble(str_val: str) -> List[int]:
        """
        Convert hex string with A-P encoding to bytes.
        Based on pseudo code: A=0, B=1, C=2, ..., P=15
        """
        result = []
        for i in range(0, len(str_val), 2):
            # Get high and low nibbles
            high_char = str_val[i]
            low_char = str_val[i + 1]

            # Convert A-P to 0-15 (A=65 in ASCII, so A-65=0)
            high_nibble = (ord(high_char) - 65) << 4
            low_nibble = ord(low_char) - 65

            result.append(high_nibble + low_nibble)
        return result

    @staticmethod
    def to_telegrams(action_table: Xp24MsActionTable, serial: str) -> List[str]:
        """Serialize action table to telegram format."""
        data_parts = [f"S{serial}F17DAAAA"]

        # Encode all 4 input actions
        input_actions = [
            action_table.input1_action,
            action_table.input2_action,
            action_table.input3_action,
            action_table.input4_action,
        ]

        for action in input_actions:
            # Use enum value directly as function ID
            function_id = action.type.value
            # Convert parameter to int (None becomes 0)
            if action.param is None:
                param_value = 0
            elif action.param.isdigit():
                param_value = int(action.param)
            else:
                param_value = 0
            data_parts.append(f"{function_id:02X}{param_value:02X}")

        # Add settings as hex values
        data_parts.extend(
            [
                "AB" if action_table.mutex12 else "AA",
                "AB" if action_table.mutex34 else "AA",
                f"{action_table.ms:02X}",
                "AB" if action_table.curtain12 else "AA",
                "AB" if action_table.curtain34 else "AA",
                "A" * 38,  # padding
            ]
        )

        data = "".join(data_parts)
        checksum = calculate_checksum(data)
        return [f"<{data}{checksum}>"]

    @staticmethod
    def from_data(msactiontable_rawdata: str) -> Xp24MsActionTable:
        """Deserialize action table from raw data parts."""
        data = msactiontable_rawdata

        # Take first 64 chars (32 bytes) as per pseudo code
        hex_data = data[:64]

        # Convert hex string to bytes using deNibble (A-P encoding)
        raw_bytes = Xp24MsActionTableSerializer._denibble(hex_data)

        # Decode input actions from positions 0-3 (2 bytes each)
        input_actions = []
        for pos in range(4):
            input_action = Xp24MsActionTableSerializer._decode_input_action(raw_bytes, pos)
            input_actions.append(input_action)

        action_table = Xp24MsActionTable(
            input1_action=input_actions[0],
            input2_action=input_actions[1],
            input3_action=input_actions[2],
            input4_action=input_actions[3],
            mutex12=raw_bytes[8] != 0,  # With A-P encoding: AA=0 (False), AB=1 (True)
            mutex34=raw_bytes[9] != 0,
            ms=raw_bytes[10],
            curtain12=raw_bytes[11] != 0,
            curtain34=raw_bytes[12] != 0,
        )
        return action_table

    @staticmethod
    def _decode_input_action(raw_bytes: list[int], pos: int) -> InputAction:
        function_id = raw_bytes[2 * pos]
        param_value = raw_bytes[2 * pos + 1]

        # Convert function ID to InputActionType
        action_type = InputActionType(function_id)

        # Convert parameter (0 means None, otherwise string representation)
        param = None if param_value == 0 else str(param_value)
        return InputAction(action_type, param)

    @staticmethod
    def from_telegrams(ms_telegrams: List[str]) -> Xp24MsActionTable:
        """Legacy method for backward compatibility. Use from_data() instead."""
        # For backward compatibility, assume full telegrams and extract data
        data_parts = ""
        for telegram in ms_telegrams:
            # Assume it's already a data part
            data_parts += (telegram[20:84])

        return Xp24MsActionTableSerializer.from_data(data_parts)
