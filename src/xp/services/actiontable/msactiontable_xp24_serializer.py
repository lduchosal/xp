"""Serializer for XP24 Action Table telegram encoding/decoding."""

from xp.models.actiontable.msactiontable_xp24 import InputAction, Xp24MsActionTable
from xp.models.telegram.input_action_type import InputActionType
from xp.models.telegram.timeparam_type import TimeParam
from xp.utils.serialization import de_nibbles, nibbles


class Xp24MsActionTableSerializer:
    """Handles serialization/deserialization of XP24 action tables to/from telegrams."""

    @staticmethod
    def to_data(action_table: Xp24MsActionTable) -> str:
        """Serialize action table to telegram format.

        Args:
            action_table: XP24 MS action table to serialize.

        Returns:
            Serialized action table data string (68 characters).
        """
        # Build byte array for the action table (32 bytes total)
        raw_bytes = bytearray()

        # Encode all 4 input actions (2 bytes each = 8 bytes total)
        input_actions = [
            action_table.input1_action,
            action_table.input2_action,
            action_table.input3_action,
            action_table.input4_action,
        ]

        for action in input_actions:
            raw_bytes.append(action.type.value)
            raw_bytes.append(action.param.value)

        # Add settings (5 bytes)
        raw_bytes.append(0x01 if action_table.mutex12 else 0x00)
        raw_bytes.append(0x01 if action_table.mutex34 else 0x00)
        raw_bytes.append(action_table.mutual_deadtime)
        raw_bytes.append(0x01 if action_table.curtain12 else 0x00)
        raw_bytes.append(0x01 if action_table.curtain34 else 0x00)

        # Add padding to reach 32 bytes (19 more bytes needed)
        raw_bytes.extend([0x00] * 19)

        # Encode to A-P nibbles (32 bytes -> 64 chars)
        encoded_data = nibbles(bytes(raw_bytes))

        # Prepend action table count "AAAA" (4 chars) -> total 68 chars
        return "AAAA" + encoded_data

    @staticmethod
    def from_data(msactiontable_rawdata: str) -> Xp24MsActionTable:
        """Deserialize action table from raw data parts.

        Args:
            msactiontable_rawdata: Raw action table data string.

        Returns:
            Deserialized XP24 MS action table.

        Raises:
            ValueError: If data length is not 68 bytes.
        """
        raw_length = len(msactiontable_rawdata)
        if raw_length != 68:
            raise ValueError(
                f"Msactiontable is not 68 bytes long ({raw_length}): {msactiontable_rawdata}"
            )

        # Remove action table count AAAA, AAAB .
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
        """Decode input action from raw bytes.

        Args:
            raw_bytes: Raw byte array containing action data.
            pos: Position of the action to decode.

        Returns:
            Decoded input action.
        """
        function_id = raw_bytes[2 * pos]
        param_id = raw_bytes[2 * pos + 1]

        # Convert function ID to InputActionType
        action_type = InputActionType(function_id)
        param_type = TimeParam(param_id)

        return InputAction(action_type, param_type)
