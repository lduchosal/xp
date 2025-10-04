"""Dependency injection container for XP services."""

import punq

from xp.models import ConbusClientConfig
from xp.models.homekit.homekit_config import HomekitConfig
from xp.models.homekit.homekit_conson_config import ConsonModuleListConfig
from xp.services.conbus.actiontable.actiontable_service import ActionTableService
from xp.services.conbus.actiontable.msactiontable_service import MsActionTableService
from xp.services.conbus.conbus_autoreport_service import ConbusAutoreportService
from xp.services.conbus.conbus_blink_service import ConbusBlinkService
from xp.services.conbus.conbus_connection_pool import (
    ConbusConnectionPool,
    ConbusSocketConnectionManager,
)
from xp.services.conbus.conbus_custom_service import ConbusCustomService
from xp.services.conbus.conbus_datapoint_service import ConbusDatapointService
from xp.services.conbus.conbus_discover_service import ConbusDiscoverService
from xp.services.conbus.conbus_lightlevel_service import ConbusLightlevelService
from xp.services.conbus.conbus_linknumber_service import ConbusLinknumberService
from xp.services.conbus.conbus_output_service import ConbusOutputService
from xp.services.conbus.conbus_raw_service import ConbusRawService
from xp.services.conbus.conbus_receive_service import ConbusReceiveService
from xp.services.conbus.conbus_scan_service import ConbusScanService
from xp.services.conbus.conbus_service import ConbusService
from xp.services.homekit.homekit_cache_service import HomeKitCacheService
from xp.services.homekit.homekit_module_service import HomekitModuleService
from xp.services.homekit.homekit_service import HomekitService
from xp.services.log_file_service import LogFileService
from xp.services.module_type_service import ModuleTypeService
from xp.services.reverse_proxy_service import ReverseProxyService
from xp.services.server.server_service import ServerService
from xp.services.telegram.telegram_blink_service import TelegramBlinkService
from xp.services.telegram.telegram_discover_service import TelegramDiscoverService
from xp.services.telegram.telegram_link_number_service import LinkNumberService
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

        # ConbusClientConfig (needed by ConbusConnectionPool)
        self.container.register(
            ConbusClientConfig,
            factory=lambda: ConbusClientConfig.from_yaml(self._config_path),
            scope=punq.Scope.singleton,
        )

        # Core infrastructure layer - ConbusConnectionPool (singleton)
        self.container.register(
            ConbusSocketConnectionManager,
            factory=lambda: ConbusSocketConnectionManager(
                cli_config=self.container.resolve(ConbusClientConfig)
            ),
            scope=punq.Scope.singleton,
        )

        self.container.register(
            ConbusConnectionPool,
            factory=lambda: ConbusConnectionPool(
                connection_manager=self.container.resolve(ConbusSocketConnectionManager)
            ),
            scope=punq.Scope.singleton,
        )

        # Telegram services layer
        self.container.register(TelegramService, scope=punq.Scope.singleton)
        self.container.register(
            TelegramOutputService,
            factory=lambda: TelegramOutputService(
                telegram_service=self.container.resolve(TelegramService),
            ),
            scope=punq.Scope.singleton,
        )
        self.container.register(TelegramDiscoverService, scope=punq.Scope.singleton)
        self.container.register(TelegramBlinkService, scope=punq.Scope.singleton)
        self.container.register(LinkNumberService, scope=punq.Scope.singleton)

        # ConbusService - depends on ConbusConnectionPool
        self.container.register(
            ConbusService,
            factory=lambda: ConbusService(
                client_config=self.container.resolve(ConbusClientConfig),
                connection_pool=self.container.resolve(ConbusConnectionPool),
            ),
            scope=punq.Scope.singleton,
        )

        # Conbus services layer
        self.container.register(
            ConbusDatapointService,
            factory=lambda: ConbusDatapointService(
                telegram_service=self.container.resolve(TelegramService),
                conbus_service=self.container.resolve(ConbusService),
            ),
            scope=punq.Scope.singleton,
        )

        self.container.register(
            ConbusScanService,
            factory=lambda: ConbusScanService(
                telegram_service=self.container.resolve(TelegramService),
                conbus_service=self.container.resolve(ConbusService),
            ),
            scope=punq.Scope.singleton,
        )

        self.container.register(
            ConbusDiscoverService,
            factory=lambda: ConbusDiscoverService(
                telegram_service=self.container.resolve(TelegramService),
                telegram_discover_service=self.container.resolve(
                    TelegramDiscoverService
                ),
                conbus_service=self.container.resolve(ConbusService),
            ),
            scope=punq.Scope.singleton,
        )

        self.container.register(
            ConbusBlinkService,
            factory=lambda: ConbusBlinkService(
                conbus_service=self.container.resolve(ConbusService),
                discover_service=self.container.resolve(ConbusDiscoverService),
                telegram_blink_service=self.container.resolve(TelegramBlinkService),
                telegram_service=self.container.resolve(TelegramService),
            ),
            scope=punq.Scope.singleton,
        )

        self.container.register(
            ConbusOutputService,
            factory=lambda: ConbusOutputService(
                telegram_service=self.container.resolve(TelegramService),
                telegram_output_service=self.container.resolve(TelegramOutputService),
                datapoint_service=self.container.resolve(ConbusDatapointService),
                conbus_service=self.container.resolve(ConbusService),
            ),
            scope=punq.Scope.singleton,
        )

        self.container.register(
            ConbusLightlevelService,
            factory=lambda: ConbusLightlevelService(
                telegram_service=self.container.resolve(TelegramService),
                conbus_service=self.container.resolve(ConbusService),
                datapoint_service=self.container.resolve(ConbusDatapointService),
            ),
            scope=punq.Scope.singleton,
        )

        self.container.register(
            ActionTableService,
            factory=lambda: ActionTableService(
                conbus_service=self.container.resolve(ConbusService),
                telegram_service=self.container.resolve(TelegramService),
            ),
            scope=punq.Scope.singleton,
        )

        self.container.register(
            MsActionTableService,
            factory=lambda: MsActionTableService(
                conbus_service=self.container.resolve(ConbusService),
                telegram_service=self.container.resolve(TelegramService),
            ),
            scope=punq.Scope.singleton,
        )

        self.container.register(
            ConbusAutoreportService,
            factory=lambda: ConbusAutoreportService(
                conbus_service=self.container.resolve(ConbusService),
                datapoint_service=self.container.resolve(ConbusDatapointService),
                telegram_service=self.container.resolve(TelegramService),
            ),
            scope=punq.Scope.singleton,
        )

        self.container.register(
            ConbusLinknumberService,
            factory=lambda: ConbusLinknumberService(
                conbus_service=self.container.resolve(ConbusService),
                datapoint_service=self.container.resolve(ConbusDatapointService),
                link_number_service=self.container.resolve(LinkNumberService),
                telegram_service=self.container.resolve(TelegramService),
            ),
            scope=punq.Scope.singleton,
        )

        self.container.register(
            ConbusCustomService,
            factory=lambda: ConbusCustomService(
                telegram_service=self.container.resolve(TelegramService),
                conbus_service=self.container.resolve(ConbusService),
            ),
            scope=punq.Scope.singleton,
        )

        self.container.register(
            ConbusRawService,
            factory=lambda: ConbusRawService(
                conbus_service=self.container.resolve(ConbusService),
            ),
            scope=punq.Scope.singleton,
        )

        self.container.register(
            ConbusReceiveService,
            factory=lambda: ConbusReceiveService(
                conbus_service=self.container.resolve(ConbusService),
            ),
            scope=punq.Scope.singleton,
        )

        # HomeKit conson config
        self.container.register(
            ConsonModuleListConfig,
            factory=lambda: ConsonModuleListConfig.from_yaml(self._conson_config_path),
            scope=punq.Scope.singleton,
        )

        # HomeKit services layer
        self.container.register(
            HomekitModuleService,
            factory=lambda: HomekitModuleService(
                conson_modules_config=self.container.resolve(ConsonModuleListConfig),
            ),
            scope=punq.Scope.singleton,
        )

        self.container.register(
            HomeKitCacheService,
            factory=lambda: HomeKitCacheService(
                cache_file=self._cache_file,
                conbus_output_service=self.container.resolve(ConbusOutputService),
                conbus_lightlevel_service=self.container.resolve(
                    ConbusLightlevelService
                ),
                telegram_service=self.container.resolve(TelegramService),
            ),
            scope=punq.Scope.singleton,
        )

        # HomeKit conson config
        self.container.register(
            HomekitConfig,
            factory=lambda: HomekitConfig.from_yaml(self._homekit_config_path),
            scope=punq.Scope.singleton,
        )

        self.container.register(
            HomekitService,
            factory=lambda: HomekitService(
                homekit_config=self.container.resolve(HomekitConfig),
                module_service=self.container.resolve(HomekitModuleService),
                output_service=self.container.resolve(ConbusOutputService),
                telegram_output_service=self.container.resolve(TelegramOutputService),
                datapoint_service=self.container.resolve(ConbusDatapointService),
                cache_service=self.container.resolve(HomeKitCacheService),
                lightlevel_service=self.container.resolve(ConbusLightlevelService),
            ),
            scope=punq.Scope.singleton,
        )

        # Log file services layer
        self.container.register(
            LogFileService,
            factory=lambda: LogFileService(
                telegram_service=self.container.resolve(TelegramService),
            ),
            scope=punq.Scope.singleton,
        )

        # Module type services layer
        self.container.register(ModuleTypeService, scope=punq.Scope.singleton)

        # Server services layer
        self.container.register(
            ServerService,
            factory=lambda: ServerService(
                telegram_service=self.container.resolve(TelegramService),
                discover_service=self.container.resolve(TelegramDiscoverService),
                config_path="server.yml",
                port=self._server_port,
            ),
            scope=punq.Scope.singleton,
        )

        # Other services
        self.container.register(
            ReverseProxyService,
            factory=lambda: ReverseProxyService(
                cli_config=self.container.resolve(ConbusClientConfig),
                listen_port=self._reverse_proxy_port,
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
