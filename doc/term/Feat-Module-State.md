# TUI Module state monitor

use Textualize to build a tui for XP
https://textual.textualize.io/

## Cli commmand

To start the TUI, use the following command

```shell

xp term state
```

## Application

### Window

The main pane has module detail
```textualize

 ╭─ Modules states ──────────────────────────────────────────────────────────────────╮
 │  name    serial number  module type    outputs    report    status   last update  │
 │  A01     0020041013     XP130                       Y        OK      00:00:03     │
 │  A02     0020030837     XP230                       Y        E10     00:00:03     │
 │  A03     0020037487     XP20                        Y        OK      00:00:03     │
 │  A04     0020041824     XP20                        Y        OK      00:00:03     │
 │  A05     0020044991     XP24           0 1 0 0      Y        OK      00:00:03     │
 │  A06     0020044974     XP24           0 1 0 0      Y        OK      00:00:03     │
 │  A06     0020044989     XP24           0 1 0 0      Y        OK      00:00:03     │
 │  A07     0020044964     XP24           0 1 0 0      Y        OK      00:00:03     │
 │  A08     0020044986     XP24           0 1 0 0      Y        OK      00:00:03     │
 │  A09     0020044966     XP24           0 1 0 0      Y        OK      00:00:03     │
 │  A10     0020042796     XP33LR           0 1 0      Y        OK      00:00:03     │
 │  A11     0020045056     XP33LED          0 1 0      Y        OK      00:00:03     │
 │  A12     0020045057     XP33LED          0 1 0      Y        OK      00:00:03     │
 │                                                                                   │
 ╰───────────────────────────────────────────────────────────────────────────────────╯ 
   ^u Update module   ^q Quit                             Connected to 127.0.0.1  🟢    
```
### Widgets

- module state
- status footer

### Columns:
- **name**: Module name/identifier (e.g., A01, A02)
- **serial number**: Module serial number (e.g., 0020041013)
- **module type**: Module type designation (e.g., XP130, XP230, XP24)
- **outputs**: Current output states (space-separated binary values)
- **report**: Auto-report status (Y/N)
- **status**: Module status (OK, or error code like E10)
- **last update**: Time since last communication (HH:MM:SS)

### Data source

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

### Architecture

```
src/xp/
├── cli/
│   └── commands/
│       └── term/
│           └── term_commands.py        # xp term start
├── services/
│   └── term/
│       └── state_monitor_service.py    # service orchestrator
└── term/
    ├── state.py                        # Textual app entry point
    └── widgets/
        ├── __init__.py
        └── modules_list.py             # Left pane: module tree
```
### Service

StateMonitorService

Wraps ConbusEventProtocol and ConsonModuleListConfig to provide high-level module state tracking for the TUI.

**Events (psygnal Signals):**
- `on_connection_state_changed: Signal(ConnectionState)` - Connection state changes (connected, disconnected, etc.)
- `on_module_list_updated: Signal(list[ModuleState])` - Complete module list refreshed from config
- `on_module_state_changed: Signal(ModuleState)` - Individual module state updated (outputs, status, report)
- `on_module_error: Signal(str, str)` - Module error occurred (serial_number, error_code)
- `on_status_message: Signal(str)` - Status messages for TUI footer

**Data Model:**
```python
@dataclass
class ModuleState:
    name: str                    # Module name (A01, A02)
    serial_number: str           # Module serial number
    module_type: str             # Module type (XP130, XP230, XP24)
    outputs: Optional[str]       # Output states "0 1 0 0"
    auto_report: bool            # Auto-report enabled (Y/N)
    error_status: str            # Status: "OK" or error code "E10"
    last_update: datetime        # Last communication timestamp
```

**Signal Flow:**
```
ConbusEventProtocol Events → StateMonitorService → TUI Signals
    ↓
- TelegramReceivedEvent       → Parse output states → on_module_state_changed
- OutputStateReceivedEvent    → Update outputs    → on_module_state_changed
- ConnectionMadeEvent         → Load config       → on_module_list_updated
- InvalidTelegramReceived     → Extract error     → on_module_error
```

### Reference Implementation

The `ProtocolMonitorApp` (src/xp/term/protocol.py) serves as the reference implementation for this feature:
- Demonstrates the service + Textual app pattern
- Shows how to wire ProtocolMonitorService signals to TUI widgets
- Implements connection state management and live updates
- Provides examples of reactive widget updates from service events

Follow the same architectural patterns when implementing StateMonitorService and the module state TUI.

### Design Principles

1. **Separation of concerns**: Widgets are independent, reusable components
2. **Reactive state**: Use Textual reactive attributes for state updates
3. **Service layer**: Business logic stays in services, TUI only for display
4. **Type safety**: Full type hints, pass mypy strict mode
5. **No bloat**: Minimal dependencies, focus on core functionality

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
5. **Protocol monitoring**: Live RX/TX message stream

### Quality Standards

Reference:
- Quality.md
- Coding.md
- Architecture.md