"""Device Service Factory for creating device instances.

This module provides a factory for creating device service instances
with proper dependency injection of serializers.
"""

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
from xp.services.server.base_server_service import BaseServerService
from xp.services.server.cp20_server_service import CP20ServerService
from xp.services.server.xp20_server_service import XP20ServerService
from xp.services.server.xp24_server_service import XP24ServerService
from xp.services.server.xp33_server_service import XP33ServerService
from xp.services.server.xp130_server_service import XP130ServerService
from xp.services.server.xp230_server_service import XP230ServerService


class DeviceServiceFactory:
    """Factory for creating device service instances.

    Encapsulates device creation logic and handles serializer injection
    for different device types.
    """

    def __init__(
        self,
        xp20ms_serializer: Xp20MsActionTableSerializer,
        xp24ms_serializer: Xp24MsActionTableSerializer,
        xp33ms_serializer: Xp33MsActionTableSerializer,
        ms_serializer: MsActionTableSerializer,
    ):
        """Initialize device service factory.

        Args:
            xp20ms_serializer: XP20 MsActionTable serializer (injected via DI).
            xp24ms_serializer: XP24 MsActionTable serializer (injected via DI).
            xp33ms_serializer: XP33 MsActionTable serializer (injected via DI).
            ms_serializer: Generic MsActionTable serializer (injected via DI).
        """
        self.xp20ms_serializer = xp20ms_serializer
        self.xp24ms_serializer = xp24ms_serializer
        self.xp33ms_serializer = xp33ms_serializer
        self.ms_serializer = ms_serializer

    def create_device(self, module_type: str, serial_number: str) -> BaseServerService:
        """Create device instance for given module type.

        Args:
            module_type: Module type code (e.g., "XP20", "XP33LR").
            serial_number: Device serial number.

        Returns:
            Device service instance configured with appropriate serializer.

        Raises:
            ValueError: If module_type is unknown or unsupported.
        """
        # Map module types to their constructors and parameters
        if module_type == "CP20":
            return CP20ServerService(serial_number, "CP20", self.ms_serializer)

        elif module_type == "XP24":
            return XP24ServerService(serial_number, "XP24", self.xp24ms_serializer)

        elif module_type == "XP33":
            return XP33ServerService(serial_number, "XP33", self.xp33ms_serializer)

        elif module_type == "XP33LR":
            return XP33ServerService(serial_number, "XP33LR", self.xp33ms_serializer)

        elif module_type == "XP33LED":
            return XP33ServerService(serial_number, "XP33LED", self.xp33ms_serializer)

        elif module_type == "XP20":
            return XP20ServerService(serial_number, "XP20", self.xp20ms_serializer)

        elif module_type == "XP130":
            return XP130ServerService(serial_number, "XP130", self.ms_serializer)

        elif module_type == "XP230":
            return XP230ServerService(serial_number, "XP230", self.ms_serializer)

        else:
            raise ValueError(
                f"Unknown device type '{module_type}' for serial {serial_number}"
            )
