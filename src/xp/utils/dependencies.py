"""Dependency injection container for XP services."""

import punq
from twisted.internet import asyncioreactor
from twisted.internet.posixbase import PosixReactorBase

from xp.models import ConbusClientConfig
from xp.models.conbus.conbus_logger_config import ConbusLoggerConfig
from xp.models.config.conson_module_config import ConsonModuleListConfig
from xp.models.homekit.homekit_config import HomekitConfig
from xp.models.term.protocol_keys_config import ProtocolKeysConfig
from xp.services.actiontable.actiontable_serializer import ActionTableSerializer
from xp.services.actiontable.msactiontable_serializer import MsActionTableSerializer
from xp.services.actiontable.msactiontable_xp20_serializer import (
    Xp20MsActionTableSerializer,
)
from xp.services.actiontable.msactiontable_xp24_serializer import (
    Xp24MsActionTableSerializer,
)
from xp.services.actiontable.msactiontable_xp33_serializer import (
    Xp33MsActionTableSerializer,
)
from xp.services.conbus.actiontable.actiontable_download_service import (
    ActionTableDownloadService,
)
from xp.services.conbus.actiontable.actiontable_list_service import (
    ActionTableListService,
)
from xp.services.conbus.actiontable.actiontable_show_service import (
    ActionTableShowService,
)
from xp.services.conbus.actiontable.actiontable_upload_service import (
    ActionTableUploadService,
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
from xp.services.conbus.conbus_event_list_service import ConbusEventListService
from xp.services.conbus.conbus_event_raw_service import ConbusEventRawService
from xp.services.conbus.conbus_export_actiontable_service import (
    ConbusActiontableExportService,
)
from xp.services.conbus.conbus_export_service import ConbusExportService
from xp.services.conbus.conbus_output_service import ConbusOutputService
from xp.services.conbus.conbus_raw_service import ConbusRawService
from xp.services.conbus.conbus_receive_service import ConbusReceiveService
from xp.services.conbus.conbus_scan_service import ConbusScanService
from xp.services.conbus.write_config_service import WriteConfigService
from xp.services.log_file_service import LogFileService
from xp.services.module_type_service import ModuleTypeService
from xp.services.protocol import ConbusEventProtocol
from xp.services.reverse_proxy_service import ReverseProxyService
from xp.services.server.device_service_factory import DeviceServiceFactory
from xp.services.server.server_service import ServerService
from xp.services.telegram.telegram_blink_service import TelegramBlinkService
from xp.services.telegram.telegram_datapoint_service import TelegramDatapointService
from xp.services.telegram.telegram_discover_service import TelegramDiscoverService
from xp.services.telegram.telegram_link_number_service import LinkNumberService
from xp.services.telegram.telegram_output_service import TelegramOutputService
from xp.services.telegram.telegram_service import TelegramService
from xp.services.term.homekit_accessory_driver import HomekitAccessoryDriver
from xp.services.term.homekit_service import HomekitService
from xp.services.term.protocol_monitor_service import ProtocolMonitorService
from xp.services.term.state_monitor_service import StateMonitorService
from xp.term.homekit import HomekitApp
from xp.term.protocol import ProtocolMonitorApp
from xp.term.state import StateMonitorApp
from xp.utils.logging import LoggerService

asyncioreactor.install()
from twisted.internet import reactor  # noqa: E402


class ServiceContainer:
    """
    Service container that manages dependency injection for all XP services.

    Uses the service dependency graph from Dependencies.dot to properly wire up all
    services with their dependencies.
    """

    def __init__(
        self,
        client_config_path: str = "cli.yml",
        logger_config_path: str = "logger.yml",
        homekit_config_path: str = "homekit.yml",
        conson_config_path: str = "conson.yml",
        export_config_path: str = "export.yml",
        server_port: int = 10001,
        protocol_keys_config_path: str = "protocol.yml",
        reverse_proxy_port: int = 10001,
    ):
        """
        Initialize the service container.

        Args:
            client_config_path: Path to the Conbus CLI configuration file
            logger_config_path: Path to the Conbus Loggerr configuration file
            homekit_config_path: Path to the HomeKit configuration file
            conson_config_path: Path to the Conson configuration file
            export_config_path: Path to the Conson export file
            protocol_keys_config_path: Path to the protocol keys configuration file
            server_port: Port for the server service
            reverse_proxy_port: Port for the reverse proxy service
        """
        self.container = punq.Container()
        self._client_config_path = client_config_path
        self._logger_config_path = logger_config_path
        self._homekit_config_path = homekit_config_path
        self._conson_config_path = conson_config_path
        self._export_config_path = export_config_path
        self._protocol_keys_config_path = protocol_keys_config_path
        self._server_port = server_port
        self._reverse_proxy_port = reverse_proxy_port

        self._register_services()

    def _register_services(self) -> None:
        """Register all services in the container based on dependency graph."""
        # ConbusClientConfig
        self.container.register(
            ConbusClientConfig,
            factory=lambda: ConbusClientConfig.from_yaml(self._client_config_path),
            scope=punq.Scope.singleton,
        )

        self.container.register(
            ConbusLoggerConfig,
            factory=lambda: ConbusLoggerConfig.from_yaml(self._logger_config_path),
            scope=punq.Scope.singleton,
        )

        self.container.register(
            ConsonModuleListConfig,
            factory=lambda: ConsonModuleListConfig.from_yaml(self._conson_config_path),
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
        self.container.register(TelegramDatapointService, scope=punq.Scope.singleton)
        self.container.register(LinkNumberService, scope=punq.Scope.singleton)

        # Reactor
        self.container.register(
            PosixReactorBase,
            factory=lambda: reactor,
            scope=punq.Scope.singleton,
        )

        # Conbus services layer
        self.container.register(
            ConbusEventProtocol,
            factory=lambda: ConbusEventProtocol(
                cli_config=self.container.resolve(ConbusClientConfig),
                reactor=self.container.resolve(PosixReactorBase),
                telegram_service=self.container.resolve(TelegramService),
            ),
            scope=punq.Scope.singleton,
        )

        self.container.register(
            ConbusDatapointService,
            factory=lambda: ConbusDatapointService(
                conbus_protocol=self.container.resolve(ConbusEventProtocol),
                telegram_service=self.container.resolve(TelegramService),
            ),
            scope=punq.Scope.singleton,
        )

        self.container.register(
            ConbusDatapointQueryAllService,
            factory=lambda: ConbusDatapointQueryAllService(
                conbus_protocol=self.container.resolve(ConbusEventProtocol),
                telegram_service=self.container.resolve(TelegramService),
            ),
            scope=punq.Scope.singleton,
        )

        self.container.register(
            ConbusScanService,
            factory=lambda: ConbusScanService(
                conbus_protocol=self.container.resolve(ConbusEventProtocol),
            ),
            scope=punq.Scope.singleton,
        )

        self.container.register(
            ConbusDiscoverService,
            factory=lambda: ConbusDiscoverService(
                conbus_protocol=self.container.resolve(ConbusEventProtocol)
            ),
            scope=punq.Scope.singleton,
        )

        self.container.register(
            ConbusExportService,
            factory=lambda: ConbusExportService(
                conbus_protocol=self.container.resolve(ConbusEventProtocol),
                telegram_service=self.container.resolve(TelegramService),
            ),
            scope=punq.Scope.singleton,
        )

        self.container.register(
            ConbusActiontableExportService,
            factory=lambda: ConbusActiontableExportService(
                download_service=self.container.resolve(ActionTableDownloadService),
                module_list=self.container.resolve(ConsonModuleListConfig),
            ),
            scope=punq.Scope.singleton,
        )

        # Terminal UI
        self.container.register(
            ProtocolMonitorService,
            factory=lambda: ProtocolMonitorService(
                conbus_protocol=self.container.resolve(ConbusEventProtocol),
                protocol_keys=self._load_protocol_keys(),
            ),
            scope=punq.Scope.singleton,
        )

        self.container.register(
            ProtocolMonitorApp,
            factory=lambda: ProtocolMonitorApp(
                protocol_service=self.container.resolve(ProtocolMonitorService)
            ),
            scope=punq.Scope.singleton,
        )

        self.container.register(
            StateMonitorService,
            factory=lambda: StateMonitorService(
                conbus_protocol=self.container.resolve(ConbusEventProtocol),
                conson_config=self.container.resolve(ConsonModuleListConfig),
                telegram_service=self.container.resolve(TelegramService),
            ),
            scope=punq.Scope.singleton,
        )

        self.container.register(
            StateMonitorApp,
            factory=lambda: StateMonitorApp(
                state_service=self.container.resolve(StateMonitorService)
            ),
            scope=punq.Scope.singleton,
        )

        # HomeKit config
        self.container.register(
            HomekitConfig,
            factory=lambda: HomekitConfig.from_yaml(self._homekit_config_path),
            scope=punq.Scope.singleton,
        )

        self.container.register(
            HomekitAccessoryDriver,
            factory=lambda: HomekitAccessoryDriver(
                homekit_config=self.container.resolve(HomekitConfig),
            ),
            scope=punq.Scope.singleton,
        )

        self.container.register(
            HomekitService,
            factory=lambda: HomekitService(
                conbus_protocol=self.container.resolve(ConbusEventProtocol),
                homekit_config=self.container.resolve(HomekitConfig),
                conson_config=self.container.resolve(ConsonModuleListConfig),
                telegram_service=self.container.resolve(TelegramService),
                accessory_driver=self.container.resolve(HomekitAccessoryDriver),
            ),
            scope=punq.Scope.singleton,
        )

        self.container.register(
            HomekitApp,
            factory=lambda: HomekitApp(
                homekit_service=self.container.resolve(HomekitService)
            ),
            scope=punq.Scope.singleton,
        )

        self.container.register(
            ConbusEventRawService,
            factory=lambda: ConbusEventRawService(
                conbus_protocol=self.container.resolve(ConbusEventProtocol)
            ),
            scope=punq.Scope.singleton,
        )

        self.container.register(
            ConbusEventListService,
            factory=lambda: ConbusEventListService(
                conson_config=self.container.resolve(ConsonModuleListConfig)
            ),
            scope=punq.Scope.singleton,
        )

        self.container.register(
            ConbusBlinkService,
            factory=lambda: ConbusBlinkService(
                conbus_protocol=self.container.resolve(ConbusEventProtocol),
                telegram_service=self.container.resolve(TelegramService),
            ),
            scope=punq.Scope.singleton,
        )

        self.container.register(
            ConbusBlinkAllService,
            factory=lambda: ConbusBlinkAllService(
                conbus_protocol=self.container.resolve(ConbusEventProtocol),
                telegram_service=self.container.resolve(TelegramService),
            ),
            scope=punq.Scope.singleton,
        )

        self.container.register(
            ConbusOutputService,
            factory=lambda: ConbusOutputService(
                conbus_protocol=self.container.resolve(ConbusEventProtocol),
                telegram_output_service=self.container.resolve(TelegramOutputService),
            ),
            scope=punq.Scope.singleton,
        )

        self.container.register(
            WriteConfigService,
            factory=lambda: WriteConfigService(
                conbus_protocol=self.container.resolve(ConbusEventProtocol),
                telegram_service=self.container.resolve(TelegramService),
            ),
            scope=punq.Scope.singleton,
        )

        self.container.register(
            ActionTableSerializer,
            factory=lambda: ActionTableSerializer,
            scope=punq.Scope.singleton,
        )

        self.container.register(
            ActionTableDownloadService,
            factory=lambda: ActionTableDownloadService(
                conbus_protocol=self.container.resolve(ConbusEventProtocol),
                actiontable_serializer=self.container.resolve(ActionTableSerializer),
                msactiontable_serializer_xp20=self.container.resolve(
                    Xp20MsActionTableSerializer
                ),
                msactiontable_serializer_xp24=self.container.resolve(
                    Xp24MsActionTableSerializer
                ),
                msactiontable_serializer_xp33=self.container.resolve(
                    Xp33MsActionTableSerializer
                ),
            ),
            scope=punq.Scope.singleton,
        )

        self.container.register(
            ActionTableUploadService,
            factory=lambda: ActionTableUploadService(
                conbus_protocol=self.container.resolve(ConbusEventProtocol),
                actiontable_serializer=self.container.resolve(ActionTableSerializer),
                xp20ms_serializer=self.container.resolve(Xp20MsActionTableSerializer),
                xp24ms_serializer=self.container.resolve(Xp24MsActionTableSerializer),
                xp33ms_serializer=self.container.resolve(Xp33MsActionTableSerializer),
                telegram_service=self.container.resolve(TelegramService),
                conson_config=self.container.resolve(ConsonModuleListConfig),
            ),
            scope=punq.Scope.singleton,
        )

        self.container.register(
            ActionTableListService,
            factory=ActionTableListService,
            scope=punq.Scope.singleton,
        )

        self.container.register(
            ActionTableShowService,
            factory=ActionTableShowService,
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
            ConbusCustomService,
            factory=lambda: ConbusCustomService(
                conbus_protocol=self.container.resolve(ConbusEventProtocol),
                telegram_service=self.container.resolve(TelegramService),
            ),
            scope=punq.Scope.singleton,
        )

        self.container.register(
            ConbusRawService,
            factory=lambda: ConbusRawService(
                conbus_protocol=self.container.resolve(ConbusEventProtocol),
            ),
            scope=punq.Scope.singleton,
        )

        self.container.register(
            ConbusReceiveService,
            factory=lambda: ConbusReceiveService(
                conbus_protocol=self.container.resolve(ConbusEventProtocol)
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

        # Logging
        self.container.register(
            LoggerService,
            factory=lambda: LoggerService(
                logger_config=self.container.resolve(ConbusLoggerConfig),
            ),
            scope=punq.Scope.singleton,
        )

        # Module type services layer
        self.container.register(ModuleTypeService, scope=punq.Scope.singleton)

        # MsActionTable serializers
        self.container.register(MsActionTableSerializer, scope=punq.Scope.singleton)
        self.container.register(Xp20MsActionTableSerializer, scope=punq.Scope.singleton)
        self.container.register(Xp24MsActionTableSerializer, scope=punq.Scope.singleton)
        self.container.register(Xp33MsActionTableSerializer, scope=punq.Scope.singleton)

        # Device service factory
        self.container.register(
            DeviceServiceFactory,
            factory=lambda: DeviceServiceFactory(
                xp20ms_serializer=self.container.resolve(Xp20MsActionTableSerializer),
                xp24ms_serializer=self.container.resolve(Xp24MsActionTableSerializer),
                xp33ms_serializer=self.container.resolve(Xp33MsActionTableSerializer),
                ms_serializer=self.container.resolve(MsActionTableSerializer),
            ),
            scope=punq.Scope.singleton,
        )

        # Server services layer
        self.container.register(
            ServerService,
            factory=lambda: ServerService(
                telegram_service=self.container.resolve(TelegramService),
                discover_service=self.container.resolve(TelegramDiscoverService),
                device_factory=self.container.resolve(DeviceServiceFactory),
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

    def _load_protocol_keys(self) -> "ProtocolKeysConfig":
        """
        Load protocol keys from YAML config file.

        Returns:
            ProtocolKeysConfig instance loaded from configuration path.
        """
        from pathlib import Path

        from xp.models.term.protocol_keys_config import ProtocolKeysConfig

        config_path = Path(self._protocol_keys_config_path).resolve()
        return ProtocolKeysConfig.from_yaml(config_path)

    def get_container(self) -> punq.Container:
        """
        Get the configured container with all services registered.

        Returns:
            punq.Container: The configured dependency injection container
        """
        return self.container
