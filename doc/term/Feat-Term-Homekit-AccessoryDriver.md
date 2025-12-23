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
    def __init__(self, homekit_config: HomekitConfig, on_set: Callable) -> None: ...
    async def start(self) -> None: ...
    async def stop(self) -> None: ...
    def update_state(self, accessory_id: str, is_on: bool) -> None: ...
```

### Accessory Mapping

| service type   | pyhap Service |
|----------------|---------------|
| `dimminglight` | Lightbulb + Brightness |
| `light`        | Lightbulb |
| `outlet`       | Outlet |

## Files

```
src/xp/services/term/
├── homekit_service.py  # existing class
└── homekit_accessory_driver.py  # Add HomekitAccessoryDriver class
```

## Config

Add `pincode` to HomekitConfig (homekit.yml):

```yaml
homekit:
  ip: 0.0.0.0
  port: 51826
  pincode: "031-45-154"

```

## Minimal Implementation

```python
from typing import Callable, Dict, Optional
import asyncio

from pyhap.accessory import Accessory, Bridge
from pyhap.accessory_driver import AccessoryDriver
from pyhap.const import CATEGORY_LIGHTBULB, CATEGORY_OUTLET
from pyhap.service import Service


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

        if service_type == "dimminglight":
            self.category = CATEGORY_LIGHTBULB
            serv = self.add_preload_service("Lightbulb", chars=["On", "Brightness"])
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

    def __init__(self, homekit_config: "HomekitConfig") -> None:
        loop = asyncio.get_event_loop()
        self._driver = AccessoryDriver(
            loop=loop,
            port=homekit_config.homekit.port,
            pincode=homekit_config.homekit.pincode.encode(),
            persist_file="./accessory.state",
        )
        self._accessories: Dict[str, XPAccessory] = {}
        self._on_set: Optional[Callable[[str, bool], None]] = None
        self._setup_bridge(homekit_config)

    def set_callback(self, on_set: Callable[[str, bool], None]) -> None:
        self._on_set = on_set

    def _setup_bridge(self, config: "HomekitConfig") -> None:
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
        await self._driver.async_start()

    async def stop(self) -> None:
        await self._driver.async_stop()

    def update_state(self, accessory_name: str, is_on: bool) -> None:
        if acc := self._accessories.get(accessory_name):
            acc.update_state(is_on)
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

    def _on_homekit_set(self, accessory_name: str, is_on: bool) -> None:
        """Called when HomeKit app toggles accessory."""
        config = self._find_accessory_config(accessory_name)
        if config:
            action = config.on_action if is_on else config.off_action
            self._conbus_protocol.send_raw_telegram(action)

    def _on_module_state_changed(self, state: AccessoryState) -> None:
        # ... existing code ...
        # Sync to HomeKit
        is_on = state.output_state == "ON"
        self._accessory_driver.update_state(state.accessory_name, is_on)
```

## Integration in HomekitApp

```python
class HomekitApp(App[None]):
    def __init__(
        self,
        homekit_service: HomekitService,
        accessory_driver: HomekitAccessoryDriver,  # injected via DI
    ) -> None:
        super().__init__()
        self.homekit_service = homekit_service
        self._accessory_driver = accessory_driver

    async def on_mount(self) -> None:
        await asyncio.sleep(0.5)
        self.homekit_service.connect()
        await self._accessory_driver.start()  # Start HAP driver

    async def on_unmount(self) -> None:
        await self._accessory_driver.stop()  # Stop HAP driver
        self.homekit_service.cleanup()
```

## DI Registration (dependencies.py)

```python
container.register(HomekitAccessoryDriver, factory=lambda: HomekitAccessoryDriver(
    homekit_config=container.resolve(HomekitConfig),
))
```

## Checklist

- [ ] Add `pincode: str` field to HomekitConfig in homekit_config.py
- [ ] Add XPAccessory and HomekitAccessoryDriver to homekit_accessory_driver.py
- [ ] Inject HomekitAccessoryDriver into HomekitService, add _on_homekit_set callback
- [ ] Update _on_module_state_changed to sync state to pyhap via accessory_driver
- [ ] Inject HomekitAccessoryDriver into HomekitApp
- [ ] Call accessory_driver.start() in HomekitApp.on_mount
- [ ] Call accessory_driver.stop() in HomekitApp.on_unmount
- [ ] Register HomekitAccessoryDriver in dependencies.py