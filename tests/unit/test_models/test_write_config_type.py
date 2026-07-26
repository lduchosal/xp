# Copyright (c) 2025 ldvchosal
"""Tests for WriteConfigType model."""

from xp.models.write_config_type import WriteConfigType


class TestWriteConfigType:
    """Test WriteConfigType enum."""

    def test_enum_values(self) -> None:
        """Test enum has expected values."""
        assert WriteConfigType.LINK_NUMBER.value == "04"
        assert WriteConfigType.MODULE_NUMBER.value == "05"
        assert WriteConfigType.SYSTEM_TYPE.value == "06"

    def test_from_code_link_number(self) -> None:
        """Test from_code with link number code."""
        result = WriteConfigType.from_code("04")
        assert result == WriteConfigType.LINK_NUMBER

    def test_from_code_module_number(self) -> None:
        """Test from_code with module number code."""
        result = WriteConfigType.from_code("05")
        assert result == WriteConfigType.MODULE_NUMBER

    def test_from_code_system_type(self) -> None:
        """Test from_code with system type code."""
        result = WriteConfigType.from_code("06")
        assert result == WriteConfigType.SYSTEM_TYPE

    def test_from_code_invalid(self) -> None:
        """Test from_code with invalid code returns None."""
        result = WriteConfigType.from_code("99")
        assert result is None

    def test_from_code_empty_string(self) -> None:
        """Test from_code with empty string returns None."""
        result = WriteConfigType.from_code("")
        assert result is None

    def test_enum_iteration(self) -> None:
        """Test iterating over enum members."""
        members = list(WriteConfigType)
        expected_member_count = 3
        assert len(members) == expected_member_count
        assert WriteConfigType.LINK_NUMBER in members
        assert WriteConfigType.MODULE_NUMBER in members
        assert WriteConfigType.SYSTEM_TYPE in members

    def test_string_representation(self) -> None:
        """Test string representation of enum members."""
        assert str(WriteConfigType.LINK_NUMBER) == "WriteConfigType.LINK_NUMBER"

    def test_enum_is_string(self) -> None:
        """Test enum values are strings."""
        for member in WriteConfigType:
            assert isinstance(member.value, str)
