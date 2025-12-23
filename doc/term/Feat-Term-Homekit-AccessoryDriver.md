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
| `switch`       | Switch |

## Files

```
src/xp/services/term/
└── homekit_service.py  # Add HomekitAccessoryDriver class + enable_homekit flag
```

## CLI

```shell
xp term homekit --apple-homekit --pincode 031-45-154
```

## Checklist

- [ ] Create HomekitAccessoryDriver wrapper
- [ ] Create Bridge with accessory factory
- [ ] Wire Conbus → pyhap (update_state)
- [ ] Wire pyhap → Conbus (setter_callback → send_raw_telegram)
- [ ] Add --apple-homekit CLI flag
- [ ] Integrate in HomekitApp.on_mount / on_unmount