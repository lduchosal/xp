"""Unit tests for HomekitApp."""

from unittest.mock import AsyncMock, Mock

import pytest

from xp.term.homekit import HomekitApp


class TestHomekitApp:
    """Unit tests for HomekitApp functionality."""

    @pytest.fixture
    def mock_service(self):
        """Create a mock HomekitService."""
        service = Mock()
        service.on_connection_state_changed = Mock()
        service.on_connection_state_changed.connect = Mock()
        service.on_connection_state_changed.disconnect = Mock()
        service.on_room_list_updated = Mock()
        service.on_room_list_updated.connect = Mock()
        service.on_room_list_updated.disconnect = Mock()
        service.on_module_state_changed = Mock()
        service.on_module_state_changed.connect = Mock()
        service.on_module_state_changed.disconnect = Mock()
        service.on_status_message = Mock()
        service.on_status_message.connect = Mock()
        service.on_status_message.disconnect = Mock()
        service.connect = Mock()
        service.disconnect = Mock()
        service.toggle_connection = Mock()
        service.toggle_accessory = Mock(return_value=True)
        service.refresh_all = Mock()
        service.cleanup = Mock()
        service.connection_state = Mock()
        service.server_info = "192.168.1.100:10001"
        return service

    @pytest.fixture
    def app(self, mock_service):
        """Create app instance with mock service."""
        return HomekitApp(homekit_service=mock_service)

    def test_app_initialization(self, app, mock_service):
        """Test app can be initialized with required dependencies."""
        assert app.homekit_service == mock_service
        assert app.room_list_widget is None
        assert app.footer_widget is None

    def test_app_title(self, app):
        """Test app has correct title."""
        assert app.TITLE == "HomeKit"

    def test_app_bindings(self, app):
        """Test app has correct key bindings."""
        binding_keys = [b[0] for b in app.BINDINGS]
        assert "Q" in binding_keys
        assert "C" in binding_keys
        assert "r" in binding_keys

    def test_action_toggle_connection(self, app, mock_service):
        """Test action_toggle_connection calls service method."""
        app.action_toggle_connection()
        mock_service.toggle_connection.assert_called_once()

    def test_action_refresh_all(self, app, mock_service):
        """Test action_refresh_all calls service method."""
        app.action_refresh_all()
        mock_service.refresh_all.assert_called_once()

    def test_on_key_action_key(self, app, mock_service):
        """Test on_key handles action keys a-z."""
        mock_event = Mock()
        mock_event.key = "a"

        app.on_key(mock_event)

        mock_service.toggle_accessory.assert_called_once_with("a")
        mock_event.prevent_default.assert_called_once()

    def test_on_key_action_key_uppercase(self, app, mock_service):
        """Test on_key handles uppercase action keys."""
        mock_event = Mock()
        mock_event.key = "A"

        app.on_key(mock_event)

        mock_service.toggle_accessory.assert_called_once_with("a")

    def test_on_key_action_key_not_found(self, app, mock_service):
        """Test on_key does not prevent default when key not found."""
        mock_service.toggle_accessory.return_value = False
        mock_event = Mock()
        mock_event.key = "z"

        app.on_key(mock_event)

        mock_event.prevent_default.assert_not_called()

    def test_on_key_non_action_key(self, app, mock_service):
        """Test on_key ignores non-action keys (symbols, punctuation)."""
        mock_event = Mock()
        mock_event.key = "@"  # Not an action key (a-z0-9)

        app.on_key(mock_event)

        mock_service.toggle_accessory.assert_not_called()

    def test_on_key_special_key(self, app, mock_service):
        """Test on_key ignores special keys."""
        mock_event = Mock()
        mock_event.key = "enter"

        app.on_key(mock_event)

        mock_service.toggle_accessory.assert_not_called()

    @pytest.mark.asyncio
    async def test_on_unmount_cleanup(self, app, mock_service):
        """Test on_unmount calls service stop."""
        mock_service.stop = AsyncMock()
        await app.on_unmount()
        mock_service.stop.assert_called_once()

    def test_refresh_last_update_column_with_widget(self, app, mock_service):
        """Test _refresh_last_update_column calls widget method."""
        mock_widget = Mock()
        app.room_list_widget = mock_widget

        app._refresh_last_update_column()

        mock_widget.refresh_last_update_times.assert_called_once()

    def test_refresh_last_update_column_no_widget(self, app):
        """Test _refresh_last_update_column handles no widget gracefully."""
        app.room_list_widget = None
        # Should not raise exception
        app._refresh_last_update_column()

    def test_css_path_exists(self, app):
        """Test CSS path is set."""
        assert app.CSS_PATH is not None
        assert app.CSS_PATH.name == "homekit.tcss"

    def test_command_palette_disabled(self, app):
        """Test command palette is disabled."""
        assert app.ENABLE_COMMAND_PALETTE is False
