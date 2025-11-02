"""Serializer for XP33 Action Table telegram encoding/decoding."""

from xp.models.actiontable.msactiontable_xp33 import (
    Xp33MsActionTable,
    Xp33Output,
    Xp33Scene,
)
from xp.models.telegram.timeparam_type import TimeParam
from xp.utils.serialization import bits_to_byte, byte_to_bits, de_nibbles, nibbles


class Xp33MsActionTableSerializer:
    """Handles serialization/deserialization of XP33 action tables to/from telegrams."""

    @staticmethod
    def _percentage_to_byte(percentage: int) -> int:
        """Convert percentage (0-100) to byte value for telegram encoding."""
        return min(max(percentage, 0), 100)

    @staticmethod
    def _byte_to_percentage(byte_val: int) -> int:
        """Convert byte value from telegram to percentage (0-100)."""
        return min(max(byte_val, 0), 100)

    @staticmethod
    def _time_param_to_byte(time_param: TimeParam) -> int:
        """Convert TimeParam enum to byte value for telegram encoding."""
        return time_param.value

    @staticmethod
    def _byte_to_time_param(byte_val: int) -> TimeParam:
        """Convert byte value from telegram to TimeParam enum."""
        try:
            return TimeParam(byte_val)
        except ValueError:
            return TimeParam.NONE

    @staticmethod
    def to_data(action_table: Xp33MsActionTable) -> str:
        """Serialize action table to telegram format.

        Args:
            action_table: XP33 MS action table to serialize.

        Returns:
            Serialized action table data string.
        """
        # Create 32-byte array
        raw_bytes = bytearray(32)

        # Encode output min/max levels (bytes 0-5)
        outputs = [action_table.output1, action_table.output2, action_table.output3]
        for i, output in enumerate(outputs):
            raw_bytes[2 * i] = Xp33MsActionTableSerializer._percentage_to_byte(
                output.min_level
            )
            raw_bytes[2 * i + 1] = Xp33MsActionTableSerializer._percentage_to_byte(
                output.max_level
            )

        # Encode scenes (bytes 6-21)
        scenes = [
            action_table.scene1,
            action_table.scene2,
            action_table.scene3,
            action_table.scene4,
        ]
        for scene_idx, scene in enumerate(scenes):
            offset = 6 + (4 * scene_idx)
            raw_bytes[offset] = Xp33MsActionTableSerializer._time_param_to_byte(
                scene.time
            )
            raw_bytes[offset + 1] = Xp33MsActionTableSerializer._percentage_to_byte(
                scene.output1_level
            )
            raw_bytes[offset + 2] = Xp33MsActionTableSerializer._percentage_to_byte(
                scene.output2_level
            )
            raw_bytes[offset + 3] = Xp33MsActionTableSerializer._percentage_to_byte(
                scene.output3_level
            )

        # Encode bit flags (bytes 22-24)
        scene_outputs_bits = [False] * 8
        start_at_full_bits = [False] * 8
        leading_edge_bits = [False] * 8

        for i, output in enumerate(outputs):
            if i < 3:  # Only 3 outputs
                scene_outputs_bits[i] = output.scene_outputs
                start_at_full_bits[i] = output.start_at_full
                leading_edge_bits[i] = output.leading_edge

        raw_bytes[22] = bits_to_byte(scene_outputs_bits)
        raw_bytes[23] = bits_to_byte(start_at_full_bits)
        raw_bytes[24] = bits_to_byte(leading_edge_bits)

        # Bytes 25-31 are padding (already 0)
        # Convert to hex string using nibble encoding
        encoded_data = nibbles(raw_bytes)

        # Convert raw bytes to hex string with A-P encoding
        return "AAAA" + encoded_data

    @staticmethod
    def from_data(msactiontable_rawdata: str) -> Xp33MsActionTable:
        """Deserialize action table from raw data parts.

        Args:
            msactiontable_rawdata: Raw action table data string.

        Returns:
            Deserialized XP33 MS action table.

        Raises:
            ValueError: If data length is less than 68 characters.
        """
        raw_length = len(msactiontable_rawdata)
        if raw_length < 68:  # Minimum: 4 char prefix + 64 chars data
            raise ValueError(
                f"Msactiontable is too short ({raw_length}), minimum 68 characters required"
            )

        # Remove action table count prefix (first 4 characters: AAAA, AAAB, etc.)
        data = msactiontable_rawdata[4:]

        # Take first 64 chars (32 bytes) as per pseudocode
        hex_data = data[:64]

        # Convert hex string to bytes using deNibble (A-P encoding)
        raw_bytes = de_nibbles(hex_data)

        # Decode outputs
        output1 = Xp33MsActionTableSerializer._decode_output(raw_bytes, 0)
        output2 = Xp33MsActionTableSerializer._decode_output(raw_bytes, 1)
        output3 = Xp33MsActionTableSerializer._decode_output(raw_bytes, 2)

        # Decode scenes
        scene1 = Xp33MsActionTableSerializer._decode_scene(raw_bytes, 0)
        scene2 = Xp33MsActionTableSerializer._decode_scene(raw_bytes, 1)
        scene3 = Xp33MsActionTableSerializer._decode_scene(raw_bytes, 2)
        scene4 = Xp33MsActionTableSerializer._decode_scene(raw_bytes, 3)

        return Xp33MsActionTable(
            output1=output1,
            output2=output2,
            output3=output3,
            scene1=scene1,
            scene2=scene2,
            scene3=scene3,
            scene4=scene4,
        )

    @staticmethod
    def _decode_output(raw_bytes: bytearray, output_index: int) -> Xp33Output:
        """Extract output configuration from raw bytes.

        Args:
            raw_bytes: Raw byte array containing output data.
            output_index: Index of the output to decode.

        Returns:
            Decoded XP33 output configuration.
        """
        # Read min/max levels from appropriate offsets
        min_level = Xp33MsActionTableSerializer._byte_to_percentage(
            raw_bytes[2 * output_index]
        )
        max_level = Xp33MsActionTableSerializer._byte_to_percentage(
            raw_bytes[2 * output_index + 1]
        )

        # Extract bit flags from bytes 22-24
        scene_outputs_bits = byte_to_bits(raw_bytes[22])
        start_at_full_bits = byte_to_bits(raw_bytes[23])

        # Handle dimFunction with exception handling as per specification
        if len(raw_bytes) > 24:
            leading_edge_bits = byte_to_bits(raw_bytes[24])
        else:
            leading_edge_bits = [False] * 8

        # Map bit flags to output properties
        scene_outputs = (
            scene_outputs_bits[output_index]
            if output_index < len(scene_outputs_bits)
            else False
        )
        start_at_full = (
            start_at_full_bits[output_index]
            if output_index < len(start_at_full_bits)
            else False
        )
        leading_edge = (
            leading_edge_bits[output_index]
            if output_index < len(leading_edge_bits)
            else False
        )

        return Xp33Output(
            min_level=min_level,
            max_level=max_level,
            scene_outputs=scene_outputs,
            start_at_full=start_at_full,
            leading_edge=leading_edge,
        )

    @staticmethod
    def _decode_scene(raw_bytes: bytearray, scene_index: int) -> Xp33Scene:
        """Extract scene configuration from raw bytes.

        Args:
            raw_bytes: Raw byte array containing scene data.
            scene_index: Index of the scene to decode.

        Returns:
            Decoded XP33 scene configuration.
        """
        # Calculate scene offset: 6 + (4 * scene_index)
        offset = 6 + (4 * scene_index)

        # Parse time parameter and output levels
        time_param = Xp33MsActionTableSerializer._byte_to_time_param(raw_bytes[offset])
        output1_level = Xp33MsActionTableSerializer._byte_to_percentage(
            raw_bytes[offset + 1]
        )
        output2_level = Xp33MsActionTableSerializer._byte_to_percentage(
            raw_bytes[offset + 2]
        )
        output3_level = Xp33MsActionTableSerializer._byte_to_percentage(
            raw_bytes[offset + 3]
        )

        return Xp33Scene(
            output1_level=output1_level,
            output2_level=output2_level,
            output3_level=output3_level,
            time=time_param,
        )
