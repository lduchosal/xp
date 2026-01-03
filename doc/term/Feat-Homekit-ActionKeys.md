# HomeKit Action Keys Enhancement

Select accessory by action key, then perform action on selection.

## Key Bindings

### Selection Keys
| Key      | Action                             |
|----------|------------------------------------|
| `a-z0-9` | Select accessory row by action key |

### Action Keys (on selected accessory)
| Key     | Action          | Telegram        |
|---------|-----------------|-----------------|
| `Space` | Toggle          | `toggle_action` |
| `+`     | Turn ON         | `on_action`     |
| `-`     | Turn OFF        | `off_action`    |
| `*`     | Increase dimmer | TBD             |
| `ç`     | Decrease dimmer | TBD             |

### Reserved Keys
| Key | Binding            |
|-----|--------------------|
| `Q` | Quit               |
| `C` | Connect/Disconnect |
| `R` | Refresh            |

## Implementation

### HomekitService

Remove `turn_on_accessory(action_key)` and `turn_off_accessory(action_key)`.

Add methods that operate on accessory ID directly:

```python
def select_accessory(self, action_key: str) -> Optional[str]:
    """
    Get accessory ID for action key.

    Args:
        action_key: Action key (a-z0-9).

    Returns:
        Accessory ID if found, None otherwise.
    """
    return self._action_map.get(action_key)

def toggle_selected(self, accessory_id: str) -> bool:
    """Toggle accessory by ID."""
    state = self._accessory_states.get(accessory_id)
    if not state or not state.toggle_action:
        return False
    self.send_action(state.toggle_action)
    self.on_status_message.emit(f"Toggling {state.accessory_name}")
    return True

def turn_on_selected(self, accessory_id: str) -> bool:
    """Turn on accessory by ID."""
    config = self._find_accessory_config_by_id(accessory_id)
    state = self._accessory_states.get(accessory_id)
    if not config or not state:
        return False
    self.send_action(config.on_action)
    self.on_status_message.emit(f"Turning ON {state.accessory_name}")
    return True

def turn_off_selected(self, accessory_id: str) -> bool:
    """Turn off accessory by ID."""
    config = self._find_accessory_config_by_id(accessory_id)
    state = self._accessory_states.get(accessory_id)
    if not config or not state:
        return False
    self.send_action(config.off_action)
    self.on_status_message.emit(f"Turning OFF {state.accessory_name}")
    return True

def increase_dimmer(self, accessory_id: str) -> bool:
    """Increase dimmer level for accessory."""
    # TBD: Implement dimmer control
    pass

def decrease_dimmer(self, accessory_id: str) -> bool:
    """Decrease dimmer level for accessory."""
    # TBD: Implement dimmer control
    pass
```

### HomekitApp

Track selected accessory and handle action keys:

```python
class HomekitApp(App[None]):
    selected_accessory_id: Optional[str] = None

    def on_key(self, event: Any) -> None:
        key = event.key

        # Selection keys (a-z0-9)
        if len(key) == 1 and (("a" <= key <= "z") or ("0" <= key <= "9")):
            accessory_id = self.homekit_service.select_accessory(key)
            if accessory_id:
                self.selected_accessory_id = accessory_id
                self._highlight_row(key)
                event.prevent_default()
            return

        # Action keys (require selection)
        if not self.selected_accessory_id:
            return

        if key == "space":
            self.homekit_service.toggle_selected(self.selected_accessory_id)
            event.prevent_default()
        elif key == "plus" or key == "+":
            self.homekit_service.turn_on_selected(self.selected_accessory_id)
            event.prevent_default()
        elif key == "minus" or key == "-":
            self.homekit_service.turn_off_selected(self.selected_accessory_id)
            event.prevent_default()
        elif key == "asterisk" or key == "*":
            self.homekit_service.increase_dimmer(self.selected_accessory_id)
            event.prevent_default()
        elif key == "ç":
            self.homekit_service.decrease_dimmer(self.selected_accessory_id)
            event.prevent_default()

    def _highlight_row(self, action_key: str) -> None:
        """Highlight the row corresponding to action key in RoomListWidget."""
        if self.room_list_widget:
            self.room_list_widget.select_by_action_key(action_key)
```

### RoomListWidget

Add method to select/highlight row by action key:

```python
def select_by_action_key(self, action_key: str) -> None:
    """Select and highlight row by action key."""
    # Find row index for action key and move cursor
    for row_index, row_key in enumerate(self._row_keys):
        if row_key == action_key:
            self.move_cursor(row=row_index)
            break
```

## Checklist

### Service Layer
- [ ] Remove `turn_on_accessory(action_key)` method
- [ ] Remove `turn_off_accessory(action_key)` method
- [ ] Add `select_accessory(action_key) -> Optional[str]` method
- [ ] Add `toggle_selected(accessory_id) -> bool` method
- [ ] Add `turn_on_selected(accessory_id) -> bool` method
- [ ] Add `turn_off_selected(accessory_id) -> bool` method
- [ ] Add `increase_dimmer(accessory_id) -> bool` method (stub)
- [ ] Add `decrease_dimmer(accessory_id) -> bool` method (stub)

### TUI Layer
- [ ] Add `selected_accessory_id` state to HomekitApp
- [ ] Update `on_key` to handle selection keys (a-z0-9)
- [ ] Update `on_key` to handle action keys (space, +, -, *, ç)
- [ ] Add `_highlight_row(action_key)` method
- [ ] Add `select_by_action_key(action_key)` to RoomListWidget

### Tests
- [ ] Update tests for new key handling
- [ ] Add tests for selection + action flow
