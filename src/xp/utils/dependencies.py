"""Dependency injection container for XP services."""

import punq
from bubus import EventBus
from twisted.internet import asyncioreactor
from twisted.internet.interfaces import IConnector
from twisted.internet.posixbase import PosixReactorBase

from xp.models import ConbusClientConfig
from xp.models.homekit.homekit_config import HomekitConfig
from xp.models.homekit.homekit_conson_config import ConsonModuleListConfig
from xp.services.conbus.actiontable.actiontable_serializer import ActionTableSerializer
from xp.services.conbus.actiontable.actiontable_service import ActionTableService
from xp.services.conbus.actiontable.msactiontable_service import MsActionTableService
from xp.services.conbus.actiontable.msactiontable_xp20_serializer import (
    Xp20MsActionTableSerializer,
)
from xp.services.conbus.actiontable.msactiontable_xp24_serializer import (
    Xp24MsActionTableSerializer,
)
from xp.services.conbus.actiontable.msactiontable_xp33_serializer import (
    Xp33MsActionTableSerializer,
)
from xp.services.conbus.conbus_blink_all_service import ConbusBlinkAllService
from xp.services.conbus.conbus_blink_service import ConbusBlinkService
from xp.services.conbus.conbus_custom_service import ConbusCustomService
from xp.services.conbus.conbus_datapoint_queryall_service import (
    ConbusDatapointQueryAllService,
)
from xp.services.conbus.conbus_datapoint_service import (
    ConbusDatapointService,
)
from xp.services.conbus.conbus_discover_service import ConbusDiscoverService
from xp.services.conbus.conbus_output_service import ConbusOutputService
from xp.services.conbus.conbus_raw_service import ConbusRawService
from xp.services.conbus.conbus_receive_service import ConbusReceiveService
from xp.services.conbus.conbus_scan_service import ConbusScanService
from xp.services.conbus.write_config_service import WriteConfigService
from xp.services.homekit.homekit_cache_service import HomeKitCacheService
from xp.services.homekit.homekit_conbus_service import HomeKitConbusService
from xp.services.homekit.homekit_dimminglight_service import HomeKitDimmingLightService
from xp.services.homekit.homekit_hap_service import HomekitHapService
from xp.services.homekit.homekit_lightbulb_service import HomeKitLightbulbService
from xp.services.homekit.homekit_module_service import HomekitModuleService
from xp.services.homekit.homekit_outlet_service import HomeKitOutletService
from xp.services.homekit.homekit_service import HomeKitService
from xp.services.log_file_service import LogFileService
from xp.services.module_type_service import ModuleTypeService
from xp.services.protocol.protocol_factory import TelegramFactory
from xp.services.protocol.telegram_protocol import TelegramProtocol
from xp.services.reverse_proxy_service import ReverseProxyService
from xp.services.server.server_service import ServerService
from xp.services.telegram.telegram_blink_service import TelegramBlinkService
from xp.services.telegram.telegram_discover_service import TelegramDiscoverService
from xp.services.telegram.telegram_link_number_service import LinkNumberService
from xp.services.telegram.telegram_output_service import TelegramOutputService
from xp.services.telegram.telegram_service import TelegramService

asyncioreactor.install()
from twisted.internet import reactor  # noqa: E402


