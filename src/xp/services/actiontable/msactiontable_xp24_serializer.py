"""Serializer for XP24 Action Table telegram encoding/decoding."""

from xp.models.actiontable.msactiontable_xp24 import InputAction, Xp24MsActionTable
from xp.models.telegram.input_action_type import InputActionType
from xp.models.telegram.system_function import SystemFunction
from xp.models.telegram.timeparam_type import TimeParam
from xp.services.actiontable.serializer_protocol import ActionTableSerializerProtocol
from xp.utils.serialization import de_nibbles, nibbles


class Xp24MsActionTableSerializer(ActionTableSerializerProtocol):
    """Handles serialization/deserialization of XP24 action tables to/from telegrams."""

    @staticmethod
    def download_type() -> SystemFunction:
        """
        Get the download system function type.

        Returns:
            The download system function: DOWNLOAD_MSACTIONTABLE
        """
        return SystemFunction.DOWNLOAD_MSACTIONTABLE

    @staticmethod
    def from_encoded_string(encoded_data: str) -> Xp24MsActionTable:
        """
        Deserialize action table from raw data parts.

        Args:
            encoded_data: Raw action table data string.

        Returns:
            Deserialized XP24 MS action table.

        Raises:
            ValueError: If data length is not 68 bytes.
        """
        raw_length = len(encoded_data)
        if raw_length != 64:
            raise ValueError(
                f"Msactiontable is not 64 bytes long ({raw_length}): {encoded_data}"
            )

        # Convert hex string to bytes using deNibble (A-P encoding)
        data = de_nibbles(encoded_data)

        # Decode input actions from positions 0-3 (2 bytes each)
        input_actions = []
        for pos in range(4):
            input_action = Xp24MsActionTableSerializer._decode_input_action(data, pos)
            input_actions.append(input_action)

        action_table = Xp24MsActionTable(
            input1_action=input_actions[0],
            input2_action=input_actions[1],
            input3_action=input_actions[2],
            input4_action=input_actions[3],
            mutex12=data[8] != 0,  # With A-P encoding: AA=0 (False), AB=1 (True)
            mutex34=data[9] != 0,
            mutual_deadtime=data[10],
            curtain12=data[11] != 0,
            curtain34=data[12] != 0,
        )
        return action_table

    @staticmethod
    def to_encoded_string(action_table: Xp24MsActionTable) -> str:
        """
        Serialize action table to telegram format.

        Args:
            action_table: XP24 MS action table to serialize.

        Returns:
            Serialized action table data string (64 characters).
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

        # Build byte array for the action table (32 bytes total)
        # Prepend action table count "AAAA" (4 chars) -> total 68 chars
        return nibbles(raw_bytes)

    @staticmethod
    def to_short_string(action_table: Xp24MsActionTable) -> list[str]:
        """
        Serialize XP24 action table to humane compact readable format.

        Args:
            action_table: XP24 action table to serialize

        Returns:
            Human-readable string describing XP24 action table
        """
        return action_table.to_short_format()

    @staticmethod
    def from_short_string(action_strings: list[str]) -> Xp24MsActionTable:
        """
        Serialize XP24 action table to humane compact readable format.

        Args:
            action_strings: XP24 action table to serialize

        Returns:
            Human-readable string describing XP24 action table
        """
        return Xp24MsActionTable.from_short_format(action_strings)

    @staticmethod
    def _decode_input_action(raw_bytes: bytes, pos: int) -> InputAction:
        """
        Decode input action from raw bytes.

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

        return InputAction(type=action_type, param=param_type)
