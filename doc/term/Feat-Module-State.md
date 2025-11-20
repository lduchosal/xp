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
 │  A07     0020044989     XP24           0 1 0 0      Y        OK      00:00:03     │
 │  A08     0020044964     XP24           0 1 0 0      Y        OK      00:00:03     │
 │  A09     0020044986     XP24           0 1 0 0      Y        OK      00:00:03     │
 │  A10     0020044966     XP24           0 1 0 0      Y        OK      00:00:03     │
 │  A11     0020042796     XP33LR           0 1 0      Y        OK      00:00:03     │
 │  A12     0020045056     XP33LED          0 1 0      Y        OK      00:00:03     │
 │  A13     0020045057     XP33LED          0 1 0      Y        OK      00:00:03     │
 │                                                                                   │
 ╰───────────────────────────────────────────────────────────────────────────────────╯ 
   ^u Update module   ^q Quit                             Connected to 127.0.0.1  🟢    
```
### Widgets

- module state
- status footer

### Keyboard Shortcuts

- **^u** (Ctrl+U): Refresh all module data - Force reload all module states from the system
- **^q** (Ctrl+Q): Quit the application

### Behavior Details

**Update Strategy**: Event-driven only
- Updates occur only when protocol events are received from ConbusEventProtocol
- No automatic polling or periodic refresh
- Manual refresh available via ^u keyboard shortcut

**Auto-report Mapping**:
- `auto_report_status: PP` in conson.yml → Display as `Y` in report column
- Other values → Display as `N`

**Error Status Source**:
- Error codes obtained from module status queries
- Displayed as error codes (e.g., `E10`) or `OK` for healthy modules

**Refresh Action Behavior**:
- Triggered by 'r' key press
- Iterates through all configured modules
- Filters modules by type: XP24, XP33LR, XP33LED
- Queries `module_output_state` datapoint for each eligible module
- Updates outputs column with received state
- Updates last_update timestamp for each queried module

### Columns:
- **name**: Module name/identifier (e.g., A01, A02) - Must be unique per module
- **serial number**: Module serial number (e.g., 0020041013)
- **module type**: Module type designation (e.g., XP130, XP230, XP24)
- **outputs**: Current output states (space-separated binary values). Empty string for modules without outputs.
- **report**: Auto-report status (Y/N). Derived from `auto_report_status` in conson.yml (PP → Y)
- **status**: Module status (OK, or error code like E10). Obtained from module status queries.
- **last update**: Time elapsed since last communication (HH:MM:SS format). Shows `--:--:--` for modules that haven't been updated yet.

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

## Implementation Checklist

Follow ProtocolMonitorApp pattern (src/xp/term/protocol.py) for reference.

### Models
- [ ] Create ModuleState dataclass in src/xp/models/term/module_state.py
- [ ] Fields: name, serial_number, module_type, outputs, auto_report, error_status, last_update
- [ ] Initialize last_update to None for modules not yet seen
- [ ] Store outputs as Optional[str] (empty string for modules without outputs)

### Service Layer
- [ ] Create StateMonitorService in src/xp/services/term/state_monitor_service.py
- [ ] Implement 5 psygnal Signals: on_connection_state_changed, on_module_list_updated, on_module_state_changed, on_module_error, on_status_message
- [ ] Load ConsonModuleListConfig from conson.yml on connection
- [ ] Connect to ConbusEventProtocol signals (event-driven updates only)
- [ ] Map auto_report_status field: PP → True (Y), others → False (N)
- [ ] Handle TelegramReceivedEvent → update module outputs
- [ ] Handle OutputStateReceivedEvent → update module outputs
- [ ] Handle ConnectionMadeEvent → load config, emit on_module_list_updated
- [ ] Query module status to obtain error codes (OK or E10, etc.)
- [ ] Track last_update timestamp per module
- [ ] Implement refresh_all() method:
  - [ ] Filter modules by type (XP24, XP33LR, XP33LED)
  - [ ] Query module_output_state datapoint for each eligible module
  - [ ] Update outputs column with received state
  - [ ] Update last_update timestamp
- [ ] Implement context manager with cleanup

### Widgets
- [ ] Create ModulesListWidget in src/xp/term/widgets/modules_list.py
- [ ] Display DataTable with 7 columns (name, serial_number, module_type, outputs, report, status, last_update)
- [ ] Use Textual reactive attributes for live updates
- [ ] Connect to service on_module_list_updated signal
- [ ] Connect to service on_module_state_changed signal
- [ ] Update table rows on signal events
- [ ] Format last_update: None → "--:--:--", datetime → elapsed time "HH:MM:SS"
- [ ] Format outputs: Empty string for modules without outputs
- [ ] Format report: bool → "Y"/"N" string
- [ ] Create StatusFooter widget in src/xp/term/widgets/status_footer.py
- [ ] Display connection state (Connected to IP 🟢)
- [ ] Show keyboard shortcuts (^u Update module, ^q Quit)
- [ ] Connect to service on_connection_state_changed signal
- [ ] Connect to service on_status_message signal

### Textual App
- [ ] Create StateMonitorApp in src/xp/term/state.py
- [ ] Compose ModulesListWidget and StatusFooter
- [ ] Initialize StateMonitorService with ConbusEventProtocol and ConsonModuleListConfig
- [ ] Wire all service signals to widget update methods
- [ ] Implement keyboard bindings (ctrl+u, ctrl+q)
- [ ] Handle app lifecycle (on_mount, on_unmount)
- [ ] Call service cleanup on exit

### CLI Command
- [ ] Add state_command in src/xp/cli/commands/term/term_commands.py
- [ ] Command: xp term state
- [ ] Load CLI config (IP, port)
- [ ] Create ConbusEventProtocol instance
- [ ] Load conson.yml config
- [ ] Initialize and run StateMonitorApp
- [ ] Setup Twisted reactor integration

### Quality
- [ ] Pass mypy strict type checking
- [ ] Follow Quality.md standards
- [ ] Follow Coding.md conventions
- [ ] Follow Architecture.md patterns
- [ ] Add docstrings to all public methods
- [ ] Handle error cases gracefully