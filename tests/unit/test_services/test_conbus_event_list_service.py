"""Unit tests for ConbusEventListService."""

import pytest

from xp.models.homekit.homekit_conson_config import (
    ConsonModuleConfig,
    ConsonModuleListConfig,
)
from xp.services.conbus.conbus_event_list_service import ConbusEventListService


class TestConbusEventListService:
    """Unit tests for ConbusEventListService functionality."""

    @pytest.fixture
    def empty_config(self):
        """Create empty config with no modules."""
        return ConsonModuleListConfig(root=[])

    @pytest.fixture
    def single_module_config(self):
        """Create config with single module and one action."""
        module = ConsonModuleConfig(
            name="A1",
            serial_number="0012345001",
            module_type="XP20",
            module_type_code=33,
            link_number=0,
            action_table=["XP20 10 0 > 0 OFF"],
        )
        return ConsonModuleListConfig(root=[module])

    @pytest.fixture
    def multiple_modules_same_event_config(self):
        """Create config with multiple modules sharing same event."""
        module1 = ConsonModuleConfig(
            name="A1",
            serial_number="0012345001",
            module_type="XP20",
            module_type_code=33,
            link_number=0,
            action_table=["XP20 10 0 > 0 OFF"],
        )
        module2 = ConsonModuleConfig(
            name="A2",
            serial_number="0012345002",
            module_type="XP20",
            module_type_code=33,
            link_number=0,
            action_table=["XP20 10 0 > 1 ON"],
        )
        module3 = ConsonModuleConfig(
            name="A3",
            serial_number="0012345003",
            module_type="XP20",
            module_type_code=33,
            link_number=0,
            action_table=["XP20 10 0 > 2 OFF"],
        )
        return ConsonModuleListConfig(root=[module1, module2, module3])

    @pytest.fixture
    def duplicate_actions_config(self):
        """Create config with duplicate actions in same module."""
        module = ConsonModuleConfig(
            name="A1",
            serial_number="0012345001",
            module_type="XP20",
            module_type_code=33,
            link_number=0,
            action_table=[
                "XP20 10 0 > 0 OFF",
                "XP20 10 0 > 1 OFF",
                "XP20 10 0 > 2 OFF",
            ],
        )
        return ConsonModuleListConfig(root=[module])

    @pytest.fixture
    def invalid_action_config(self):
        """Create config with invalid action format."""
        module = ConsonModuleConfig(
            name="A1",
            serial_number="0012345001",
            module_type="XP20",
            module_type_code=33,
            link_number=0,
            action_table=[
                "XP20 10 0 > 0 OFF",  # Valid
                "INVALID ACTION FORMAT",  # Invalid
                "XP20 10 8 > 0 ON",  # Valid
            ],
        )
        return ConsonModuleListConfig(root=[module])

    @pytest.fixture
    def empty_action_table_config(self):
        """Create config with module having empty action table."""
        module1 = ConsonModuleConfig(
            name="A1",
            serial_number="0012345001",
            module_type="XP20",
            module_type_code=33,
            link_number=0,
            action_table=[],
        )
        module2 = ConsonModuleConfig(
            name="A2",
            serial_number="0012345002",
            module_type="XP20",
            module_type_code=33,
            link_number=0,
            action_table=["XP20 10 0 > 0 OFF"],
        )
        return ConsonModuleListConfig(root=[module1, module2])

    @pytest.fixture
    def sorting_config(self):
        """Create config for testing sorting by module count."""
        # Event XP20 10 00 has 3 modules
        module1 = ConsonModuleConfig(
            name="A1",
            serial_number="0012345001",
            module_type="XP20",
            module_type_code=33,
            link_number=0,
            action_table=["XP20 10 0 > 0 OFF"],
        )
        module2 = ConsonModuleConfig(
            name="A2",
            serial_number="0012345002",
            module_type="XP20",
            module_type_code=33,
            link_number=0,
            action_table=["XP20 10 0 > 1 ON"],
        )
        module3 = ConsonModuleConfig(
            name="A3",
            serial_number="0012345003",
            module_type="XP20",
            module_type_code=33,
            link_number=0,
            action_table=["XP20 10 0 > 2 OFF"],
        )
        # Event XP20 10 08 has 2 modules
        module4 = ConsonModuleConfig(
            name="A4",
            serial_number="0012345004",
            module_type="XP20",
            module_type_code=33,
            link_number=0,
            action_table=["XP20 10 8 > 0 ON"],
        )
        module5 = ConsonModuleConfig(
            name="A5",
            serial_number="0012345005",
            module_type="XP20",
            module_type_code=33,
            link_number=0,
            action_table=["XP20 10 8 > 1 OFF"],
        )
        # Event CP20 00 00 has 1 module
        module6 = ConsonModuleConfig(
            name="A6",
            serial_number="0012345006",
            module_type="CP20",
            module_type_code=2,
            link_number=0,
            action_table=["CP20 0 0 > 0 OFF"],
        )
        return ConsonModuleListConfig(
            root=[module1, module2, module3, module4, module5, module6]
        )

    def test_empty_config(self, empty_config):
        """Test with empty configuration (no modules)."""
        response = ConbusEventListService(conson_config=empty_config).list_events()

        assert response.events == {}
        assert response.timestamp is not None

    def test_single_module(self, single_module_config):
        """Test with single module and one action."""
        response = ConbusEventListService(
            conson_config=single_module_config
        ).list_events()

        assert len(response.events) == 1
        assert "XP20 10 00" in response.events
        assert response.events["XP20 10 00"] == ["0012345001:0"]

    def test_multiple_modules_same_event(self, multiple_modules_same_event_config):
        """Test multiple modules sharing same event."""
        response = ConbusEventListService(
            conson_config=multiple_modules_same_event_config
        ).list_events()

        assert len(response.events) == 1
        assert "XP20 10 00" in response.events
        assert sorted(response.events["XP20 10 00"]) == [
            "0012345001:0",
            "0012345002:1",
            "0012345003:2",
        ]

    def test_duplicate_actions_deduplication(self, duplicate_actions_config):
        """Test that duplicate actions in same module are deduplicated."""
        response = ConbusEventListService(
            conson_config=duplicate_actions_config
        ).list_events()

        assert len(response.events) == 1
        assert "XP20 10 00" in response.events
        assert response.events["XP20 10 00"] == [
            "0012345001:0",
            "0012345001:1",
            "0012345001:2",
        ]  # Only once, not three times

    def test_invalid_action_format(self, invalid_action_config, caplog):
        """Test that invalid actions are skipped with warning."""
        response = ConbusEventListService(
            conson_config=invalid_action_config
        ).list_events()

        # Should have 2 valid events
        assert len(response.events) == 2
        assert "XP20 10 00" in response.events
        assert "XP20 10 08" in response.events

        # Should have logged warning about invalid action
        assert "Invalid action" in caplog.text
        assert "INVALID ACTION FORMAT" in caplog.text

    def test_empty_action_table(self, empty_action_table_config):
        """Test that modules with empty action table are silently skipped."""
        response = ConbusEventListService(
            conson_config=empty_action_table_config
        ).list_events()

        # Only A2 should be in result (A1 has empty action_table)
        assert len(response.events) == 1
        assert "XP20 10 00" in response.events
        assert response.events["XP20 10 00"] == ["0012345002:0"]

    def test_sorting_by_module_count(self, sorting_config):
        """Test that events are sorted by module count (descending)."""
        response = ConbusEventListService(conson_config=sorting_config).list_events()

        # Get events in order
        event_keys = list(response.events.keys())

        # Should be sorted by count: XP20 10 00 (3), XP20 10 08 (2), CP20 00 00 (1)
        assert event_keys[0] == "XP20 10 00"
        assert len(response.events[event_keys[0]]) == 3
        assert event_keys[1] == "XP20 10 08"
        assert len(response.events[event_keys[1]]) == 2
        assert event_keys[2] == "CP20 00 00"
        assert len(response.events[event_keys[2]]) == 1

    def test_to_dict_serialization(self, single_module_config):
        """Test that response can be serialized to dict."""
        result_dict = (
            ConbusEventListService(conson_config=single_module_config)
            .list_events()
            .to_dict()
        )

        assert "events" in result_dict
        assert "timestamp" in result_dict
        assert isinstance(result_dict["events"], dict)
        assert isinstance(result_dict["timestamp"], str)  # ISO format
