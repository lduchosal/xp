"""Serializer for XP24 Action Table telegram encoding/decoding."""

from typing import List

from ..models.input_action_type import InputActionType
from ..models.xp24_msactiontable import InputAction, Xp24MsActionTable
from ..utils.checksum import calculate_checksum


class Xp24ActionTableSerializer:
    """Handles serialization/deserialization of XP24 action tables to/from telegrams."""

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
    def from_telegrams(ms_telegrams: List[str]) -> Xp24MsActionTable:
        """Deserialize action table from telegram format."""
        # Extract and concatenate payload data
        concat = "".join(telegram[20:84] for telegram in ms_telegrams)
        raw_bytes = bytes.fromhex(concat[:64])

        # Decode input actions
        input_actions = []
        for i in range(4):
            function_id = raw_bytes[2 * i]
            param_value = raw_bytes[2 * i + 1]

            # Find action type by enum value
            action_type = InputActionType.VOID  # Default fallback
            for action in InputActionType:
                if action.value == function_id:
                    action_type = action
                    break

            # Convert parameter (0 becomes None for cleaner representation)
            param_str = None if param_value == 0 else str(param_value)
            input_actions.append(InputAction(action_type, param_str))

        action_table = Xp24MsActionTable(
            input1_action=input_actions[0],
            input2_action=input_actions[1],
            input3_action=input_actions[2],
            input4_action=input_actions[3],
            mutex12=raw_bytes[8] == 0xAB,  # AB = True, AA = False
            mutex34=raw_bytes[9] == 0xAB,
            ms=raw_bytes[10],
            curtain12=raw_bytes[11] == 0xAB,
            curtain34=raw_bytes[12] == 0xAB,
        )

        return action_table
