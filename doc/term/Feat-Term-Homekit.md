# TUI homekit implementation

use Textualize to build a tui equivalent of HomeKit

## Cli commmand

To start the Term app, use the following command

```shell

xp term homekit
```

## Term Window

```textualize

 ╭─ Rooms ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
 │  room / accessory                actions   state   dim     module     serial      type      status   output   updated   │
 │                                                                                                                         │
 │  Salon                                                                                                                  │
 │    - Variateur salon               a        ON     90%     A12       0020045056   XP33LED      OK     1      --:--:--   │
 │    - Variateur salle à manger      b        OFF      -     A12       0020045056   XP33LED      OK     2      --:--:--   │
 │    - Variateur cuisine             c        ON             A12       0020045056   XP33LED      OK     3      --:--:--   │
 │    - Prise salon                   d        ON             A5        0020044974   XP24         OK     2      --:--:--   │
 │    - Prise couloir cuisine         e        OFF            A5        0020044974   XP24         OK     3      --:--:--   │
 │    - Prise couloir cuisine 2       f        OFF            A5        0020044974   XP24         OK     4      --:--:--   │
 │    - Lumière couloir               g        ON             A5        0020044974   XP24         OK     1      --:--:--   │
 │    - Lumière blacon                h        ON             A6        0020044966   XP24         OK     4      --:--:--   │
 │                                                                                                                         │
 │  Parents                                                                                                                │
 │    - Lumiere dressing              i        ON             A6        0020044966   XP24         OK     1      --:--:--   │
 │    - Variateur parents             j        ON     90%     A13       0020045057   XP33LED      OK     2      --:--:--   │
 │    - Lumière mirroir douche        k        ON             A6        0020044966   XP24         OK     2      --:--:--   │
 │    - Variateur douche              l        OFF      -     A3        0020042796   XP33LR       OK     1      --:--:--   │
 │    - Prise parents 1               m        ON             A7        0020044989   XP24         OK     2      --:--:--   │
 │    - Prise parents 2               n        ON             A7        0020044989   XP24         OK     3      --:--:--   │
 │                                                                                                                         │
 │  Entrée                                                                                                                 │
 │    - Lumière entrée                o        ON             A8        0020044964   XP24         OK     1      --:--:--   │
 │    - Lumière mirroir sdb           p        ON             A8        0020044964   XP24         OK     2      --:--:--   │
 │    - Variateur sdb                 q        ON     10%     A3        0020042796   XP33LR       OK     2      --:--:--   │
 │    - Prise all                     r        ON             A2        0020037487   XP20         OK     3      --:--:--   │
 │    - Prise na                      s        ON             A2        0020037487   XP20         OK     2      --:--:--   │
 │    - All off                       t        ON             A2        0020037487   XP20         OK     1      --:--:--   │
 │                                                                                                                         │
 │  Bureau                                                                                                                 │
 │    - Variateur bureau              u        ON     20%     A13       0020045057   XP33LED      OK     1      --:--:--   │
 │    - Prise bureau                  v        ON             A9        0020044986   XP24         E10    1      --:--:--   │
 │                                                                                                                         │
 │  Chambre                                                                                                                │
 │    - Variateur chambre             w        ON     50%     A13       0020045057   XP33LED      OK     3      --:--:--   │
 │    - Prise chambre                 x        ON             A9        0020044986   XP24         E10    3      --:--:--   │
 │                                                                                                                         │
 ╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯ 
   ^Q Quit     ^[a-z] Actions                                                  Connected to 127.0.0.1  🟢    
```
### Widgets

- Room list
- Status footer

### Detail

The center top pane has module detail

### Columns:
- **Room**: Room name (Salon, Parents, Entrée, Bureau, Chambre)
- **Accessory**: Accessory name (Variateur salon, Lumière entrée, Prise bureau)
- **Action**: Action key (a,b,c,d ...) - triggers accessory actions (on_action, off_action, toggle_action, dimup_action, dimdown_action) from HomekitConfig
- **State**: Module output state (ON, OFF). Obtained from module status.
- **Dim**: For dimmable modules (XP33LR, XP33LED): show percentage if ON, show `-` if OFF, show empty if non-dimmable module
- **Module**: Module name/identifier (e.g., A1, A22)
- **serial number**: Module serial number (e.g., 0020041013)
- **module type**: Module type designation (e.g., XP130, XP230, XP24)
- **output**: module output linked to accessory.
- **last update**: Time elapsed since last communication (HH:MM:SS format). Shows `--:--:--` for modules that haven't been updated yet.


