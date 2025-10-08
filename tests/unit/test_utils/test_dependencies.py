"""Unit tests for dependency injection container.

Tests the ServiceContainer class to ensure all services are properly
registered and can be resolved with their dependencies.
"""

import pytest

from xp.services.conbus.actiontable.actiontable_service import ActionTableService
from xp.services.conbus.actiontable.msactiontable_service import MsActionTableService
from xp.services.conbus.conbus_blink_service import ConbusBlinkService
from xp.services.conbus.conbus_connection_pool import ConbusConnectionPool
from xp.services.conbus.conbus_datapoint_service import ConbusDatapointService
from xp.services.conbus.conbus_discover_service import ConbusDiscoverService
from xp.services.conbus.conbus_lightlevel_service import ConbusLightlevelService
from xp.services.conbus.conbus_output_service import ConbusOutputService
from xp.services.conbus.conbus_scan_service import ConbusScanService
from xp.services.conbus.conbus_service import ConbusService
from xp.services.homekit.homekit_hap_service import HomekitHapService
from xp.services.homekit.homekit_module_service import HomekitModuleService
from xp.services.reverse_proxy_service import ReverseProxyService
from xp.services.server.server_service import ServerService
from xp.services.telegram.telegram_blink_service import TelegramBlinkService
from xp.services.telegram.telegram_discover_service import TelegramDiscoverService
from xp.services.telegram.telegram_output_service import TelegramOutputService
from xp.services.telegram.telegram_service import TelegramService
from xp.utils.dependencies import ServiceContainer


