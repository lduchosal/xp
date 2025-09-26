"""Integration tests for cache command functionality and HomeKit cache service."""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from click.testing import CliRunner

from xp.cli.main import cli
from xp.models import ConbusDatapointResponse
from xp.models.reply_telegram import ReplyTelegram
from xp.services.homekit_cache_service import HomeKitCacheService


class TestCacheIntegration:
    """Integration tests for cache command functionality"""

    def setup_method(self):
        """Setup test fixtures"""
        self.runner = CliRunner()
        # Use temporary file for cache during tests
        self.temp_cache_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
        self.temp_cache_file.close()

    def teardown_method(self):
        """Cleanup test fixtures"""
        # Clean up temporary cache file
        Path(self.temp_cache_file.name).unlink(missing_ok=True)

    def test_cache_set_command(self):
        """Test cache set command"""
        with patch(
            "xp.cli.commands.cache_commands.HomeKitCacheService"
        ) as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service

            result = self.runner.invoke(
                cli, ["cache", "set", "2113010000", "output_state", "ON"]
            )

            assert result.exit_code == 0
            mock_service.set.assert_called_once_with("2113010000", "output_state", "ON")

            # Parse JSON output
            output = json.loads(result.output)
            assert output["success"] is True
            assert output["key"] == "2113010000"
            assert output["tag"] == "output_state"
            assert output["data"] == "ON"

    def test_cache_get_hit(self):
        """Test cache get command with cache hit"""
        with patch(
            "xp.cli.commands.cache_commands.HomeKitCacheService"
        ) as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service

            # Mock cache hit response
            from xp.models.cache import CacheResponse

            mock_response = CacheResponse(data="ON", hit=True)
            mock_service.get.return_value = mock_response

            result = self.runner.invoke(
                cli, ["cache", "get", "2113010000", "output_state"]
            )

            assert result.exit_code == 0
            mock_service.get.assert_called_once_with("2113010000", "output_state")

            # Parse JSON output
            output = json.loads(result.output)
            assert output["key"] == "2113010000"
            assert output["tag"] == "output_state"
            assert output["hit"] is True
            assert output["data"] == "ON"

    def test_cache_get_miss(self):
        """Test cache get command with cache miss and device query"""
        with patch(
            "xp.cli.commands.cache_commands.HomeKitCacheService"
        ) as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service

            # Mock cache miss response
            from xp.models.cache import CacheResponse

            mock_response = CacheResponse(data="OFF", hit=False)
            mock_service.get.return_value = mock_response

            result = self.runner.invoke(
                cli, ["cache", "get", "2113010000", "output_state"]
            )

            assert result.exit_code == 0
            mock_service.get.assert_called_once_with("2113010000", "output_state")

            # Parse JSON output
            output = json.loads(result.output)
            assert output["key"] == "2113010000"
            assert output["tag"] == "output_state"
            assert output["hit"] is False
            assert output["data"] == "OFF"

    def test_cache_get_error(self):
        """Test cache get command with error response"""
        with patch(
            "xp.cli.commands.cache_commands.HomeKitCacheService"
        ) as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service

            # Mock error response
            from xp.models.cache import CacheResponse

            mock_response = CacheResponse(
                data=None, hit=False, error="Device not found"
            )
            mock_service.get.return_value = mock_response

            result = self.runner.invoke(
                cli, ["cache", "get", "invalid_device", "output_state"]
            )

            assert result.exit_code == 0
            mock_service.get.assert_called_once_with("invalid_device", "output_state")

            # Parse JSON output
            output = json.loads(result.output)
            assert output["key"] == "invalid_device"
            assert output["hit"] is False
            assert output["error"] == "Device not found"

    def test_cache_clear_specific_key(self):
        """Test cache clear command for specific key"""
        with patch(
            "xp.cli.commands.cache_commands.HomeKitCacheService"
        ) as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service

            result = self.runner.invoke(cli, ["cache", "clear", "2113010000"])

            assert result.exit_code == 0
            mock_service.clear.assert_called_once_with("2113010000")

            # Parse JSON output
            output = json.loads(result.output)
            assert output["success"] is True
            assert output["cleared"] == "2113010000"

    def test_cache_clear_all(self):
        """Test cache clear command for entire cache"""
        with patch(
            "xp.cli.commands.cache_commands.HomeKitCacheService"
        ) as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service

            result = self.runner.invoke(cli, ["cache", "clear", "all"])

            assert result.exit_code == 0
            mock_service.clear.assert_called_once_with()

            # Parse JSON output
            output = json.loads(result.output)
            assert output["success"] is True
            assert output["cleared"] == "all"

    def test_cache_items(self):
        """Test cache items command"""
        with patch(
            "xp.cli.commands.cache_commands.HomeKitCacheService"
        ) as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service

            # Mock cached items
            mock_items = {"2113010000": "ON", "2113010001": "OFF"}
            mock_stats = {"total_entries": 2, "expired_entries": 0, "active_entries": 2}
            mock_service.items.return_value = mock_items
            mock_service.get_cache_stats.return_value = mock_stats

            result = self.runner.invoke(cli, ["cache", "items"])

            assert result.exit_code == 0
            mock_service.items.assert_called_once()
            mock_service.get_cache_stats.assert_called_once()

            # Parse JSON output
            output = json.loads(result.output)
            assert "cached_items" in output
            assert output["cached_items"] == mock_items
            assert "statistics" in output
            assert output["statistics"] == mock_stats
            assert "formatted_output" in output
            assert "- 2113010000 : ON" in output["formatted_output"]

    def test_cache_stats(self):
        """Test cache stats command"""
        with patch(
            "xp.cli.commands.cache_commands.HomeKitCacheService"
        ) as mock_service_class:
            mock_service = Mock()
            mock_service.cache_file = Path("/tmp/test_cache.json")
            mock_service_class.return_value = mock_service

            mock_stats = {"total_entries": 5, "expired_entries": 1, "active_entries": 4}
            mock_service.get_cache_stats.return_value = mock_stats

            result = self.runner.invoke(cli, ["cache", "stats"])

            assert result.exit_code == 0
            mock_service.get_cache_stats.assert_called_once()

            # Parse JSON output
            output = json.loads(result.output)
            assert "cache_statistics" in output
            assert output["cache_statistics"] == mock_stats
            assert "cache_file" in output

    def test_service_cache_functionality(self):
        """Test HomeKitCacheService caching functionality with TTL"""
        # Use real service with temporary cache file
        service = HomeKitCacheService(cache_file=self.temp_cache_file.name)

        # Mock ConbusOutputService to avoid actual device calls
        with patch.object(service, "conbus_output_service") as mock_conbus:
            mock_response = ConbusDatapointResponse(
                success=True,
                datapoint_telegram=ReplyTelegram(
                    checksum="CK", raw_telegram="device_data"
                ),
            )
            mock_conbus.get_output_state.return_value = mock_response

            # Test cache miss - should query device
            response1 = service.get("test_device", "test_tag")
            assert response1.hit is False
            assert response1.data == "device_data"
            mock_conbus.get_output_state.assert_called_once_with("test_device")

            # Test cache hit - should not query device again
            mock_conbus.reset_mock()
            response2 = service.get("test_device", "test_tag")
            assert response2.hit is True
            assert response2.data == "device_data"
            mock_conbus.get_output_state.assert_not_called()

    def test_service_event_invalidation(self):
        """Test event-based cache invalidation"""
        service = HomeKitCacheService(cache_file=self.temp_cache_file.name)

        # Add cache entry manually
        service.set("test_device", "output_state", "ON")

        # Verify entry exists
        items = service.items()
        assert "test_device" in items
        assert items["test_device"] == "ON"

        # Invalidate cache by event
        service.received_event("output_state")

        # Verify entry is removed
        items = service.items()
        assert "test_device" not in items

    def test_service_persistence(self):
        """Test file-based persistence and recovery"""
        # Create first service instance and add data
        service1 = HomeKitCacheService(cache_file=self.temp_cache_file.name)
        service1.set("persistent_device", "test_tag", "persistent_data")

        # Create second service instance and verify data persists
        items = HomeKitCacheService(cache_file=self.temp_cache_file.name).items()
        assert (
            "persistent_device" in items
            and items["persistent_device"] == "persistent_data"
        )

    def test_service_received_update(self):
        """Test received update functionality"""
        service = HomeKitCacheService(cache_file=self.temp_cache_file.name)

        # Add initial cache entry
        service.set("update_device", "status", "initial_value")

        # Update with new data
        service.set("update_device", "status", "updated_value")

        # Verify data is updated
        items = service.items()
        assert items["update_device"] == "updated_value"

    def test_cache_help_command(self):
        """Test cache help command"""
        result = self.runner.invoke(cli, ["cache", "--help"])

        assert result.exit_code == 0
        assert "Cache operations for HomeKit device states" in result.output
        assert "get" in result.output
        assert "set" in result.output
        assert "clear" in result.output
        assert "items" in result.output
        assert "stats" in result.output

    def test_cache_subcommand_help(self):
        """Test cache subcommand help"""
        result = self.runner.invoke(cli, ["cache", "get", "--help"])

        assert result.exit_code == 0
        assert "Get cached data for a device key" in result.output
        assert "Examples:" in result.output
        assert "xp cache get" in result.output
