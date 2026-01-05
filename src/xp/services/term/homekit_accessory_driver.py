"""HomeKit Accessory Driver for pyhap integration."""

import asyncio
import logging
from typing import Callable, Dict, Optional

from pyhap.accessory import Accessory, Bridge
from pyhap.accessory_driver import AccessoryDriver
from pyhap.const import CATEGORY_LIGHTBULB, CATEGORY_OUTLET

from xp.models.homekit.homekit_config import HomekitConfig

# Callback type: (accessory_name, is_on, brightness_or_none)
OnSetCallback = Callable[[str, bool, Optional[int]], None]


class XPAccessory(Accessory):
    """
    Single accessory wrapping a Conbus output.

    Attributes:
        logger: Logger instance for this accessory.
        current_brightness: Current brightness value 0-100.
    """

    def __init__(
        self,
        driver: "HomekitAccessoryDriver",
        name: str,
        display_name: str,
        service_type: str,
        aid: int,
    ) -> None:
        """
        Initialize the XP accessory.

        Args:
            driver: HomekitAccessoryDriver instance.
            name: Accessory name (unique identifier for internal tracking).
            display_name: Display name shown in HomeKit (from config description).
            service_type: Service type ('light', 'outlet', 'dimminglight').
            aid: Accessory ID for HomeKit.
        """
        super().__init__(driver._driver, display_name, aid=aid)
        self._hk_driver = driver
        self._accessory_id = name
        self._is_dimmable = service_type == "dimminglight"
        self._char_brightness: Optional[object] = None
        self._current_brightness: int = 100
        self.logger = logging.getLogger(__name__)

        if self._is_dimmable:
            self.category = CATEGORY_LIGHTBULB
            serv = self.add_preload_service("Lightbulb", chars=["On", "Brightness"])
            self._char_brightness = serv.configure_char(
                "Brightness",
                setter_callback=self._set_brightness,
                value=self._current_brightness,
            )
        elif service_type == "outlet":
            self.category = CATEGORY_OUTLET
            serv = self.add_preload_service("Outlet")
        else:
            self.category = CATEGORY_LIGHTBULB
            serv = self.add_preload_service("Lightbulb")

        self._char_on = serv.configure_char("On", setter_callback=self._set_on)

    def _set_on(self, value: bool) -> None:
        """
        Handle HomeKit set on/off request.

        Args:
            value: True for on, False for off.
        """
        if self._hk_driver._on_set:
            self._hk_driver._on_set(self._accessory_id, value, None)

    def _set_brightness(self, value: int) -> None:
        """
        Handle HomeKit set brightness request.

        Args:
            value: Brightness value 0-100.
        """
        if self._hk_driver._on_set:
            self._hk_driver._on_set(self._accessory_id, True, value)
        self._current_brightness = value

    def update_state(self, is_on: bool, brightness: Optional[int] = None) -> None:
        """
        Update accessory state from Conbus event.

        Args:
            is_on: True if accessory is on, False otherwise.
            brightness: Optional brightness value 0-100.
        """
        self._char_on.set_value(is_on)
        if brightness is not None and self._char_brightness:
            self._char_brightness.set_value(brightness)  # type: ignore[attr-defined]
            self._current_brightness = brightness

    @property
    def current_brightness(self) -> int:
        """Get current brightness value."""
        return self._current_brightness


class HomekitAccessoryDriver:
    """Wrapper around pyhap AccessoryDriver."""

    def __init__(self, homekit_config: HomekitConfig) -> None:
        """
        Initialize the HomeKit accessory driver.

        Args:
            homekit_config: HomekitConfig with network and accessory settings.
        """
        self.logger = logging.getLogger(__name__)
        self._homekit_config = homekit_config
        self._driver: Optional[AccessoryDriver] = None
        self._accessories: Dict[str, XPAccessory] = {}
        self._on_set: Optional[OnSetCallback] = None

    def set_callback(self, on_set: OnSetCallback) -> None:
        """
        Set callback for HomeKit set events.

        Args:
            on_set: Callback(accessory_name, is_on, brightness) called when HomeKit app changes state.
                    brightness is None for on/off only, or 0-100 for dimming.
        """
        self._on_set = on_set

    def _setup_bridge(self, config: HomekitConfig) -> None:
        """
        Set up HomeKit bridge with accessories.

        Args:
            config: HomekitConfig with accessory definitions.
        """
        assert self._driver is not None
        bridge = Bridge(self._driver, config.bridge.name)
        aid = 2  # Bridge is 1

        for acc_config in config.accessories:
            accessory = XPAccessory(
                driver=self,
                name=acc_config.name,
                display_name=acc_config.description,
                service_type=acc_config.service,
                aid=aid,
            )
            bridge.add_accessory(accessory)
            self._accessories[acc_config.name] = accessory
            aid += 1

        self._driver.add_accessory(bridge)

    async def start(self) -> None:
        """Start the AccessoryDriver (non-blocking)."""
        try:
            # Enable pyhap debug logging
            pyhap_logger = logging.getLogger("pyhap")
            pyhap_logger.setLevel(logging.DEBUG)

            # Create driver with the running event loop
            loop = asyncio.get_running_loop()
            config = self._homekit_config
            pincode = config.homekit.pincode.encode()
            self.logger.info(
                f"Starting HAP driver on {config.homekit.ip}:{config.homekit.port} with pincode {config.homekit.pincode}"
            )
            self._driver = AccessoryDriver(
                loop=loop,
                address=str(config.homekit.ip),
                port=config.homekit.port,
                pincode=pincode,
                persist_file=config.homekit.accessory_state_file,
            )
            self._setup_bridge(config)
            await self._driver.async_start()
            self.logger.info("AccessoryDriver started successfully")
        except Exception as e:
            self.logger.error(f"Error starting AccessoryDriver: {e}", exc_info=True)

    async def stop(self) -> None:
        """Stop the AccessoryDriver."""
        if not self._driver:
            return
        try:
            await self._driver.async_stop()
            self.logger.info("AccessoryDriver stopped successfully")
        except Exception as e:
            self.logger.error(f"Error stopping AccessoryDriver: {e}", exc_info=True)

    def update_state(
        self, accessory_name: str, is_on: bool, brightness: Optional[int] = None
    ) -> None:
        """
        Update accessory state from Conbus event.

        Args:
            accessory_name: Accessory name to update.
            is_on: True if accessory is on, False otherwise.
            brightness: Optional brightness value 0-100.
        """
        acc = self._accessories.get(accessory_name)
        if acc:
            acc.update_state(is_on, brightness)
        else:
            self.logger.warning(f"Unknown accessory name: {accessory_name}")

    def get_brightness(self, accessory_name: str) -> int:
        """
        Get current brightness for an accessory.

        Args:
            accessory_name: Accessory name.

        Returns:
            Current brightness 0-100, defaults to 100 if not found.
        """
        acc = self._accessories.get(accessory_name)
        if acc:
            return acc.current_brightness
        return 100
