"""Serializer for XP24 Action Table telegram encoding/decoding."""

from ..models.input_action_type import InputActionType
from ..models.timeparam_type import TimeParam
from ..models.msactiontable_xp24 import InputAction, Xp24MsActionTable
from ..utils.serialization import de_nibbles


class Xp24MsActionTableSerializer:
    """Handles serialization/deserialization of XP24 action tables to/from telegrams."""

    @staticmethod
    def to_data(action_table: Xp24MsActionTable) -> str:
        """Serialize action table to telegram format."""
        data_parts: list[str] = []

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
            param_id = action.param.value
            data_parts.append(f"{function_id:02X}{param_id:02X}")

        # Add settings as hex values
        data_parts.extend(
            [
                "AB" if action_table.mutex12 else "AA",
                "AB" if action_table.mutex34 else "AA",
                f"{action_table.mutual_deadtime:02X}",
                "AB" if action_table.curtain12 else "AA",
                "AB" if action_table.curtain34 else "AA",
                "A" * 38,  # padding
            ]
        )

        data = "AAAA".join(data_parts)
        return data

    @staticmethod
    def from_data(msactiontable_rawdata: str) -> Xp24MsActionTable:
        """Deserialize action table from raw data parts."""

        raw_length = len(msactiontable_rawdata)
        if raw_length != 68:
            raise ValueError(f"Msactiontable is not 68 bytes long ({raw_length})")

        # Remove action table count AAAA, AAAB ...
        data = msactiontable_rawdata[4:]

        # Take first 64 chars (32 bytes) as per pseudocode
        hex_data = data[:64]

        # Convert hex string to bytes using deNibble (A-P encoding)
        raw_bytes = de_nibbles(hex_data)

        # Decode input actions from positions 0-3 (2 bytes each)
        input_actions = []
        for pos in range(4):
            input_action = Xp24MsActionTableSerializer._decode_input_action(
                raw_bytes, pos
            )
            input_actions.append(input_action)

        action_table = Xp24MsActionTable(
            input1_action=input_actions[0],
            input2_action=input_actions[1],
            input3_action=input_actions[2],
            input4_action=input_actions[3],
            mutex12=raw_bytes[8] != 0,  # With A-P encoding: AA=0 (False), AB=1 (True)
            mutex34=raw_bytes[9] != 0,
            mutual_deadtime=raw_bytes[10],
            curtain12=raw_bytes[11] != 0,
            curtain34=raw_bytes[12] != 0,
        )
        return action_table

    @staticmethod
    def _decode_input_action(raw_bytes: bytearray, pos: int) -> InputAction:
        function_id = raw_bytes[2 * pos]
        param_id = raw_bytes[2 * pos + 1]

        # Convert function ID to InputActionType
        action_type = InputActionType(function_id)
        param_type = TimeParam(param_id)

        return InputAction(action_type, param_type)

    @staticmethod
    def from_telegrams(ms_telegrams: str) -> Xp24MsActionTable:
        """Legacy method for backward compatibility. Use from_data() instead."""
        # For backward compatibility, assume full telegrams and extract data
        data_parts = ms_telegrams[16:84]

        return Xp24MsActionTableSerializer.from_data(data_parts)
