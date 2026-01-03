# HomeKit Action Keys Enhancement

Add explicit on/off control via modifier keys in addition to existing toggle functionality.

## Reserved Keys

The following keys are reserved for app bindings and excluded from action key assignment:

| Key | Binding |
|-----|---------|
| `q` | Quit |
| `c` | Connect/Disconnect |
| `r` | Refresh |

**Implementation**: Define `RESERVED_KEYS = {"q", "c", "r"}` in `HomekitService` and skip these when assigning action keys during `_initialize_accessory_states()`.

## Current Behavior

| Key | Action |
|-----|--------|
| `a-z0-9` | Toggle accessory (sends `toggle_action`) |

## New Behavior

| Key | Action | Telegram |
|-----|--------|----------|
| `a-z0-9` | Toggle accessory | `toggle_action` |
| `ctrl+a-z0-9` | Turn accessory ON | `on_action` |
| `ctrl+shift+a-z0-9` | Turn accessory OFF | `off_action` |

## Configuration

Each accessory in `homekit.yml` already defines the required actions:

```yaml
accessories:
  - name: variateur_salon
    on_action: E02L12I00
    off_action: E02L12I03
    toggle_action: E02L12I02
```

## Implementation

### HomekitService

Add two new methods in `src/xp/services/term/homekit_service.py`:

```python
def turn_on_accessory(self, action_key: str) -> bool:
    """
    Turn on accessory by action key.

    Sends the on_action telegram for the accessory mapped to the given key.

    Args:
        action_key: Action key (a-z0-9).

    Returns:
        True if on command was sent, False otherwise.
    """
    accessory_id = self._action_map.get(action_key)
    if not accessory_id:
        return False

    state = self._accessory_states.get(accessory_id)
    if not state:
        return False

    config = self._find_accessory_config_by_id(accessory_id)
    if not config:
        self.logger.warning(f"No config for accessory {accessory_id}")
        return False

    self._conbus_protocol.send_raw_telegram(config.on_action)
    self.on_status_message.emit(f"Turning ON {state.accessory_name}")
    return True


def turn_off_accessory(self, action_key: str) -> bool:
    """
    Turn off accessory by action key.

    Sends the off_action telegram for the accessory mapped to the given key.

    Args:
        action_key: Action key (a-z0-9).

    Returns:
        True if off command was sent, False otherwise.
    """
    accessory_id = self._action_map.get(action_key)
    if not accessory_id:
        return False

    state = self._accessory_states.get(accessory_id)
    if not state:
        return False

    config = self._find_accessory_config_by_id(accessory_id)
    if not config:
        self.logger.warning(f"No config for accessory {accessory_id}")
        return False

    self._conbus_protocol.send_raw_telegram(config.off_action)
    self.on_status_message.emit(f"Turning OFF {state.accessory_name}")
    return True
```

Add helper method to find config by accessory_id:

```python
def _find_accessory_config_by_id(self, accessory_id: str) -> Optional[HomekitAccessoryConfig]:
    """
    Find accessory config by accessory ID.

    Args:
        accessory_id: Accessory ID (e.g., "A12_1").

    Returns:
        HomekitAccessoryConfig if found, None otherwise.
    """
    state = self._accessory_states.get(accessory_id)
    if not state:
        return None
    return self._find_accessory_config_by_output(state.serial_number, state.output)
```

Add reserved keys constant and update action key assignment:

```python
# Reserved keys that conflict with app bindings
RESERVED_KEYS: set[str] = {"q", "c", "r"}

def _initialize_accessory_states(self) -> None:
    """Initialize accessory states from HomekitConfig and ConsonModuleListConfig."""
    action_keys = "abcdefghijklmnopqrstuvwxyz0123456789"
    action_index = 0
    # ...

    for room in self._homekit_config.bridge.rooms:
        for accessory_name in room.accessories:
            # ... existing code ...

            # Skip reserved keys when assigning
            while (
                action_index < len(action_keys)
                and action_keys[action_index] in RESERVED_KEYS
            ):
                action_index += 1

            action_key = (
                action_keys[action_index] if action_index < len(action_keys) else ""
            )
            action_index += 1
            # ... rest of existing code ...
```

### HomekitApp

Update `on_key` method in `src/xp/term/homekit.py`:

```python
def on_key(self, event: Any) -> None:
    """
    Handle key press events for action keys.

    Intercepts action keys with modifiers:
    - a-z0-9: Toggle accessory
    - ctrl+a-z0-9: Turn accessory ON
    - ctrl+shift+a-z0-9: Turn accessory OFF

    Args:
        event: Key press event.
    """
    key = event.key

    # Check for ctrl+shift+key (OFF command)
    if key.startswith("ctrl+shift+"):
        base_key = key[11:].lower()  # Remove "ctrl+shift+" prefix
        if len(base_key) == 1 and (("a" <= base_key <= "z") or ("0" <= base_key <= "9")):
            if self.homekit_service.turn_off_accessory(base_key):
                event.prevent_default()
            return

    # Check for ctrl+key (ON command)
    if key.startswith("ctrl+"):
        base_key = key[5:].lower()  # Remove "ctrl+" prefix
        if len(base_key) == 1 and (("a" <= base_key <= "z") or ("0" <= base_key <= "9")):
            if self.homekit_service.turn_on_accessory(base_key):
                event.prevent_default()
            return

    # Plain key (toggle)
    key_lower = key.lower()
    if len(key_lower) == 1 and (("a" <= key_lower <= "z") or ("0" <= key_lower <= "9")):
        if self.homekit_service.toggle_accessory(key_lower):
            event.prevent_default()
```

## Status Messages

| Action | Status Message |
|--------|----------------|
| Toggle | `Toggling {accessory_name}` |
| ON | `Turning ON {accessory_name}` |
| OFF | `Turning OFF {accessory_name}` |

## Checklist

### Service Layer
- [ ] Define `RESERVED_KEYS = {"q", "c", "r"}` constant
- [ ] Update `_initialize_accessory_states()` to skip reserved keys
- [ ] Add `turn_on_accessory(action_key: str) -> bool` method
- [ ] Add `turn_off_accessory(action_key: str) -> bool` method
- [ ] Add `_find_accessory_config_by_id(accessory_id: str)` helper method
- [ ] Emit status messages for on/off actions

### TUI Layer
- [ ] Update `on_key` to detect `ctrl+` prefix for ON command
- [ ] Update `on_key` to detect `ctrl+shift+` prefix for OFF command
- [ ] Maintain existing toggle behavior for plain keys

### Documentation
- [ ] Update docstrings in `homekit.py`
- [ ] Update docstrings in `homekit_service.py`

### Quality
- [ ] Pass mypy strict type checking
- [ ] Follow existing code patterns
