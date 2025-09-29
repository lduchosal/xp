"""Integration tests for ActionTable functionality."""

import pytest
from unittest.mock import Mock, patch
import json
from click.testing import CliRunner

from xp.services.actiontable_service import ActionTableService
from xp.services.actiontable_serializer import ActionTableSerializer
from xp.cli.commands.conbus_actiontable_commands import conbus_download_actiontable
from xp.models.actiontable import ActionTable, ActionTableEntry
from xp.models import ModuleTypeCode
from xp.models.input_action_type import InputActionType
from xp.models.timeparam_type import TimeParam


class TestActionTableIntegration:
    """Integration tests for ActionTable components"""

    @pytest.fixture
    def sample_actiontable(self):
        """Create sample ActionTable for testing"""
        entries = [
            ActionTableEntry(
                module_type=ModuleTypeCode.CP20,
                link_number=0,
                module_input=0,
                module_output=1,
                inverted=False,
                command=InputActionType.TURNOFF,
                parameter=TimeParam.NONE,
            ),
            ActionTableEntry(
                module_type=ModuleTypeCode.CP20,
                link_number=0,
                module_input=1,
                module_output=2,
                inverted=True,
                command=InputActionType.TURNON,
                parameter=TimeParam.NONE,
            ),
        ]
        return ActionTable(entries=entries)

    def test_serializer_roundtrip(self, sample_actiontable):
        """Test ActionTableSerializer encode/decode roundtrip"""
        serializer = ActionTableSerializer()

        # Serialize to bytes
        data = serializer.to_data(sample_actiontable)
        assert isinstance(data, bytes)
        assert len(data) > 0

        # Deserialize back
        restored_table = serializer.from_data(data)
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
        """Test ActionTableSerializer base64 string roundtrip"""
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
        """Test ActionTableSerializer output formatting"""
        serializer = ActionTableSerializer()

        # Test decoded output format
        decoded = serializer.format_decoded_output(sample_actiontable)
        expected_lines = ["CP20 0 0 > 1 TURNOFF;", "CP20 0 1 > 2 ~TURNON;"]
        assert decoded == "\n".join(expected_lines)

        # Test encoded output format
        encoded = serializer.to_encoded_string(sample_actiontable)
        assert isinstance(encoded, str)
        assert len(encoded) > 0

    def test_service_serializer_integration(self, sample_actiontable):
        """Test ActionTableService and ActionTableSerializer integration"""
        # Setup service with mocked dependencies
        service = ActionTableService()

        # Test formatting methods work
        decoded = service.format_decoded_output(sample_actiontable)
        encoded = service.format_encoded_output(sample_actiontable)

        assert isinstance(decoded, str)
        assert isinstance(encoded, str)
        assert "CP20 0 0 > 1 TURNOFF;" in decoded
        assert len(encoded) > 0

    @patch("xp.cli.commands.conbus_actiontable_commands.ActionTableService")
    def test_end_to_end_cli_download(self, mock_service_class, sample_actiontable):
        """Test end-to-end CLI download functionality"""
        # Setup mock service
        mock_service = Mock()
        mock_service.__enter__ = Mock(return_value=mock_service)
        mock_service.__exit__ = Mock(return_value=None)
        mock_service.download_actiontable.return_value = sample_actiontable
        mock_service_class.return_value = mock_service

        # Create CLI runner and execute command
        result = CliRunner().invoke(conbus_download_actiontable, ["012345"])

        # Verify successful execution
        assert result.exit_code == 0

        # Verify output is valid JSON
        output_data = json.loads(result.output)
        assert "serial_number" in output_data
        assert "actiontable" in output_data
        assert output_data["serial_number"] == "0000012345"

        # Verify service was called correctly
        mock_service.download_actiontable.assert_called_once_with("0000012345")

    def test_bcd_encoding_decoding(self):
        """Test BCD encoding/decoding functionality"""
        from xp.utils.serialization import to_bcd, de_bcd

        # Test BCD conversion
        test_values = [0, 5, 10, 15, 25, 99]
        for value in test_values:
            if value <= 99:  # BCD valid range
                bcd = to_bcd(value)
                decoded = de_bcd(bcd)
                assert decoded == value

    def test_bit_manipulation(self):
        """Test bit manipulation functions"""
        from xp.utils.serialization import lower3, upper5

        # Test lower 3 bits extraction
        test_byte = 0b11110111  # 247
        lower3_result = lower3(test_byte)
        assert lower3_result == 0b111  # 7

        # Test upper 5 bits extraction
        upper5_result = upper5(test_byte)
        assert upper5_result == 0b11110  # 30

    def test_actiontable_empty_entries(self):
        """Test ActionTable with empty entries"""
        empty_table = ActionTable(entries=[])
        serializer = ActionTableSerializer()

        # Should handle empty table gracefully
        data = serializer.to_data(empty_table)
        assert isinstance(data, bytes)
        assert len(data) == 0

        # Restore empty table
        restored = serializer.from_data(data)
        assert len(restored.entries) == 0

    def test_actiontable_edge_cases(self):
        """Test ActionTable with edge case values"""
        edge_entry = ActionTableEntry(
            module_type=ModuleTypeCode.CP20,
            link_number=99,  # Max BCD value
            module_input=99,  # Max BCD value
            module_output=7,  # Max 3-bit value
            inverted=False,
            command=InputActionType.TURNOFF,
            parameter=TimeParam.NONE,
        )
        edge_table = ActionTable(entries=[edge_entry])

        serializer = ActionTableSerializer()

        # Should handle edge values
        data = serializer.to_data(edge_table)
        restored = serializer.from_data(data)

        assert len(restored.entries) == 1
        restored_entry = restored.entries[0]
        assert restored_entry.link_number == edge_entry.link_number
        assert restored_entry.module_input == edge_entry.module_input
        assert restored_entry.module_output == edge_entry.module_output
