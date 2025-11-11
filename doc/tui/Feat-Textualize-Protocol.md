# TUI Module protocol monitor

use Textualize to build a tui for XP
https://textual.textualize.io/

## Cli commmand

To start the TUI, use the following command

```shell

xp term protocol
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
  f1 Help  d Discover                                  ^q Quit   
```
### Colors and style

The TUI uses a dark theme with green accent colors for optimal readability in terminal environments:

- **Background**: Dark gray/black background for the main application
- **Border**: Light gray borders for panels and containers
- **Title**: Gray text for panel headers (e.g., "Protocol")
- **TX Messages**: Green color for `[TX]` direction markers
- **RX Messages**: Green color for `[RX]` direction markers
- **Message Content**: Light gray/white text for protocol message data (enclosed in angle brackets)

Example output:
```
[TX] <S0020240110F02D01ED>  # Green [TX], light gray message content
[RX] <E02L01I00MAK>         # Green [RX], light gray message content
```

The green color scheme provides:
- Clear visual distinction between direction markers and message data
- Good contrast against the dark background
- Reduced eye strain during extended monitoring sessions

Reference screenshot: Colors-And-Styles.png

## Implementation Checklist

**References**: [Quality.md](../Quality.md) | [Coding.md](../Coding.md) | [Architecture.md](../Architecture.md)

### File Structure
Create these files following the architecture pattern:
- [ ] `src/xp/cli/commands/term/term_commands.py` - CLI command for `xp term protocol`
- [ ] `src/xp/tui/app.py` - Textual App entry point
- [ ] `src/xp/tui/widgets/protocol_log.py` - Main protocol display widget
- [ ] `src/xp/tui/screens/main_screen.py` - Screen layout manager
- [ ] `tests/unit/test_tui/test_protocol_log.py` - Widget unit tests

### 1. Dependencies
- [ ] Add `textual>=1.0.0` to pyproject.toml dependencies
- [ ] Run `pdm install` to update lock file

### 2. CLI Command
- [ ] Create `term_commands.py` with Click command `protocol`
- [ ] Resolve ServiceContainer from context: `ctx.obj["container"]`
- [ ] Initialize Textual app with container reference
- [ ] Call `app.run()` to start TUI
- [ ] NO business logic in command (delegate to app)

### 3. Textual App
- [ ] Create `ProtocolMonitorApp(App)` class in `tui/app.py`
- [ ] Store ServiceContainer reference in app instance
- [ ] Compose main screen in `compose()` method
- [ ] Bind keyboard shortcuts: `^q` for quit, `f1` for help, `d` for discover
- [ ] Set CSS styling for dark theme with green accents

### 4. Protocol Widget
Create `ProtocolLogWidget(Widget)` in `tui/widgets/protocol_log.py`:

**Reactor Integration (CRITICAL)**:
- [ ] Resolve `ConbusReceiveService` from container in `on_mount()`
- [ ] Connect psygnal signals: `on_telegram_received`, `on_telegram_sent`, `on_timeout`, `on_failed`
- [ ] Call `reactor.connectTCP()` with protocol config (DO NOT call `start_reactor()`)
- [ ] Textual's event loop handles both Twisted and Textual events automatically
- [ ] Store messages in reactive list attribute for auto-refresh

**Signal Handlers**:
- [ ] `on_telegram_received()`: Append `[RX] {frame}` to message list
- [ ] `on_telegram_sent()`: Append `[TX] {frame}` to message list
- [ ] `on_timeout()`: Log timeout (continuous monitoring, no action needed)
- [ ] `on_failed()`: Display error message in widget

**Rendering**:
- [ ] Use Textual reactive attributes for message list
- [ ] Apply green color to `[TX]` and `[RX]` markers
- [ ] Light gray/white for telegram frames
- [ ] Auto-scroll to newest messages

**Cleanup**:
- [ ] Disconnect all signals in `on_unmount()`
- [ ] Close transport with `transport.loseConnection()`

### 5. Styling
Apply color scheme matching Colors-And-Styles.png:
- [ ] Dark gray/black background
- [ ] Light gray borders
- [ ] Green text for `[TX]` and `[RX]` markers
- [ ] Light gray text for telegram content
- [ ] Footer with key bindings: `f1 Help`, `d Discover`, `^q Quit`

### 6. Testing
- [ ] Mock `reactor` in tests to avoid event loop conflicts
- [ ] Test widget signal handlers with mock events
- [ ] Test keyboard bindings and app lifecycle
- [ ] Verify 75% minimum coverage: `pdm test-cov`
- [ ] Run `pdm test-quick` before commit

### 7. Quality Checks
Run all checks before committing:
- [ ] `pdm format` - Black formatting (88 char line length)
- [ ] `pdm lint` - Ruff linting
- [ ] `pdm typecheck` - Mypy strict mode (100% type hints)
- [ ] `pdm absolufy` - Convert to absolute imports
- [ ] `pdm refurb` - Code modernization
- [ ] `pdm check` - Full quality suite

### 8. Documentation
- [ ] Module-level docstrings for all files
- [ ] Class docstrings explaining purpose
- [ ] Method docstrings with Args, Returns, Raises
- [ ] Pass `pdm run flake8 --select=D,DCO` (docstring checker)

### Critical Integration Notes

**Event Loop**: Textual and Twisted share asyncio loop via `asyncioreactor`
- Textual's `app.run()` controls the loop
- `reactor.connectTCP()` schedules connection without blocking
- DO NOT call `start_reactor()` or `reactor.run()` in TUI code

**Service Reuse**: ConbusReceiveService works without modification
- Skip `start_reactor()` method only
- All signals, callbacks, and timeout logic works as-is
- No changes needed to existing service code

**Data Flow**: `CLI → App → Widget → Signals → Protocol → TCP`
- Widget connects to protocol signals on mount
- Signals fire when telegrams arrive
- Reactive attributes trigger automatic UI updates