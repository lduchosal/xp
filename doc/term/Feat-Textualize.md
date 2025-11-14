# Terminal UI with Textualize

use Textualize to build a tui for XP
https://textual.textualize.io/

## Cli commmand

To start the TUI, use the following command

```shell

xp term start
```

## TUI Window

```textualize

 ╭─ Modules ─────────╮ ╭─ Detail ────────────────────────────────────────────────────────────────────╮ ╭─ Protocol ──────────────────────────────╮  
 │ ▼ XP130           │ │  name: A13                      input_state: xxx00000                       │ │ [TX] <E02L01I00MAK>                     │  
 │ ├─ 0020041013     │ │  serial_number: 0020045057      output_state: xxxxx000                      │ │ [TX] <S0020240110F02D01ED>              │  
 │ └─ 0020030837     │ │  module_type: XP33LED           fw_crc: PGJALJLM                            │ │ [RX] <E02L01I00MAK>                     │  
 │ ▼ XP20            │ │  link_number: 13                action_table_crc: MHIEIJBG                  │ │ [RX] <E02L01I00MAK>                     │  
 │ ├─ 0020037487     │ │  module_type_code: 35           light_level: 00:000[%],01:000[%],02:000[%]  │ │ [RX] <E02L01I00MAK>                     │  
 │ └─ 0020041824     │ │  hw_version: XP33LED_HW_VER1    operating_hours: ??                         │ │ [RX] <E02L01I00MAK>                     │  
 │ ▼ XP24            │ │  sw_version: XP33LED_V0.04.01   energy_level: ??                            │ │ [RX] <E02L01I00MAK>                     │  
 │ ├─ 0020044991     │ │  module_number: 2               temperature: -20,0\u00a7C                   │ │ [RX] <E02L01I00MAK>                     │  
 │ ├─ 0020044974     │ │  auto_report_status: PP         sw_top_version: ??                          │ │ [RX] <E02L01I00MAK>                     │  
 │ ├─ 0020044989     │ │  module_state: OFF              voltage: ??                                 │ │ [RX] <E02L01I00MAK>                     │  
 │ ├─ 0020044964     │ │  module_error_code: 00                                                      │ │ [RX] <E02L01I00MAK>                     │  
 │ ├─ 0020044986     │ ╰─────────────────────────────────────────────────────────────────────────────╯ │ [RX] <E02L01I00MAK>                     │  
 │ └─ 0020044966     │ ╭─ Actions ──────────────────────────╮ ╭─ Action table ▼ ─────────────────────╮ │ [RX] <E02L01I00MAK>                     │  
 │ ▼ XP33LR          │ │ ▼ Datapoint                        │ │  CP20 0 0 > 0 OFF                    │ │ [RX] <E02L01I00MAK>                     │  
 │ └─ 0020042796     │ │ ├─ link_number                     │ │  CP20 0 0 > 1 OFF                    │ │ [RX] <E02L01I00MAK>                     │  
 │ ▼ XP33LED         │ │ ╰─ auto_report_status              │ │  CP20 0 0 > 2 OFF                    │ │ [RX] <E02L01I00MAK>                     │  
 │ ├─ 0020045056     │ │ ▼ Led                              │ │  CP20 0 8 > 0 ON                     │ │ [RX] <E02L01I00MAK>                     │  
 │ └─ 0020045057     │ │ ├─ blink                           │ │  CP20 0 8 > 1 ON                     │ │ [RX] <E02L01I00MAK>                     │  
 │                   │ │ ╰─ unblink                         │ │  CP20 0 8 > 2 ON                     │ │ [RX] <E02L01I00MAK>                     │  
 │                   │ │ ▶ Light level                      │ │  CP20 3 0 > 0 ON                     │ │                                         │  
 │                   │ │ ▶ Outputs                          │ │  CP20 3 1 > 1 ON                     │ │                                         │  
 │                   │ │ ▶ Action table                     │ │  CP20 3 2 > 2 ON                     │ │                                         │  
 │                   │ │ ▶ Ms Action table                  │ │  CP20 3 3 > 0 OFF                    │ │                                         │  
 │                   │ │ ▶ Discover                         │ │  CP20 3 4 > 1 OFF                    │ │                                         │  
 │                   │ │ ▶ Raw                              │ │  CP20 3 5 > 2 OFF                    │ │                                         │  
 │                   │ │ ▶ Custom                           │ │                                      │ │                                         │  
 │                   │ │ ▶ Reset                            │ │                                      │ │                                         │  
 ╰───────────────────╯ ╰────────────────────────────────────╯ ╰──────────────────────────────────────╯ ╰─────────────────────────────────────────╯   
 ^q Quit  f1 Help
```

### Modules

The left pane, has the module list

### Detail

The center top pane has module detail

### Actions

The center bottom left pane has an action list

### Action table

The center bottom right pane has an action list

### Protocol

The right pane has the protocol communication

## Implementation

### Architecture

```
src/xp/
├── cli/
│   └── commands/
│       └── term/
│           ├── __init__.py
│           └── term_commands.py        # xp term start
├── services/
│   └── tui/
│       ├── __init__.py
│       ├── tui_service.py              # Main TUI orchestrator
│       └── tui_state.py                # Shared state management
└── tui/
    ├── __init__.py
    ├── app.py                          # Textual app entry point
    ├── widgets/
    │   ├── __init__.py
    │   ├── modules_tree.py             # Left pane: module tree
    │   ├── detail_panel.py             # Top center: module details
    │   ├── actions_tree.py             # Bottom left: actions tree
    │   ├── actiontable_list.py         # Bottom right: action table
    │   └── protocol_log.py             # Right pane: protocol log
    └── screens/
        ├── __init__.py
        └── main_screen.py              # Main layout screen
```

### Dependencies

Add to pyproject.toml:
- textual>=1.0.0

### Design Principles

1. **Separation of concerns**: Widgets are independent, reusable components
2. **Reactive state**: Use Textual reactive attributes for state updates
3. **Service layer**: Business logic stays in services, TUI only for display
4. **Type safety**: Full type hints, pass mypy strict mode
5. **No bloat**: Minimal dependencies, focus on core functionality

### Data Flow

```
CLI Command → TUI Service → Textual App → Widgets
                ↓              ↓           ↓
           Conbus Service → State → Reactive Display
```

### Key Features

1. **Module tree**: Expandable tree with module hierarchy
2. **Live updates**: Protocol messages update in real-time
3. **Keyboard navigation**: Vi-style keybindings (j/k for navigation)
4. **Action execution**: Select and execute actions from tree
5. **Protocol monitoring**: Live RX/TX message stream

### Quality Standards

- Type hints: 100% coverage
- Docstrings: flake8-docstrings compliant (D,DCO)
- Tests: Unit tests for widgets and services
- Format: black, isort, ruff
- Linting: flake8, mypy strict mode