### Data source

#### Conson 

- File: conson.yml
- ConsonConfig

```yml
- name: A2
  serial_number: "0020037487"
  module_type: XP20
  module_type_code: 33
  link_number: 02
  module_number: 2
  auto_report_status: PP
  action_table:

- name: A3
...
```

#### homekit

- File: homekit.yml
- HomekitConfig

```yml

bridge:
  name: "Maison"
  rooms:
    - name: "Salon"
      accessories:
      - lumiere_salon
      - variateur_salon

accessories:
  - name: variateur_salon
    id: A12R1
    serial_number: "0020045056"
    output_number: 0
    on_action: E02L12I00
    off_action: E02L12I03
    description: Salon
    service: dimminglight

```

## Implementation

### Architecture

```
src/xp/
├── cli/
│   └── commands/
│       └── term/
│           ├── __init__.py
│           └── term_commands.py        # xp term homekit
│
├── services/
│   └── term/
│       ├── __init__.py
│       └── homekit_service.py         # Main TUI orchestrator
│
└── term/
    ├── __init__.py
    ├── homekit.py                     # Homekit TUI app 
    ├── homekit.tcss                   # Homekit style sheet
    └── widgets/
        ├── __init__.py
        └── room_list.py               # Main pane: room list
```

### Dependencies

Already existing in pyproject.toml:
- textual>=1.0.0

### Design Principles

1. **Separation of concerns**: Widgets are independent, reusable components
2. **Reactive state**: Use Textual reactive attributes for state updates
3. **Service layer**: Business logic stays in services, TUI only for display
4. **Type safety**: Full type hints, pass mypy strict mode
5. **No bloat**: Minimal dependencies, focus on core functionality


### Service

HomekitService

Wraps ConbusEventProtocol, ConsonModuleListConfig, HomekitConfig to provide high-level homekit for the TUI.

**Events (psygnal Signals):**
- `on_connection_state_changed: Signal(ConnectionState)` - Connection state changes (connected, disconnected, etc.)
- `on_room_list_updated: Signal(list[AccessoryState])` - Complete room and accessory list refreshed from HomekitConfig
- `on_module_state_changed: Signal(ModuleState)` - Individual module state updated (outputs, status, report)
- `on_module_error: Signal(str, str)` - Module error occurred (serial_number, error_code)
- `on_status_message: Signal(str)` - Status messages for TUI footer

**Data Model:**
```python
@dataclass
class AccessoryState:
    room_name: str               # Room name (Salon)
    accessory_name: str          # Accessory name (Variateur salon)
    action: str                  # Action on accessory (a: toggle on / off)
    output_state: str            # Output state (ON / OFF / -) use "-" if unknown
    dimming_state: str           # Dimming state of supported modules (XP33LED and XP33LR),
    module_name: str             # Module name (A1, A2, ... A22)
    serial_number: str           # Module serial number (0020045056)
    module_type: str             # Module type (XP130, XP230, XP24, ...)
    error_status: str            # Status: "OK" or error code "E10"
    output: int                  # Module output (1,2,3,4)
    last_update: datetime        # Last communication timestamp
```

**Signal Flow:**
```
ConbusEventProtocol Events → HomekitService → TUI Signals
    ↓
- TelegramReceivedEvent       → Parse output states → on_module_state_changed
- OutputStateReceivedEvent    → Update outputs    → on_module_state_changed
- ConnectionMadeEvent         → Load config       → on_room_list_updated
- InvalidTelegramReceived     → Extract error     → on_module_error
```

### Reference Implementation

The `ProtocolMonitorApp` (src/xp/term/protocol.py) serves as the reference implementation for this feature:
- Demonstrates the service + Textual app pattern
- Shows how to wire ProtocolMonitorService signals to TUI widgets
- Implements connection state management and live updates
- Provides examples of reactive widget updates from service events

