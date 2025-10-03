"""Dependency injection container for XP services."""

import punq

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
from xp.services.homekit.homekit_cache_service import HomeKitCacheService
from xp.services.homekit.homekit_module_service import HomekitModuleService
from xp.services.homekit.homekit_service import HomekitService
from xp.services.reverse_proxy_service import ReverseProxyService
from xp.services.server.server_service import ServerService
from xp.services.telegram.telegram_blink_service import TelegramBlinkService
from xp.services.telegram.telegram_discover_service import TelegramDiscoverService
from xp.services.telegram.telegram_output_service import TelegramOutputService
from xp.services.telegram.telegram_service import TelegramService


class ServiceContainer:
    """
    Service container that manages dependency injection for all XP services.

    Uses the service dependency graph from Service-Dependencies.dot to properly
    wire up all services with their dependencies.
    """

    def __init__(
        self,
        config_path: str = "cli.yml",
        homekit_config_path: str = "homekit.yml",
        conson_config_path: str = "conson.yml",
        cache_file: str = ".homekit_cache.json",
        server_port: int = 10001,
        reverse_proxy_port: int = 10001,
    ):
        """
        Initialize the service container.

        Args:
            config_path: Path to the Conbus CLI configuration file
            homekit_config_path: Path to the HomeKit configuration file
            conson_config_path: Path to the Conson configuration file
            cache_file: Path to the HomeKit cache file
            server_port: Port for the server service
            reverse_proxy_port: Port for the reverse proxy service
        """
        self.container = punq.Container()
        self._config_path = config_path
        self._homekit_config_path = homekit_config_path
        self._conson_config_path = conson_config_path
        self._cache_file = cache_file
        self._server_port = server_port
        self._reverse_proxy_port = reverse_proxy_port

        self._register_services()

    def _register_services(self) -> None:
        """Register all services in the container based on dependency graph."""

        # Core infrastructure layer - ConbusConnectionPool (singleton)
        self.container.register(
            ConbusConnectionPool,
            instance=ConbusConnectionPool.get_instance(),
            scope=punq.Scope.singleton,
        )

        # Telegram services layer - no dependencies
        self.container.register(TelegramService, scope=punq.Scope.singleton)
        self.container.register(TelegramOutputService, scope=punq.Scope.singleton)
        self.container.register(TelegramDiscoverService, scope=punq.Scope.singleton)
        self.container.register(TelegramBlinkService, scope=punq.Scope.singleton)

        # ConbusService - depends on ConbusConnectionPool
        self.container.register(
            ConbusService,
            factory=lambda: ConbusService(self._config_path),
            scope=punq.Scope.singleton,
        )

        # Conbus services layer
        self.container.register(
            ConbusDatapointService,
            factory=lambda: ConbusDatapointService(self._config_path),
            scope=punq.Scope.singleton,
        )

        self.container.register(
            ConbusScanService,
            factory=lambda: ConbusScanService(self._config_path),
            scope=punq.Scope.singleton,
        )

        self.container.register(
            ConbusDiscoverService,
            factory=lambda: ConbusDiscoverService(self._config_path),
            scope=punq.Scope.singleton,
        )

        self.container.register(
            ConbusBlinkService,
            factory=lambda: ConbusBlinkService(self._config_path),
            scope=punq.Scope.singleton,
        )

        self.container.register(
            ConbusOutputService,
            factory=lambda: ConbusOutputService(self._config_path),
            scope=punq.Scope.singleton,
        )

        self.container.register(
            ConbusLightlevelService,
            factory=lambda: ConbusLightlevelService(self._config_path),
            scope=punq.Scope.singleton,
        )

        self.container.register(
            ActionTableService,
            factory=lambda: ActionTableService(self._config_path),
            scope=punq.Scope.singleton,
        )

        self.container.register(
            MsActionTableService,
            factory=lambda: MsActionTableService(self._config_path),
            scope=punq.Scope.singleton,
        )

        # HomeKit services layer
        self.container.register(
            HomekitModuleService,
            factory=lambda: HomekitModuleService(self._conson_config_path),
            scope=punq.Scope.singleton,
        )

        self.container.register(
            HomeKitCacheService,
            factory=lambda: HomeKitCacheService(self._config_path, self._cache_file),
            scope=punq.Scope.singleton,
        )

        self.container.register(
            HomekitService,
            factory=lambda: HomekitService(
                self._homekit_config_path, self._conson_config_path
            ),
            scope=punq.Scope.singleton,
        )

        # Server services layer
        self.container.register(
            ServerService,
            factory=lambda: ServerService(self._config_path, self._server_port),
            scope=punq.Scope.singleton,
        )

        # Other services
        self.container.register(
            ReverseProxyService,
            factory=lambda: ReverseProxyService(
                self._config_path, self._reverse_proxy_port
            ),
            scope=punq.Scope.singleton,
        )

    def get_container(self) -> punq.Container:
        """
        Get the configured container with all services registered.

        Returns:
            punq.Container: The configured dependency injection container
        """
        return self.container
