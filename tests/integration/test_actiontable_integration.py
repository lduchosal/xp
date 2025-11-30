"""Integration tests for ActionTable functionality."""

from unittest.mock import Mock

import pytest
from click.testing import CliRunner

from xp.cli.commands.conbus.conbus_actiontable_commands import (
    conbus_download_actiontable,
)
from xp.models import ModuleTypeCode
from xp.models.actiontable.actiontable import ActionTable, ActionTableEntry
from xp.models.telegram.input_action_type import InputActionType
from xp.models.telegram.timeparam_type import TimeParam
from xp.services.actiontable.actiontable_serializer import ActionTableSerializer
from xp.utils.serialization import de_nibbles


class TestActionTableIntegration:
    """Integration tests for ActionTable components."""

    @pytest.fixture
    def sample_actiontable(self):
        """Create sample ActionTable for testing."""
        entries = [
            ActionTableEntry(
                module_type=ModuleTypeCode.CP20,
                link_number=0,
                module_input=0,
                module_output=1,
                inverted=False,
                command=InputActionType.OFF,
                parameter=TimeParam.NONE,
            ),
            ActionTableEntry(
                module_type=ModuleTypeCode.CP20,
                link_number=0,
                module_input=1,
                module_output=2,
                inverted=True,
                command=InputActionType.ON,
                parameter=TimeParam.NONE,
            ),
        ]
        return ActionTable(entries=entries)

    def test_serializer_roundtrip(self, sample_actiontable):
        """Test ActionTableSerializer encode/decode roundtrip."""
        serializer = ActionTableSerializer()

        # Serialize to bytes
        encoded_string = serializer.to_encoded_string(sample_actiontable)
        data = de_nibbles(encoded_string)
        assert isinstance(data, (bytes, bytearray))
        assert len(data) > 0

        # Deserialize back
        restored_table = serializer.from_encoded_string(encoded_string)
        assert isinstance(restored_table, ActionTable)
        assert len(restored_table.entries) == len(sample_actiontable.entries)

        # Compare first entry
        original_entry = sample_actiontable.entries[0]
        restored_entry = restored_table.entries[0]

        assert restored_entry.module_type == original_entry.module_type
        assert restored_entry.link_number == original_entry.link_number
        assert restored_entry.module_input == original_entry.module_input
        assert restored_entry.module_output == original_entry.module_output

    def test_serializer_encoded_string_roundtrip(self, sample_actiontable):
        """Test ActionTableSerializer base64 string roundtrip."""
        serializer = ActionTableSerializer()

        # Encode to string
        encoded = serializer.to_encoded_string(sample_actiontable)
        assert isinstance(encoded, str)
        assert len(encoded) > 0

        # Decode back
        restored_table = serializer.from_encoded_string(encoded)
        assert isinstance(restored_table, ActionTable)
        assert len(restored_table.entries) == len(sample_actiontable.entries)

    def test_serializer_format_output(self, sample_actiontable):
        """Test ActionTableSerializer output formatting."""
        serializer = ActionTableSerializer()

        # Test decoded output format
        decoded = serializer.to_short_string(sample_actiontable)
        expected_lines = ["CP20 0 0 > 1 OFF;", "CP20 0 1 > 2 ~ON;"]
        assert decoded == expected_lines

        # Test encoded output format
        encoded = serializer.to_encoded_string(sample_actiontable)
        assert isinstance(encoded, str)
        assert len(encoded) > 0

    def test_end_to_end_cli_download(self, sample_actiontable):
        """Test end-to-end CLI download functionality."""
        # Setup mock service
        mock_service = Mock()
        mock_service.__enter__ = Mock(return_value=mock_service)
        mock_service.__exit__ = Mock(return_value=None)

        # Store the callbacks that are connected
        callbacks = {
            "on_finish": None,
            "on_progress": None,
            "on_actiontable_received": None,
        }

        def mock_on_finish_connect(callback):
            """
            Mock on_finish event connection.

            Args:
                callback: Callback function to store.
            """
            callbacks["on_finish"] = callback

        def mock_on_progress_connect(callback):
            """
            Mock on_progress event connection.

            Args:
                callback: Callback function to store.
            """
            callbacks["on_progress"] = callback

        def mock_on_actiontable_received_connect(callback):
            """
            Mock on_actiontable_received event connection.

            Args:
                callback: Callback function to store.
            """
            callbacks["on_actiontable_received"] = callback

        mock_service.on_finish.connect.side_effect = mock_on_finish_connect
        mock_service.on_progress.connect.side_effect = mock_on_progress_connect
        mock_service.on_actiontable_received.connect.side_effect = (
            mock_on_actiontable_received_connect
        )

        # Mock the configure method
        def mock_configure(serial_number, actiontable_type):
            """
            Test helper function.

            Args:
                serial_number: Serial number of the module.
                actiontable_type: Type of action table to download.
            """
            # Configure stores the serial number (nothing to do here for test)
            pass

        # Mock the start_reactor to trigger callbacks
        def mock_start_reactor_impl():
            """Mock reactor start method that triggers callbacks."""
            # Generate dict and short format like the service does
            actiontable_short = ActionTableSerializer.to_short_string(
                sample_actiontable
            )
            # Call the on_actiontable_received callback with data
            if callbacks["on_actiontable_received"]:
                callbacks["on_actiontable_received"](
                    sample_actiontable, actiontable_short
                )
            # Call the on_finish callback without arguments
            if callbacks["on_finish"]:
                callbacks["on_finish"]()

        mock_service.configure.side_effect = mock_configure
        mock_service.start_reactor.side_effect = mock_start_reactor_impl

        # Setup mock container
        mock_container = Mock()
        mock_container.resolve.return_value = mock_service

        mock_service_container = Mock()
        mock_service_container.get_container.return_value = mock_container

        # Create CLI runner with context
        result = CliRunner().invoke(
            conbus_download_actiontable,
            ["012345"],
            obj={"container": mock_service_container},
        )

        # Verify successful execution
        assert result.exit_code == 0

        # Verify output contains actiontable data
        # The output contains progress dots and then the JSON, so we check for the serial number
        assert "0000012345" in result.output
        assert "actiontable" in result.output

        # Verify service.start was called
        assert mock_service.configure.called

    def test_bcd_encoding_decoding(self):
        """Test BCD encoding/decoding functionality."""
        from xp.utils.serialization import de_bcd, to_bcd

        # Test BCD conversion
        test_values = [0, 5, 10, 15, 25, 99]
        for value in test_values:
            if value <= 99:  # BCD valid range
                bcd = to_bcd(value)
                decoded = de_bcd(bcd)
                assert decoded == value

    def test_bit_manipulation(self):
        """Test bit manipulation functions."""
        from xp.utils.serialization import lower3, upper5

        # Test lower 3 bits extraction
        test_byte = 0b11110111  # 247
        lower3_result = lower3(test_byte)
        assert lower3_result == 0b111  # 7

        # Test upper 5 bits extraction
        upper5_result = upper5(test_byte)
        assert upper5_result == 0b11110  # 30

    def test_actiontable_empty_entries(self):
        """Test ActionTable with empty entries."""
        empty_table = ActionTable(entries=[])
        serializer = ActionTableSerializer()

        # Empty table should be padded to 96 entries (480 bytes) during serialization
        encoded_string = serializer.to_encoded_string(empty_table)
        data = de_nibbles(encoded_string)

        assert isinstance(data, (bytes, bytearray))
        assert len(data) == 480  # 96 entries × 5 bytes
        assert bytes(data) == b"\x00" * 480  # All padding (NOMOD entries)

        # Restore table - padding (NOMOD entries) is stripped during deserialization
        restored = serializer.from_encoded_string(encoded_string)
        assert len(restored.entries) == 0  # Padding removed

    def test_actiontable_edge_cases(self):
        """Test ActionTable with edge case values."""
        edge_entry = ActionTableEntry(
            module_type=ModuleTypeCode.CP20,
            link_number=99,  # Max BCD value
            module_input=99,  # Max BCD value
            module_output=7,  # Max 3-bit value
            inverted=False,
            command=InputActionType.OFF,
            parameter=TimeParam.NONE,
        )
        edge_table = ActionTable(entries=[edge_entry])

        serializer = ActionTableSerializer()

        # Should handle edge values
        data = serializer.to_encoded_string(edge_table)
        restored = serializer.from_encoded_string(data)

        assert len(restored.entries) == 1
        restored_entry = restored.entries[0]
        assert restored_entry.link_number == edge_entry.link_number
        assert restored_entry.module_input == edge_entry.module_input
        assert restored_entry.module_output == edge_entry.module_output
