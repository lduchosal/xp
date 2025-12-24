# AccessoryDriver Integration for HomekitService

Add pyhap AccessoryDriver to expose accessories via Apple HomeKit protocol.

## Architecture

```
HomekitService
├── ConbusEventProtocol (existing)
├── HomekitConfig (existing)
└── HomekitAccessoryDriver (NEW)
    ├── Bridge + Accessories
    ├── HAPServer
    └── mDNS
```

## Event Loop Integration

All three systems share the same asyncio loop (owned by Textual):

```python
# AccessoryDriver receives the shared loop, uses async_start()
loop = asyncio.get_event_loop()
driver = AccessoryDriver(loop=loop, ...)

await driver.async_start()  # Non-blocking, NOT driver.start()
await driver.async_stop()
```

## Bidirectional Sync

```
Conbus Event → HomekitService → char.set_value(notify=True)
HomeKit App  → setter_callback → HomekitService → send_raw_telegram()
```

## Key Components

### HomekitAccessoryDriver

```python
class HomekitAccessoryDriver:
    def __init__(self, homekit_config: HomekitConfig) -> None: ...
    def set_callback(self, on_set: Callable[[str, bool], None]) -> None: ...
    async def start(self) -> None: ...
    async def stop(self) -> None: ...
    def update_state(self, accessory_name: str, is_on: bool) -> None: ...
```

### Accessory Mapping

| service type   | pyhap Service          | Notes                    |
|----------------|------------------------|--------------------------|
| `light`        | Lightbulb              | On/Off only              |
| `outlet`       | Outlet                 | On/Off only              |
| `dimminglight` | Lightbulb + Brightness | Brightness deferred      |

Note: Brightness characteristic for `dimminglight` will be implemented in a future update.

### Accessory Name Uniqueness

Accessory names (`HomekitAccessoryConfig.name`) must be unique within the configuration. The name serves as both the display name and the lookup key for state updates.

## Files

```
src/xp/services/term/
├── homekit_service.py  # existing class
└── homekit_accessory_driver.py  # Add HomekitAccessoryDriver class
```

## Config

Add `pincode` and `accessory_state_file` to HomekitConfig (homekit.yml):

```yaml
homekit:
  ip: 0.0.0.0
  port: 51826
  pincode: "031-45-154"
  accessory_state_file: "./accessory.state"
```

### HomekitConfig Structure (Pydantic)

```python
class NetworkConfig(BaseModel):
    ip: Union[IPvAnyAddress, IPv4Address, IPv6Address, str] = "127.0.0.1"
    port: int = 51826

class BridgeConfig(BaseModel):
    name: str = "Conson Bridge"
    rooms: List[RoomConfig] = []

class HomekitAccessoryConfig(BaseModel):
    name: str                      # Unique identifier and display name
    id: str
    serial_number: str
    output_number: int
    description: str
    service: str                   # "light", "outlet", "dimminglight"
    on_action: str                 # Telegram string, e.g. "S0012345678F03D0101"
    off_action: str                # Telegram string, e.g. "S0012345678F03D0100"
    toggle_action: Optional[str]
    hap_accessory: Optional[int]

class HomekitConfig(BaseModel):
    homekit: NetworkConfig
    conson: NetworkConfig
    bridge: BridgeConfig
    accessories: List[HomekitAccessoryConfig]
```

Required additions to `NetworkConfig`:
- `pincode: str = "031-45-154"`
- `accessory_state_file: str = "./accessory.state"`

## Error Handling

Follow existing codebase patterns:

```python
try:
    await self._driver.async_start()
except Exception as e:
    self.logger.error(f"Error starting AccessoryDriver: {e}", exc_info=True)
```

Specific error scenarios:
- **Port in use**: Log error, do not crash service
- **Unknown accessory name in callback**: Log warning, ignore update

## Minimal Implementation

