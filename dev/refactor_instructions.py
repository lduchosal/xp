#!/usr/bin/env python3
"""Auto-generated refactoring script for IoC/DI support."""

# This script shows what changes need to be made
# Review carefully before applying!


# File: src/xp/services/conbus/conbus_scan_service.py
#======================================================================

# Class: ConbusScanService
# Current params: ['config_path']
# Dependencies: 2

# NEW SIGNATURE:
# def __init__(
        self,
        config_path: str = "cli.yml",
        telegram_service: Optional[TelegramService] = None,
        conbus_service: Optional[ConbusService] = None,
    ):

# NEW ASSIGNMENTS:
#         self.telegram_service = telegram_service or TelegramService()
#         self.conbus_service = conbus_service or ConbusService(config_path)


# File: src/xp/services/conbus/conbus_datapoint_service.py
#======================================================================

# Class: ConbusDatapointService
# Current params: ['config_path']
# Dependencies: 2

# NEW SIGNATURE:
# def __init__(
        self,
        config_path: str = "cli.yml",
        telegram_service: Optional[TelegramService] = None,
        conbus_service: Optional[ConbusService] = None,
    ):

# NEW ASSIGNMENTS:
#         self.telegram_service = telegram_service or TelegramService()
#         self.conbus_service = conbus_service or ConbusService(config_path)


# File: src/xp/services/conbus/conbus_output_service.py
#======================================================================

# Class: ConbusOutputService
# Current params: ['config_path']
# Dependencies: 4

# NEW SIGNATURE:
# def __init__(
        self,
        config_path: str = "cli.yml",
        telegram_service: Optional[TelegramService] = None,
        telegram_output_service: Optional[TelegramOutputService] = None,
        datapoint_service: Optional[ConbusDatapointService] = None,
        conbus_service: Optional[ConbusService] = None,
    ):

# NEW ASSIGNMENTS:
#         self.telegram_service = telegram_service or TelegramService()
#         self.telegram_output_service = telegram_output_service or TelegramOutputService()
#         self.datapoint_service = datapoint_service or ConbusDatapointService()
#         self.conbus_service = conbus_service or ConbusService(config_path)


# File: src/xp/services/conbus/conbus_discover_service.py
#======================================================================

# Class: ConbusDiscoverService
# Current params: ['config_path']
# Dependencies: 3

# NEW SIGNATURE:
# def __init__(
        self,
        config_path: str = "cli.yml",
        telegram_service: Optional[TelegramService] = None,
        telegram_discover_service: Optional[TelegramDiscoverService] = None,
        conbus_service: Optional[ConbusService] = None,
    ):

# NEW ASSIGNMENTS:
#         self.telegram_service = telegram_service or TelegramService()
#         self.telegram_discover_service = telegram_discover_service or TelegramDiscoverService()
#         self.conbus_service = conbus_service or ConbusService(config_path)


# File: src/xp/services/conbus/actiontable/actiontable_service.py
#======================================================================

# Class: ActionTableService
# Current params: ['config_path']
# Dependencies: 3

# NEW SIGNATURE:
# def __init__(
        self,
        config_path: str = "cli.yml",
        conbus_service: Optional[ConbusService] = None,
        serializer: Optional[ActionTableSerializer] = None,
        telegram_service: Optional[TelegramService] = None,
    ):

# NEW ASSIGNMENTS:
#         self.conbus_service = conbus_service or ConbusService(config_path)
#         self.serializer = serializer or ActionTableSerializer()
#         self.telegram_service = telegram_service or TelegramService()


# File: src/xp/services/conbus/actiontable/msactiontable_service.py
#======================================================================

# Class: MsActionTableService
# Current params: ['config_path']
# Dependencies: 3

# NEW SIGNATURE:
# def __init__(
        self,
        config_path: str = "cli.yml",
        conbus_service: Optional[ConbusService] = None,
        serializer: Optional[Xp24MsActionTableSerializer] = None,
        telegram_service: Optional[TelegramService] = None,
    ):

# NEW ASSIGNMENTS:
#         self.conbus_service = conbus_service or ConbusService(config_path)
#         self.serializer = serializer or Xp24MsActionTableSerializer()
#         self.telegram_service = telegram_service or TelegramService()


# File: src/xp/services/homekit/homekit_cache_service.py
#======================================================================

# Class: HomeKitCacheService
# Current params: ['config_path', 'cache_file']
# Dependencies: 3


# File: src/xp/services/homekit/homekit_service.py
#======================================================================

# Class: HomekitService
# Current params: ['homekit_config_path', 'conson_config_path']
# Dependencies: 1


# File: src/xp/services/server/server_service.py
#======================================================================

# Class: ServerService
# Current params: ['config_path', 'port']
# Dependencies: 2

# NEW SIGNATURE:
# def __init__(
        self,
        config_path: str = "cli.yml",
        telegram_service: Optional[TelegramService] = None,
        discover_service: Optional[TelegramDiscoverService] = None,
    ):

# NEW ASSIGNMENTS:
#         self.telegram_service = telegram_service or TelegramService()
#         self.discover_service = discover_service or TelegramDiscoverService()

