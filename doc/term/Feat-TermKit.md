# TUI homekit implementation

use Textualize to build a tui equivalent of HomeKit

## Cli commmand

To start the Term app, use the following command

```shell

xp term start
```

## Term Window

```textualize

 ╭─ Rooms ───────────────────────────────────────────╮
 │                                    states   keys  │
 │  Salon                                            │
 │    - Variateur salon                 ON      a    │
 │    - Variateur salle à manger        OFF     b    │
 │    - Variateur cuisine               ON      c    │
 │    - Prise salon                     ON      d    │
 │    - Prise couloir cuisine           OFF     e    │
 │    - Prise couloir cuisine 2         OFF     f    │
 │    - Lumière couloir                 ON      g    │
 │    - Lumière blacon                  ON      h    │
 │                                                   │
 │  Parents                                          │
 │    - Lumiere dressing                ON      i    │
 │    - Variateur parents               ON      j    │
 │    - Lumière mirroir douche          ON      k    │
 │    - Lumière douche                  ON      l    │
 │    - Prise parents 1                 ON      m    │
 │    - Prise parents 2                 ON      n    │
 │                                                   │
 │  Entrée                                           │
 │    - Lumière entrée                  ON      o    │
 │    - Lumière mirroir sdb             ON      p    │
 │    - Lumière sdb                     ON      q    │
 │    - Prise all                       ON      r    │
 │    - Prise na                        ON      s    │
 │    - All off                         ON      t    │
 │                                                   │
 │  Bureau                                           │
 │    - Variateur bureau                ON      u    │
 │    - Prise bureau                    ON      v    │
 │                                                   │
 │  Chambre                                          │
 │    - Variateur chambre               ON      w    │
 │    - Prise chambre                   ON      x    │
 │                                                   │
 ╰───────────────────────────────────────────────────╯ 
 ^q Quit  f1 Help
```

### Detail

The center top pane has module detail

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
│   └── term/
│       ├── __init__.py
│       └── tui_service.py              # Main TUI orchestrator
└── term/
    ├── __init__.py
    ├── app.py                          # Textual app entry point
    ├── widgets/
    │   ├── __init__.py
    │   └── modules_tree.py             # Left pane: module tree
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
CLI Command → Textual App → Widgets  → Term Service
                ↓              ↓           ↓
              State → Reactive Display → Conbus Service
```

### Key Features

1. **Module tree**: Expandable tree with module hierarchy
2. **Live updates**: Protocol messages update in real-time
3. **Keyboard navigation**: Vi-style keybindings (j/k for navigation)
4. **Action execution**: Select and execute actions from tree

### Quality Standards

Reference:
- Quality.md
- Coding.md
- Architecture.md