```python
from typing import Callable, Dict, Optional
import asyncio
import logging

from pyhap.accessory import Accessory, Bridge
from pyhap.accessory_driver import AccessoryDriver
from pyhap.const import CATEGORY_LIGHTBULB, CATEGORY_OUTLET

from xp.models.homekit.homekit_config import HomekitConfig


class XPAccessory(Accessory):
    """Single accessory wrapping a Conbus output."""

    def __init__(
        self,
        driver: "HomekitAccessoryDriver",
        name: str,
        service_type: str,
        aid: int,
    ) -> None:
        super().__init__(driver._driver, name, aid=aid)
        self._hk_driver = driver
        self._accessory_id = name
        self.logger = logging.getLogger(__name__)

        if service_type == "dimminglight":
            self.category = CATEGORY_LIGHTBULB
            serv = self.add_preload_service("Lightbulb", chars=["On", "Brightness"])
            # Note: Brightness setter_callback deferred to future update
        elif service_type == "outlet":
            self.category = CATEGORY_OUTLET
            serv = self.add_preload_service("Outlet")
        else:
            self.category = CATEGORY_LIGHTBULB
            serv = self.add_preload_service("Lightbulb")

        self._char_on = serv.configure_char("On", setter_callback=self._set_on)

    def _set_on(self, value: bool) -> None:
        if self._hk_driver._on_set:
            self._hk_driver._on_set(self._accessory_id, value)

    def update_state(self, is_on: bool) -> None:
        self._char_on.set_value(is_on)


class HomekitAccessoryDriver:
    """Wrapper around pyhap AccessoryDriver."""

    def __init__(self, homekit_config: HomekitConfig) -> None:
        self.logger = logging.getLogger(__name__)
        loop = asyncio.get_event_loop()
        self._driver = AccessoryDriver(
            loop=loop,
            address=str(homekit_config.homekit.ip),
            port=homekit_config.homekit.port,
            pincode=homekit_config.homekit.pincode.encode(),
            persist_file=homekit_config.homekit.accessory_state_file,
        )
        self._accessories: Dict[str, XPAccessory] = {}
        self._on_set: Optional[Callable[[str, bool], None]] = None
        self._setup_bridge(homekit_config)

    def set_callback(self, on_set: Callable[[str, bool], None]) -> None:
        self._on_set = on_set

    def _setup_bridge(self, config: HomekitConfig) -> None:
        bridge = Bridge(self._driver, config.bridge.name)
        aid = 2  # Bridge is 1

        for acc_config in config.accessories:
            accessory = XPAccessory(
                driver=self,
                name=acc_config.name,
                service_type=acc_config.service,
                aid=aid,
            )
            bridge.add_accessory(accessory)
            self._accessories[acc_config.name] = accessory
            aid += 1

        self._driver.add_accessory(bridge)

    async def start(self) -> None:
        try:
            await self._driver.async_start()
            self.logger.info("AccessoryDriver started successfully")
        except Exception as e:
            self.logger.error(f"Error starting AccessoryDriver: {e}", exc_info=True)

    async def stop(self) -> None:
        try:
            await self._driver.async_stop()
            self.logger.info("AccessoryDriver stopped successfully")
        except Exception as e:
            self.logger.error(f"Error stopping AccessoryDriver: {e}", exc_info=True)

    def update_state(self, accessory_name: str, is_on: bool) -> None:
        if acc := self._accessories.get(accessory_name):
            acc.update_state(is_on)
        else:
            self.logger.warning(f"Unknown accessory name: {accessory_name}")
```

## Integration in HomekitService

```python
class HomekitService:
    def __init__(
        self,
        conbus_protocol: ConbusEventProtocol,
        homekit_config: HomekitConfig,
        conson_config: ConsonModuleListConfig,
        telegram_service: TelegramService,
        accessory_driver: HomekitAccessoryDriver,  # injected via DI
    ) -> None:
        ...
        self._accessory_driver = accessory_driver
        self._accessory_driver.set_callback(self._on_homekit_set)

    async def start(self) -> None:
        """Start the service and AccessoryDriver."""
        self.connect()
        await self._accessory_driver.start()

    async def stop(self) -> None:
        """Stop the AccessoryDriver and cleanup."""
        await self._accessory_driver.stop()
        self.cleanup()

    def _on_homekit_set(self, accessory_name: str, is_on: bool) -> None:
        """Called when HomeKit app toggles accessory."""
        config = self._find_accessory_config(accessory_name)
        if config:
            # on_action/off_action are telegram strings
            action = config.on_action if is_on else config.off_action
            self._conbus_protocol.send_raw_telegram(action)

    def _on_module_state_changed(self, state: AccessoryState) -> None:
        # ... existing code ...
        # Sync to HomeKit
        is_on = state.output_state == "ON"
        self._accessory_driver.update_state(state.accessory_name, is_on)
```

## Integration in HomekitApp

HomekitApp delegates AccessoryDriver lifecycle to HomekitService:

```python
class HomekitApp(App[None]):
    def __init__(
        self,
        homekit_service: HomekitService,
    ) -> None:
        super().__init__()
        self.homekit_service = homekit_service

    async def on_mount(self) -> None:
        await asyncio.sleep(0.5)
        await self.homekit_service.start()

    async def on_unmount(self) -> None:
        await self.homekit_service.stop()
```

## DI Registration (dependencies.py)

```python
container.register(HomekitAccessoryDriver, factory=lambda: HomekitAccessoryDriver(
    homekit_config=container.resolve(HomekitConfig),
))
```

## Checklist

- [ ] Add `pincode: str` field to NetworkConfig in homekit_config.py
- [ ] Add `accessory_state_file: str` field to NetworkConfig in homekit_config.py
- [ ] Add XPAccessory and HomekitAccessoryDriver to homekit_accessory_driver.py
- [ ] Inject HomekitAccessoryDriver into HomekitService
- [ ] Add `start()` and `stop()` async methods to HomekitService
- [ ] Add `_on_homekit_set` callback in HomekitService
- [ ] Update _on_module_state_changed to sync state to pyhap via accessory_driver
- [ ] Update HomekitApp to call `homekit_service.start()` / `stop()`
- [ ] Register HomekitAccessoryDriver in dependencies.py
