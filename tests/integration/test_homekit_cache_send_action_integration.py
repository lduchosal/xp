"""Integration tests for HomeKitCacheService send_action method."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from xp.models.action_type import ActionType
from xp.models.event_telegram import EventTelegram
from xp.services.homekit_cache_service import HomeKitCacheService


class TestHomeKitCacheServiceSendActionIntegration:
    """Integration tests for HomeKitCacheService send_action method."""

    def setup_method(self):
        """Setup test fixtures"""
        # Use temporary file for cache during tests
        self.temp_cache_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
        self.temp_cache_file.close()

    def teardown_method(self):
        """Cleanup test fixtures"""
        # Clean up temporary cache file
        Path(self.temp_cache_file.name).unlink(missing_ok=True)

    @patch("xp.services.homekit_cache_service.ConbusOutputService")
    @patch("xp.services.homekit_cache_service.TelegramService")
    def test_send_action_with_event_telegram_integration(
        self, mock_telegram_service_class, mock_conbus_service_class
    ):
        """Integration test for send_action method when receiving EventTelegram."""
        # Setup mocks
        mock_conbus_service = Mock()
        mock_conbus_service_class.return_value = mock_conbus_service

        mock_telegram_service = Mock()
        mock_telegram_service_class.return_value = mock_telegram_service

        # Create mock response with received telegrams (strings, not objects)
        mock_response = Mock()
        mock_response.success = True
        mock_response.received_telegrams = ["<E14L01I02MAK>"]
        mock_conbus_service.send_action.return_value = mock_response

        # Create mock event telegram
        mock_event_telegram = Mock(spec=EventTelegram)
        mock_event_telegram.raw_telegram = "<E14L01I02MAK>"
        mock_telegram_service.parse_event_telegram.return_value = mock_event_telegram

        # Initialize cache service
        cache_service = HomeKitCacheService(cache_file=self.temp_cache_file.name)

        # Mock the received_event method to track calls
        with patch.object(cache_service, "received_event") as mock_received_event:
            # Call send_action
            cache_service.send_action("2113010000", 1, ActionType.OFF_PRESS)

            # Verify conbus service was called correctly
            mock_conbus_service.send_action.assert_called_once_with(
                "2113010000", 1, ActionType.OFF_PRESS
            )

            # Verify telegram service parsed the raw telegram
            mock_telegram_service.parse_event_telegram.assert_called_once_with(
                "<E14L01I02MAK>"
            )

            # Verify received_event was called with raw telegram
            mock_received_event.assert_called_once_with("<E14L01I02MAK>")

    @patch("xp.services.homekit_cache_service.ConbusOutputService")
    @patch("xp.services.homekit_cache_service.TelegramService")
    def test_send_action_with_event_telegram_integration_2(
        self, mock_telegram_service_class, mock_conbus_service_class
    ):
        """Integration test for send_action method when receiving EventTelegram."""
        # Setup mocks
        mock_conbus_service = Mock()
        mock_conbus_service_class.return_value = mock_conbus_service

        mock_telegram_service = Mock()
        mock_telegram_service_class.return_value = mock_telegram_service

        # Create mock event telegram
        mock_event_telegram = Mock(spec=EventTelegram)
        mock_event_telegram.raw_telegram = "<E14L01I02MAK>"

        # Configure mock to raise exception for reply telegram, success for event telegram
        from xp.services import TelegramParsingError

        def side_effect(telegram):
            if telegram == "<R2113010000E18DFJ>":
                raise TelegramParsingError("Not an event telegram")
            elif telegram == "<E14L01I02MAK>":
                return mock_event_telegram
            else:
                raise TelegramParsingError("Unknown telegram")

        mock_telegram_service.parse_event_telegram.side_effect = side_effect

        # Create mock response with received telegrams (strings, not objects)
        mock_response = Mock()
        mock_response.success = True
        mock_response.received_telegrams = [
            "<R2113010000E18DFJ>",
            "<E14L01I02MAK>",
        ]
        mock_conbus_service.send_action.return_value = mock_response

        # Initialize cache service
        cache_service = HomeKitCacheService(cache_file=self.temp_cache_file.name)

        # Mock the received_event method to track calls
        with patch.object(cache_service, "received_event") as mock_received_event:
            # Call send_action
            cache_service.send_action("2113010000", 1, ActionType.OFF_PRESS)

            # Verify conbus service was called correctly
            mock_conbus_service.send_action.assert_called_once_with(
                "2113010000", 1, ActionType.OFF_PRESS
            )

            # Verify received_event was called with raw telegram
            mock_received_event.assert_called_once_with("<E14L01I02MAK>")

    @patch("xp.services.homekit_cache_service.ConbusOutputService")
    @patch("xp.services.homekit_cache_service.TelegramService")
    def test_send_action_failed_response_integration(
        self, mock_telegram_service_class, mock_conbus_service_class
    ):
        """Integration test for send_action method when conbus response fails."""
        # Setup mocks
        mock_conbus_service = Mock()
        mock_conbus_service_class.return_value = mock_conbus_service

        mock_telegram_service = Mock()
        mock_telegram_service_class.return_value = mock_telegram_service

        # Create mock failed response
        mock_response = Mock()
        mock_response.success = False
        mock_response.received_telegrams = None
        mock_conbus_service.send_action.return_value = mock_response

        # Initialize cache service
        cache_service = HomeKitCacheService(cache_file=self.temp_cache_file.name)

        # Mock the received_event method to track calls
        with patch.object(cache_service, "received_event") as mock_received_event:
            # Call send_action
            cache_service.send_action("2113010000", 1, ActionType.OFF_PRESS)

            # Verify conbus service was called correctly
            mock_conbus_service.send_action.assert_called_once_with(
                "2113010000", 1, ActionType.OFF_PRESS
            )

            # Verify telegram service was not called since response failed
            mock_telegram_service.parse_telegram.assert_not_called()

            # Verify received_event was not called
            mock_received_event.assert_not_called()

    @patch("xp.services.homekit_cache_service.ConbusOutputService")
    @patch("xp.services.homekit_cache_service.TelegramService")
    def test_send_action_no_received_telegrams_integration(
        self, mock_telegram_service_class, mock_conbus_service_class
    ):
        """Integration test for send_action method when no telegrams are received."""
        # Setup mocks
        mock_conbus_service = Mock()
        mock_conbus_service_class.return_value = mock_conbus_service

        mock_telegram_service = Mock()
        mock_telegram_service_class.return_value = mock_telegram_service

        # Create mock response with no received telegrams
        mock_response = Mock()
        mock_response.success = True
        mock_response.received_telegrams = []
        mock_conbus_service.send_action.return_value = mock_response

        # Initialize cache service
        cache_service = HomeKitCacheService(cache_file=self.temp_cache_file.name)

        # Mock the received_event method to track calls
        with patch.object(cache_service, "received_event") as mock_received_event:
            # Call send_action
            cache_service.send_action("2113010000", 1, ActionType.OFF_PRESS)

            # Verify conbus service was called correctly
            mock_conbus_service.send_action.assert_called_once_with(
                "2113010000", 1, ActionType.OFF_PRESS
            )

            # Verify telegram service was not called since no telegrams received
            mock_telegram_service.parse_telegram.assert_not_called()

            # Verify received_event was not called
            mock_received_event.assert_not_called()