class TestServiceContainer:
    """Test class for ServiceContainer dependency injection."""

    def test_container_creation(self):
        """Test basic container creation."""
        container = ServiceContainer()
        assert container is not None
        assert container.container is not None

    def test_get_container_returns_punq_container(self):
        """Test get_container returns a punq Container instance."""
        container = ServiceContainer().get_container()
        assert container is not None

    def test_custom_configuration_paths(self):
        """Test container creation with custom configuration paths."""
        container = ServiceContainer(
            config_path="custom-cli.yml",
            homekit_config_path="custom-homekit.yml",
            conson_config_path="custom-conson.yml",
            server_port=8080,
            reverse_proxy_port=9090,
        )
        assert container is not None
        assert container._config_path == "custom-cli.yml"
        assert container._homekit_config_path == "custom-homekit.yml"
        assert container._conson_config_path == "custom-conson.yml"
        assert container._server_port == 8080
        assert container._reverse_proxy_port == 9090

    # Test resolving core infrastructure services
    def test_resolve_conbus_connection_pool(self):
        """Test resolving ConbusConnectionPool (singleton)."""
        container = ServiceContainer().get_container()

        service1 = container.resolve(ConbusConnectionPool)
        service2 = container.resolve(ConbusConnectionPool)

        assert isinstance(service1, ConbusConnectionPool)
        # Verify singleton - same instance returned
        assert service1 is service2

    # Test resolving telegram services
    def test_resolve_telegram_service(self):
        """Test resolving TelegramService."""
        service = ServiceContainer().get_container().resolve(TelegramService)
        assert isinstance(service, TelegramService)

    def test_resolve_telegram_output_service(self):
        """Test resolving TelegramOutputService."""
        service = ServiceContainer().get_container().resolve(TelegramOutputService)
        assert isinstance(service, TelegramOutputService)

    def test_resolve_telegram_discover_service(self):
        """Test resolving TelegramDiscoverService."""
        service = ServiceContainer().get_container().resolve(TelegramDiscoverService)
        assert isinstance(service, TelegramDiscoverService)

    def test_resolve_telegram_blink_service(self):
        """Test resolving TelegramBlinkService."""
        service = ServiceContainer().get_container().resolve(TelegramBlinkService)
        assert isinstance(service, TelegramBlinkService)

    # Test resolving conbus services
    def test_resolve_conbus_service(self):
        """Test resolving ConbusService."""
        service = ServiceContainer().get_container().resolve(ConbusService)
        assert isinstance(service, ConbusService)

    def test_resolve_conbus_datapoint_service(self):
        """Test resolving ConbusDatapointService."""
        service = ServiceContainer().get_container().resolve(ConbusDatapointService)
        assert isinstance(service, ConbusDatapointService)

    def test_resolve_conbus_scan_service(self):
        """Test resolving ConbusScanService."""
        service = ServiceContainer().get_container().resolve(ConbusScanService)
        assert isinstance(service, ConbusScanService)

    def test_resolve_conbus_discover_service(self):
        """Test resolving ConbusDiscoverService."""
        service = ServiceContainer().get_container().resolve(ConbusDiscoverService)
        assert isinstance(service, ConbusDiscoverService)

    def test_resolve_conbus_blink_service(self):
        """Test resolving ConbusBlinkService."""
        service = ServiceContainer().get_container().resolve(ConbusBlinkService)
        assert isinstance(service, ConbusBlinkService)

    def test_resolve_conbus_output_service(self):
        """Test resolving ConbusOutputService."""
        service = ServiceContainer().get_container().resolve(ConbusOutputService)
        assert isinstance(service, ConbusOutputService)

    def test_resolve_conbus_lightlevel_service(self):
        """Test resolving ConbusLightlevelService."""
        service = ServiceContainer().get_container().resolve(ConbusLightlevelService)
        assert isinstance(service, ConbusLightlevelService)

    def test_resolve_actiontable_service(self):
        """Test resolving ActionTableService."""
        service = ServiceContainer().get_container().resolve(ActionTableService)
        assert isinstance(service, ActionTableService)

    def test_resolve_msactiontable_service(self):
        """Test resolving MsActionTableService."""
        service = ServiceContainer().get_container().resolve(MsActionTableService)
        assert isinstance(service, MsActionTableService)

    # Test resolving homekit services
    def test_resolve_homekit_module_service(self):
        """Test resolving HomekitModuleService."""
        service = ServiceContainer().get_container().resolve(HomekitModuleService)
        assert isinstance(service, HomekitModuleService)

    def test_resolve_homekit_service(self):
        """Test resolving HomekitService."""
        service = ServiceContainer().get_container().resolve(HomekitHapService)
        assert isinstance(service, HomekitHapService)

    # Test resolving server services
    def test_resolve_server_service(self):
        """Test resolving ServerService."""
        service = ServiceContainer().get_container().resolve(ServerService)
        assert isinstance(service, ServerService)

    # Test resolving other services
    def test_resolve_reverse_proxy_service(self):
        """Test resolving ReverseProxyService."""
        service = ServiceContainer().get_container().resolve(ReverseProxyService)
        assert isinstance(service, ReverseProxyService)

    # Test singleton scope
    def test_telegram_services_are_singletons(self):
        """Test that telegram services are registered as singletons."""
        container = ServiceContainer().get_container()

        # Resolve twice and verify same instance
        service1 = container.resolve(TelegramService)
        service2 = container.resolve(TelegramService)
        assert service1 is service2

    def test_conbus_service_is_singleton(self):
        """Test that ConbusService is registered as singleton."""
        container = ServiceContainer().get_container()

        service1 = container.resolve(ConbusService)
        service2 = container.resolve(ConbusService)
        assert service1 is service2

    @pytest.mark.parametrize(
        "service_class",
        [
            TelegramService,
            TelegramOutputService,
            TelegramDiscoverService,
            TelegramBlinkService,
            ConbusConnectionPool,
            ConbusService,
            ConbusDatapointService,
            ConbusScanService,
            ConbusDiscoverService,
            ConbusBlinkService,
            ConbusOutputService,
            ConbusLightlevelService,
            ActionTableService,
            MsActionTableService,
            HomekitModuleService,
            HomekitHapService,
            ServerService,
            ReverseProxyService,
        ],
    )
    def test_all_services_resolvable(self, service_class):
        """Test that all services can be resolved from container."""
        service = ServiceContainer().get_container().resolve(service_class)
        assert isinstance(service, service_class)

    @pytest.mark.parametrize(
        "service_class",
        [
            TelegramService,
            ConbusService,
            ConbusDatapointService,
            ActionTableService,
        ],
    )
    def test_services_are_singletons(self, service_class):
        """Test that multiple resolutions return same instance (singleton)."""
        container = ServiceContainer().get_container()

        service1 = container.resolve(service_class)
        service2 = container.resolve(service_class)
        assert service1 is service2

    def test_multiple_containers_independent(self):
        """Test that multiple ServiceContainers are independent."""
        container1 = ServiceContainer(config_path="cli1.yml")
        container2 = ServiceContainer(config_path="cli2.yml")

        assert container1 is not container2
        assert container1.container is not container2.container
        assert container1._config_path != container2._config_path
