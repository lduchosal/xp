import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import yaml

from xp.services.homekit_module_service import HomekitModuleService


class TestHomekitModuleServiceIntegration:
    """Integration tests for HomekitModuleService."""

    @staticmethod
    def create_temp_conson_config():
        """Create a temporary conson.yml file for testing."""
        config_data = [
            {
                "name": "TestModule",
                "serial_number": "1234567890",
                "module_type": "XP24",
                "module_type_code": 14,
                "link_number": 1,
                "module_number": 1,
                "conbus_ip": "192.168.1.100",
                "conbus_port": 10001,
            }
        ]

        temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False)
        yaml.dump(config_data, temp_file, default_flow_style=False)
        temp_file.close()
        return temp_file.name

    @patch("xp.services.homekit_module_service.HomeKitCacheService")
    @patch("xp.services.homekit_module_service.TelegramOutputService")
    def test_on_accessory_get_on_integration(
        self, mock_telegram_service, mock_cache_service
    ):
        """Integration test for _on_accessory_get_on method."""
        # Create temporary config
        config_path = self.create_temp_conson_config()

        try:
            # Mock the cache service response
            mock_cache_instance = Mock()
            mock_cache_service.return_value = mock_cache_instance

            mock_response = Mock()
            mock_response.data = "test_telegram_data"
            mock_cache_instance.get.return_value = mock_response

            # Mock the telegram output service
            mock_telegram_instance = Mock()
            mock_telegram_service.return_value = mock_telegram_instance
            mock_telegram_instance.parse_status_response.return_value = {
                1: True,
                2: False,
                3: True,
            }

            # Initialize service
            service = HomekitModuleService(config_path)

            # Test valid request
            result = service._on_accessory_get_on(
                sender=None, serial_number="1234567890", output_number=1
            )

            # Verify result
            assert result is True

            # Verify cache service was called with correct parameters
            mock_cache_instance.get.assert_called_once_with(
                key="1234567890", tag="E14L01"
            )

            # Verify telegram service was called
            mock_telegram_instance.parse_status_response.assert_called_once_with(
                "test_telegram_data"
            )

        finally:
            # Cleanup
            if Path(config_path).exists():
                Path(config_path).unlink()
