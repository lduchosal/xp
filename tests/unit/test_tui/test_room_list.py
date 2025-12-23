"""Unit tests for RoomListWidget."""

from datetime import datetime, timedelta
from unittest.mock import Mock

import pytest

from xp.models.term.accessory_state import AccessoryState
from xp.term.widgets.room_list import RoomListWidget


class TestRoomListWidget:
    """Unit tests for RoomListWidget functionality."""

    @pytest.fixture
    def mock_service(self):
        """Create a mock HomekitService."""
        service = Mock()
        service.on_room_list_updated = Mock()
        service.on_room_list_updated.connect = Mock()
        service.on_room_list_updated.disconnect = Mock()
        service.on_module_state_changed = Mock()
        service.on_module_state_changed.connect = Mock()
        service.on_module_state_changed.disconnect = Mock()
        service.accessory_states = []
        return service

    @pytest.fixture
    def widget(self, mock_service):
        """Create widget instance with mock service."""
        return RoomListWidget(service=mock_service)

    @pytest.fixture
    def accessory_state(self):
        """Create a basic AccessoryState for testing."""
        return AccessoryState(
            room_name="Living Room",
            accessory_name="Main Light",
            action="a",
            output_state="ON",
            dimming_state="",
            module_name="A01",
            serial_number="1234567890",
            module_type="XP24",
            error_status="OK",
            output=1,
            sort=1,
            last_update=datetime.now(),
        )

    @pytest.fixture
    def dimmable_accessory_state(self):
        """Create a dimmable AccessoryState for testing."""
        return AccessoryState(
            room_name="Bedroom",
            accessory_name="Dimmer",
            action="b",
            output_state="ON",
            dimming_state="75%",
            module_name="A02",
            serial_number="2222222222",
            module_type="XP33LED",
            error_status="OK",
            output=1,
            sort=2,
            last_update=datetime.now(),
        )

    def test_widget_initialization(self, widget, mock_service):
        """Test widget can be initialized with required dependencies."""
        assert widget.service == mock_service

    def test_format_dim_non_dimmable(self, widget, accessory_state):
        """Test _format_dim returns empty for non-dimmable modules."""
        result = widget._format_dim(accessory_state)
        assert result == ""

    def test_format_dim_dimmable_on(self, widget, dimmable_accessory_state):
        """Test _format_dim returns percentage for dimmable ON modules."""
        result = widget._format_dim(dimmable_accessory_state)
        assert result == "75%"

    def test_format_dim_dimmable_off(self, widget):
        """Test _format_dim returns dash for dimmable OFF modules."""
        state = AccessoryState(
            room_name="Room",
            accessory_name="Dimmer",
            action="a",
            output_state="OFF",
            dimming_state="-",
            module_name="A01",
            serial_number="1234567890",
            module_type="XP33LED",
            error_status="OK",
            output=1,
            sort=1,
        )
        result = widget._format_dim(state)
        assert result == "-"

    def test_format_dim_dimmable_on_empty(self, widget):
        """Test _format_dim returns empty when dimming_state is empty."""
        state = AccessoryState(
            room_name="Room",
            accessory_name="Dimmer",
            action="a",
            output_state="ON",
            dimming_state="",
            module_name="A01",
            serial_number="1234567890",
            module_type="XP33LED",
            error_status="OK",
            output=1,
            sort=1,
        )
        result = widget._format_dim(state)
        assert result == ""

    def test_format_last_update_none(self, widget):
        """Test _format_last_update returns placeholder for None."""
        result = widget._format_last_update(None)
        assert result == "--:--:--"

    def test_format_last_update_recent(self, widget):
        """Test _format_last_update formats recent time correctly."""
        # 1 hour, 30 minutes, 45 seconds ago
        last_update = datetime.now() - timedelta(hours=1, minutes=30, seconds=45)
        result = widget._format_last_update(last_update)
        assert result == "01:30:45"

    def test_format_last_update_zero(self, widget):
        """Test _format_last_update for just now."""
        last_update = datetime.now()
        result = widget._format_last_update(last_update)
        assert result == "00:00:00"

    def test_format_last_update_hours(self, widget):
        """Test _format_last_update with many hours."""
        last_update = datetime.now() - timedelta(hours=25, minutes=5, seconds=10)
        result = widget._format_last_update(last_update)
        assert result == "25:05:10"

    def test_cleanup_on_unmount(self, widget, mock_service):
        """Test on_unmount disconnects signals from service."""
        widget.on_unmount()

        mock_service.on_room_list_updated.disconnect.assert_called_once()
        mock_service.on_module_state_changed.disconnect.assert_called_once()

    def test_cleanup_on_unmount_no_service(self):
        """Test on_unmount handles no service gracefully."""
        widget = RoomListWidget(service=None)
        # Should not raise exception
        widget.on_unmount()

    def test_update_accessory_list_no_table(self, widget, accessory_state):
        """Test update_accessory_list handles no table gracefully."""
        widget.table = None
        # Should not raise exception
        widget.update_accessory_list([accessory_state])

    def test_update_accessory_state_no_table(self, widget, accessory_state):
        """Test update_accessory_state handles no table gracefully."""
        widget.table = None
        # Should not raise exception
        widget.update_accessory_state(accessory_state)

    def test_add_accessory_row_no_table(self, widget, accessory_state):
        """Test _add_accessory_row handles no table gracefully."""
        widget.table = None
        # Should not raise exception
        widget._add_accessory_row(accessory_state)

    def test_refresh_last_update_times_no_table(self, widget):
        """Test refresh_last_update_times handles no table gracefully."""
        widget.table = None
        # Should not raise exception
        widget.refresh_last_update_times()

    def test_refresh_last_update_times_no_service(self):
        """Test refresh_last_update_times handles no service gracefully."""
        widget = RoomListWidget(service=None)
        widget.table = Mock()
        # Should not raise exception
        widget.refresh_last_update_times()

    def test_update_accessory_list_with_mock_table(self, widget, accessory_state):
        """Test update_accessory_list clears and populates table."""
        mock_table = Mock()
        mock_table.add_row = Mock(return_value="row_key_1")
        widget.table = mock_table

        widget.update_accessory_list([accessory_state])

        mock_table.clear.assert_called_once()
        # add_row should be called multiple times (room header + accessory)
        assert mock_table.add_row.call_count >= 1

    def test_update_accessory_list_groups_by_room(self, widget):
        """Test update_accessory_list groups accessories by room."""
        mock_table = Mock()
        mock_table.add_row = Mock(return_value="row_key")
        widget.table = mock_table

        states = [
            AccessoryState(
                room_name="Room A",
                accessory_name="Light 1",
                action="a",
                output_state="ON",
                dimming_state="",
                module_name="A01",
                serial_number="1234567890",
                module_type="XP24",
                error_status="OK",
                output=1,
                sort=1,
            ),
            AccessoryState(
                room_name="Room A",
                accessory_name="Light 2",
                action="b",
                output_state="OFF",
                dimming_state="",
                module_name="A01",
                serial_number="1234567890",
                module_type="XP24",
                error_status="OK",
                output=2,
                sort=2,
            ),
            AccessoryState(
                room_name="Room B",
                accessory_name="Light 3",
                action="c",
                output_state="ON",
                dimming_state="",
                module_name="A02",
                serial_number="2222222222",
                module_type="XP24",
                error_status="OK",
                output=1,
                sort=3,
            ),
        ]

        widget.update_accessory_list(states)

        # Should have multiple rows: room headers + accessories
        assert mock_table.add_row.call_count >= 3

    def test_update_accessory_state_existing(self, widget, accessory_state):
        """Test update_accessory_state updates existing row."""
        mock_table = Mock()
        widget.table = mock_table
        widget._row_keys = {"A01_1": "existing_row_key"}

        widget.update_accessory_state(accessory_state)

        # Should update cells, not add new row
        assert mock_table.update_cell.call_count == 4  # state, dim, status, updated
        mock_table.add_row.assert_not_called()

    def test_update_accessory_state_new(self, widget, accessory_state):
        """Test update_accessory_state adds new row for unknown accessory."""
        mock_table = Mock()
        mock_table.add_row = Mock(return_value="new_row_key")
        widget.table = mock_table
        widget._row_keys = {}  # No existing rows

        widget.update_accessory_state(accessory_state)

        mock_table.add_row.assert_called_once()
        assert "A01_1" in widget._row_keys

    def test_refresh_last_update_times_updates_cells(self, widget, mock_service):
        """Test refresh_last_update_times updates time cells."""
        mock_table = Mock()
        widget.table = mock_table
        widget._row_keys = {"A01_1": "row_key_1"}

        state = AccessoryState(
            room_name="Room",
            accessory_name="Light",
            action="a",
            output_state="ON",
            dimming_state="",
            module_name="A01",
            serial_number="1234567890",
            module_type="XP24",
            error_status="OK",
            output=1,
            sort=1,
            last_update=datetime.now() - timedelta(minutes=5),
        )
        mock_service.accessory_states = [state]

        widget.refresh_last_update_times()

        mock_table.update_cell.assert_called_once()