class ServiceContainer:
    """
    Service container that manages dependency injection for all XP services.

    Uses the service dependency graph from Dependencies.dot to properly
    wire up all services with their dependencies.
    """

    def __init__(
        self,
        config_path: str = "cli.yml",
        homekit_config_path: str = "homekit.yml",
        conson_config_path: str = "conson.yml",
        server_port: int = 10001,
        reverse_proxy_port: int = 10001,
    ):
        """
        Initialize the service container.

        Args:
            config_path: Path to the Conbus CLI configuration file
            homekit_config_path: Path to the HomeKit configuration file
            conson_config_path: Path to the Conson configuration file
            server_port: Port for the server service
            reverse_proxy_port: Port for the reverse proxy service
        """
        self.container = punq.Container()
        self._config_path = config_path
        self._homekit_config_path = homekit_config_path
        self._conson_config_path = conson_config_path
        self._server_port = server_port
        self._reverse_proxy_port = reverse_proxy_port

        self._register_services()

    def _register_services(self) -> None:
        """Register all services in the container based on dependency graph."""
        # ConbusClientConfig
        self.container.register(
            ConbusClientConfig,
            factory=lambda: ConbusClientConfig.from_yaml(self._config_path),
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

        # Conbus services layer
        self.container.register(
            ConbusDatapointService,
            factory=lambda: ConbusDatapointService(
                telegram_service=self.container.resolve(TelegramService),
                cli_config=self.container.resolve(ConbusClientConfig),
                reactor=self.container.resolve(PosixReactorBase),
            ),
            scope=punq.Scope.singleton,
        )

        self.container.register(
            ConbusDatapointQueryAllService,
            factory=lambda: ConbusDatapointQueryAllService(
                telegram_service=self.container.resolve(TelegramService),
                cli_config=self.container.resolve(ConbusClientConfig),
                reactor=self.container.resolve(PosixReactorBase),
            ),
            scope=punq.Scope.singleton,
        )

        self.container.register(
            ConbusScanService,
            factory=lambda: ConbusScanService(
                cli_config=self.container.resolve(ConbusClientConfig),
                reactor=self.container.resolve(PosixReactorBase),
            ),
            scope=punq.Scope.singleton,
        )

        self.container.register(
            ConbusDiscoverService,
            factory=lambda: ConbusDiscoverService(
                cli_config=self.container.resolve(ConbusClientConfig),
                reactor=self.container.resolve(PosixReactorBase),
            ),
            scope=punq.Scope.singleton,
        )

        self.container.register(
            ConbusBlinkService,
            factory=lambda: ConbusBlinkService(
                cli_config=self.container.resolve(ConbusClientConfig),
                reactor=self.container.resolve(PosixReactorBase),
                telegram_service=self.container.resolve(TelegramService),
            ),
            scope=punq.Scope.singleton,
        )

        self.container.register(
            ConbusBlinkAllService,
            factory=lambda: ConbusBlinkAllService(
                cli_config=self.container.resolve(ConbusClientConfig),
                reactor=self.container.resolve(PosixReactorBase),
                telegram_service=self.container.resolve(TelegramService),
            ),
            scope=punq.Scope.singleton,
        )

        self.container.register(
            ConbusOutputService,
            factory=lambda: ConbusOutputService(
                telegram_output_service=self.container.resolve(TelegramOutputService),
                cli_config=self.container.resolve(ConbusClientConfig),
                reactor=self.container.resolve(PosixReactorBase),
            ),
            scope=punq.Scope.singleton,
        )

        self.container.register(
            WriteConfigService,
            factory=lambda: WriteConfigService(
                telegram_service=self.container.resolve(TelegramService),
                cli_config=self.container.resolve(ConbusClientConfig),
                reactor=self.container.resolve(PosixReactorBase),
            ),
            scope=punq.Scope.singleton,
        )

        self.container.register(
            ActionTableSerializer,
            factory=lambda: ActionTableSerializer,
            scope=punq.Scope.singleton,
        )

        self.container.register(
            ActionTableService,
            factory=lambda: ActionTableService(
                cli_config=self.container.resolve(ConbusClientConfig),
                reactor=self.container.resolve(PosixReactorBase),
                actiontable_serializer=self.container.resolve(ActionTableSerializer),
                telegram_service=self.container.resolve(TelegramService),
            ),
            scope=punq.Scope.singleton,
        )

        self.container.register(
            Xp20MsActionTableSerializer,
            factory=lambda: Xp20MsActionTableSerializer,
            scope=punq.Scope.singleton,
        )

        self.container.register(
            Xp24MsActionTableSerializer,
            factory=lambda: Xp24MsActionTableSerializer,
            scope=punq.Scope.singleton,
        )

        self.container.register(
            Xp33MsActionTableSerializer,
            factory=lambda: Xp33MsActionTableSerializer,
            scope=punq.Scope.singleton,
        )

        self.container.register(
            MsActionTableService,
            factory=lambda: MsActionTableService(
                cli_config=self.container.resolve(ConbusClientConfig),
                reactor=self.container.resolve(PosixReactorBase),
                xp20ms_serializer=self.container.resolve(Xp20MsActionTableSerializer),
                xp24ms_serializer=self.container.resolve(Xp24MsActionTableSerializer),
                xp33ms_serializer=self.container.resolve(Xp33MsActionTableSerializer),
                telegram_service=self.container.resolve(TelegramService),
            ),
            scope=punq.Scope.singleton,
        )

        self.container.register(
            ConbusCustomService,
            factory=lambda: ConbusCustomService(
                telegram_service=self.container.resolve(TelegramService),
                cli_config=self.container.resolve(ConbusClientConfig),
                reactor=self.container.resolve(PosixReactorBase),
            ),
            scope=punq.Scope.singleton,
        )

        self.container.register(
            ConbusRawService,
            factory=lambda: ConbusRawService(
                cli_config=self.container.resolve(ConbusClientConfig),
                reactor=self.container.resolve(PosixReactorBase),
            ),
            scope=punq.Scope.singleton,
        )

        self.container.register(
            ConbusReceiveService,
            factory=lambda: ConbusReceiveService(
                cli_config=self.container.resolve(ConbusClientConfig),
                reactor=self.container.resolve(PosixReactorBase),
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

        # Create event bus
        self.container.register(
            EventBus,
            factory=lambda: EventBus(max_history_size=500),
            scope=punq.Scope.singleton,
        )

        # HomeKit conson config
        self.container.register(
            HomekitConfig,
            factory=lambda: HomekitConfig.from_yaml(self._homekit_config_path),
            scope=punq.Scope.singleton,
        )

        self.container.register(
            HomekitHapService,
            factory=lambda: HomekitHapService(
                homekit_config=self.container.resolve(HomekitConfig),
                module_service=self.container.resolve(HomekitModuleService),
                event_bus=self.container.resolve(EventBus),
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

        # Create protocol with built-in debouncing
        self.container.register(
            TelegramProtocol,
            factory=lambda: TelegramProtocol(
                event_bus=self.container.resolve(EventBus),
                debounce_ms=50,
            ),
            scope=punq.Scope.singleton,
        )

        self.container.register(
            IConnector,
            factory=lambda: reactor,
            scope=punq.Scope.singleton,
        )

        self.container.register(
            TelegramFactory,
            factory=lambda: TelegramFactory(
                event_bus=self.container.resolve(EventBus),
                telegram_protocol=self.container.resolve(TelegramProtocol),
                connector=self.container.resolve(IConnector),
            ),
            scope=punq.Scope.singleton,
        )

        self.container.register(
            PosixReactorBase,
            factory=lambda: reactor,
            scope=punq.Scope.singleton,
        )

        self.container.register(
            HomeKitLightbulbService,
            factory=lambda: HomeKitLightbulbService(
                event_bus=self.container.resolve(EventBus),
            ),
            scope=punq.Scope.singleton,
        )

        self.container.register(
            HomeKitOutletService,
            factory=lambda: HomeKitOutletService(
                event_bus=self.container.resolve(EventBus),
            ),
            scope=punq.Scope.singleton,
        )

        self.container.register(
            HomeKitDimmingLightService,
            factory=lambda: HomeKitDimmingLightService(
                event_bus=self.container.resolve(EventBus),
            ),
            scope=punq.Scope.singleton,
        )

        # Cache service must be registered BEFORE HomeKitConbusService
        # so it intercepts ReadDatapointEvent first
        self.container.register(
            HomeKitCacheService,
            factory=lambda: HomeKitCacheService(
                event_bus=self.container.resolve(EventBus),
            ),
            scope=punq.Scope.singleton,
        )

        self.container.register(
            HomeKitConbusService,
            factory=lambda: HomeKitConbusService(
                event_bus=self.container.resolve(EventBus),
                telegram_protocol=self.container.resolve(TelegramProtocol),
            ),
            scope=punq.Scope.singleton,
        )

        self.container.register(
            TelegramService,
            factory=TelegramService,
            scope=punq.Scope.singleton,
        )

        self.container.register(
            HomeKitService,
            factory=lambda: HomeKitService(
                cli_config=self.container.resolve(ConbusClientConfig),
                event_bus=self.container.resolve(EventBus),
                telegram_factory=self.container.resolve(TelegramFactory),
                reactor=self.container.resolve(PosixReactorBase),
                lightbulb_service=self.container.resolve(HomeKitLightbulbService),
                outlet_service=self.container.resolve(HomeKitOutletService),
                dimminglight_service=self.container.resolve(HomeKitDimmingLightService),
                cache_service=self.container.resolve(HomeKitCacheService),
                conbus_service=self.container.resolve(HomeKitConbusService),
                module_factory=self.container.resolve(HomekitHapService),
                telegram_service=self.container.resolve(TelegramService),
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
