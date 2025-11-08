# TUI Module state monitor

use Textualize to build a tui for XP
https://textual.textualize.io/

## Cli commmand

To start the TUI, use the following command

```shell

xp term start
```

## TUI Window

```textualize

 ╭─ Modules states ──────────────────────────────────────────────╮ ╭─ Protocol ──────────────────────────────╮  
 │  name    serial_number  module_type    output state    Status │ │ [TX] <S0020240110F02D01ED>              │  
 │  A01     0020041013     XP130                          OK     │ │ [TX] <S0020240110F02D01ED>              │  
 │  A01     0020030837     XP230                          OK     │ │ [RX] <E02L01I00MAK>                     │  
 │  A01     0020037487     XP20           0 1 0 0         OK     │ │ [RX] <E02L01I00MAK>                     │  
 │  A01     0020041824     XP20           0 1 0 0         OK     │ │ [RX] <E02L01I00MAK>                     │  
 │  A01     0020044991     XP24           0 1 0 0         OK     │ │ [RX] <E02L01I00MAK>                     │  
 │  A01     0020044974     XP24           0 1 0 0         OK     │ │ [RX] <E02L01I00MAK>                     │  
 │  A01     0020044989     XP24           0 1 0 0         OK     │ │ [RX] <E02L01I00MAK>                     │  
 │  A01     0020044964     XP24           0 1 0 0         OK     │ │ [RX] <E02L01I00MAK>                     │  
 │  A01     0020044986     XP24           0 1 0 0         OK     │ │ [RX] <E02L01I00MAK>                     │  
 │  A01     0020044966     XP24           0 1 0 0         OK     │ │ [RX] <E02L01I00MAK>                     │  
 │  A01     0020042796     XP33LR           0 1 0         OK     │ │ [RX] <E02L01I00MAK>                     │  
 │  A01     0020045056     XP33LED          0 1 0         OK     │ │ [RX] <E02L01I00MAK>                     │  
 │  A01     0020045057     XP33LED          0 1 0         OK     │ │ [RX] <E02L01I00MAK>                     │  
 │                                                               │ │                                         │  
 ╰───────────────────────────────────────────────────────────────╯ ╰─────────────────────────────────────────╯   
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