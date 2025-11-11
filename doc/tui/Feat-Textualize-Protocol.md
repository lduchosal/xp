# TUI Module protocol monitor

use Textualize to build a tui for XP
https://textual.textualize.io/

## Cli commmand

To start the TUI, use the following command

```shell

xp term start
```

## TUI Window

```textualize

╭─ Protocol ───────────────────────────────────────────────────╮  
│ [TX] <S0020240110F02D01ED>                                   │  
│ [TX] <S0020240110F02D01ED>                                   │  
│ [RX] <E02L01I00MAK>                                          │  
│ [RX] <E02L01I00MAK>                                          │  
│ [RX] <E02L01I00MAK>                                          │  
│ [RX] <E02L01I00MAK>                                          │  
│ [RX] <E02L01I00MAK>                                          │  
│ [RX] <E02L01I00MAK>                                          │  
│ [RX] <E02L01I00MAK>                                          │  
│ [RX] <E02L01I00MAK>                                          │  
│ [RX] <E02L01I00MAK>                                          │  
│ [RX] <E02L01I00MAK>                                          │  
│ [RX] <E02L01I00MAK>                                          │  
│ [RX] <E02L01I00MAK>                                          │  
│                                                              │  
╰──────────────────────────────────────────────────────────────╯   
 ^q Quit  f1 Help
```

### Protocol

The main pane has the protocol communication

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
    │   └── protocol_log.py             # Main pane: protocol log
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

1. **Protocol monitoring**: Live RX/TX message stream

### Quality Standards

- Type hints: 100% coverage
- Docstrings: flake8-docstrings compliant (D,DCO)
- Tests: Unit tests for widgets and services
- Format: black, isort, ruff
- Linting: flake8, mypy strict mode