Follow the same architectural patterns when implementing HomekitService and the module state TUI.

### Data Flow
```
CLI Command → Textual App → Widgets  → Term Service
                ↓              ↓           ↓
              State → Reactive Display → Conbus Service
```

### Key Features

1. **Module tree**: Expandable tree with module hierarchy
2. **Live updates**: Protocol messages update in real-time
3. **Keyboard navigation**: Vi-style keybindings (j/k for navigation)
4. **Action execution**: Select and execute actions from tree


## Implementation Checklist

Follow ProtocolMonitorApp pattern (src/xp/term/protocol.py) for reference.

### Models
- [ ] Create AccessoryState dataclass in src/xp/models/term/accessory_state.py
- [ ] Fields: room_name, accessory_name, action, output_state, dimming_state, module_name, serial_number, module_type, status, output, last_update
- [ ] Initialize last_update to None for modules not yet seen

### Service Layer
- [ ] Create HomekitService in src/xp/services/term/homekit_service.py
- [ ] Implement 5 psygnal Signals: on_connection_state_changed, on_room_list_updated, on_module_state_changed, on_module_error, on_status_message
- [ ] Load CliConfig from cli.yml on connection
- [ ] Load ConsonModuleListConfig from conson.yml on connection
- [ ] Load HomekitConfig from homekit.yml on connection
- [ ] Connect to ConbusEventProtocol signals (event-driven updates only)
- [ ] Handle TelegramReceivedEvent → update module outputs
- [ ] Handle OutputStateReceivedEvent → update module outputs
- [ ] Handle ConnectionMadeEvent → load config, emit on_room_list_updated
- [ ] Query module status to obtain error codes (OK or E10, etc.)
- [ ] Track last_update timestamp per module
- [ ] Implement refresh_all() method:
  - [ ] Filter modules by type (XP24, XP33LR, XP33LED)
  - [ ] Query module_output_state datapoint for each eligible module
  - [ ] Update outputs column with received state
  - [ ] Update last_update timestamp
- [ ] Implement context manager with cleanup

### Widgets
- [ ] Create RoomListWidget in src/xp/term/widgets/room_list.py
- [ ] Display DataTable with 10 columns (room / accessory, actions, state, dim, module, serial, type, status, out, updated)
- [ ] Use Textual reactive attributes for live updates
- [ ] Connect to service on_room_list_updated signal
- [ ] Connect to service on_module_state_changed signal
- [ ] Update table rows on signal events
- [ ] Format last_update: None → "--:--:--", datetime → elapsed time "HH:MM:SS"
- [ ] Format outputs: Empty string for modules without outputs
- [ ] Reuse StatusFooter widget in src/xp/term/widgets/status_footer.py
- [ ] Display connection state (Connected to IP 🟢)
- [ ] Show keyboard shortcuts (^u Update module, ^q Quit)
- [ ] Connect to service on_connection_state_changed signal
- [ ] Connect to service on_status_message signal

### Textual App
- [ ] Create HomekitApp in src/xp/term/homekit.py
- [ ] Compose RoomListWidget and StatusFooter
- [ ] Initialize HomekitService with ConbusEventProtocol, ConsonModuleListConfig, HomekitConfig
- [ ] Wire all service signals to widget update methods
- [ ] Implement keyboard bindings (ctrl+u, ctrl+q)
- [ ] Handle app lifecycle (on_mount, on_unmount)
- [ ] Call service cleanup on exit

### CLI Command
- [ ] Add homekit_command in src/xp/cli/commands/term/term_commands.py
- [ ] Command: xp term homekit
- [ ] Create ConbusEventProtocol instance
- [ ] Load cli.yml config
- [ ] Load conson.yml config
- [ ] Load homekit.yml config
- [ ] Initialize and run HomekitApp
- [ ] Setup Twisted reactor integration

### Quality
- [ ] Pass mypy strict type checking
- [ ] Follow Quality.md standards
- [ ] Follow Coding.md conventions
- [ ] Follow Architecture.md patterns
- [ ] Add docstrings to all public methods
- [ ] Handle error cases gracefully

### Quality Standards

Reference:
- Quality.md
- Coding.md
- Architecture.md