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
  d Discover                                            q Quit   
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
- [ ] `src/xp/cli/commands/term/__init__.py` - Term command group (new)
- [ ] `src/xp/cli/commands/term/term_commands.py` - CLI command `xp term protocol`
- [ ] `src/xp/tui/__init__.py` - TUI module init
- [ ] `src/xp/tui/app.py` - Textual App entry point (composes widgets directly)
- [ ] `src/xp/tui/protocol.tcss` - Textual CSS styling
- [ ] `src/xp/tui/widgets/__init__.py` - Widgets module init
- [ ] `src/xp/tui/widgets/protocol_log.py` - Main protocol display widget
- [ ] `tests/unit/test_tui/test_protocol_log.py` - Widget unit tests

### 1. Dependencies
- [ ] Add `textual>=1.0.0` to pyproject.toml dependencies
- [ ] Run `pdm install` to update lock file

### 2. CLI Command Group
- [ ] Create `term/__init__.py` with `@click.group()` named `term`
- [ ] Register `term` group in `cli/main.py` main CLI
- [ ] Create `term_commands.py` with `@term.command("protocol")`
- [ ] Resolve ServiceContainer: `ctx.obj.get("container").get_container().resolve()`
- [ ] Initialize Textual app with container reference
- [ ] Call `app.run()` to start TUI (blocking until quit)
- [ ] NO business logic in command (delegate to app)

### 3. Textual App
- [ ] Create `ProtocolMonitorApp(App)` class in `tui/app.py`
- [ ] Store ServiceContainer reference in app instance
- [ ] Load CSS: `CSS_PATH = Path(__file__).parent / "protocol.tcss"`
- [ ] Compose widgets directly in `compose()` method (no screen layer - keep it simple)
- [ ] Bind keyboard shortcuts: `q` or `ctrl+c` for quit, `d` for discover
- [ ] Create `action_discover()` method to send discover telegram
- [ ] Pass container to widgets via constructor or app reference

### 4. Protocol Widget
Create `ProtocolLogWidget(Widget)` in `tui/widgets/protocol_log.py`:

**Connection State Management (CRITICAL)**:
- [ ] Define connection state enum: `DISCONNECTED`, `CONNECTING`, `CONNECTED`, `FAILED`
- [ ] Store current state in reactive attribute: `connection_state = reactive("DISCONNECTED")`
- [ ] Store protocol reference to prevent duplicate connections: `self.protocol = None`
- [ ] Display connection state in widget header or status line

**Reactor Integration (CRITICAL)**:
- [ ] Accept ServiceContainer in constructor
- [ ] Resolve `ConbusReceiveService` from container in `on_mount()`
- [ ] Use `self.set_timer()` to delay connection (e.g., 0.5s) - let UI render first
- [ ] In timer callback: **Check `self.protocol is None` before connecting** (race condition guard)
- [ ] Set state to `CONNECTING` before connection attempt
- [ ] Connect psygnal signals: `on_telegram_received`, `on_telegram_sent`, `on_timeout`, `on_failed`, `on_connection_made`
- [ ] Call `reactor.connectTCP()` with protocol config from `ConbusClientConfig`
- [ ] Store protocol reference: `self.protocol = service.conbus_protocol`
- [ ] DO NOT call `start_reactor()` - Textual's event loop handles both Twisted and Textual events
- [ ] Store messages in reactive list attribute (no limit - keep it simple)

**Signal Handlers**:
- [ ] `on_connection_made()`: Set state to `CONNECTED`, display "Connected" status
- [ ] `on_telegram_received()`: Append `[RX] {frame}` to message list
- [ ] `on_telegram_sent()`: Append `[TX] {frame}` to message list
- [ ] `on_timeout()`: Log timeout (continuous monitoring, no action needed)
- [ ] `on_failed(error)`: Set state to `FAILED`, display error message, call `self.app.exit()` after brief delay

**Discover Functionality**:
- [ ] Create `send_discover()` method called by app's `action_discover()`
- [ ] Send predefined telegram: `<S0000000000F01D00FA>` using protocol's `send_telegram()` or queue
- [ ] Display sent telegram in message list as `[TX]`

**Rendering**:
- [ ] Display connection status based on reactive `connection_state` attribute:
  - `DISCONNECTED`: Show nothing (initial state)
  - `CONNECTING`: Show "Connecting..." in yellow
  - `CONNECTED`: Show "Connected" in green (or hide after 2s)
  - `FAILED`: Show error message in red
- [ ] Use Textual reactive attributes for message list
- [ ] Apply green color to `[TX]` and `[RX]` markers using Rich markup
- [ ] Light gray/white for telegram frames
- [ ] No scroll handling - keep it simple (Textual handles basic scrolling)

**Cleanup**:
- [ ] Check `if self.protocol is not None` before cleanup
- [ ] Disconnect all signals in `on_unmount()`
- [ ] Close transport with `self.protocol.transport.loseConnection()` if connected
- [ ] Set `self.protocol = None` after cleanup
- [ ] Set connection state to `DISCONNECTED`

### 5. Styling (protocol.tcss)
Create `src/xp/tui/protocol.tcss` with color scheme matching Colors-And-Styles.png:
- [ ] Dark gray/black background for app and widgets
- [ ] Light gray borders for containers
- [ ] Green text for `[TX]` and `[RX]` markers (use Textual rich color tags)
- [ ] Light gray text for telegram content
- [ ] Footer with key bindings: `d Discover`, `q Quit`

### 6. Testing
- [ ] Mock `reactor` in tests to avoid event loop conflicts
- [ ] Test connection state transitions: DISCONNECTED → CONNECTING → CONNECTED
- [ ] Test connection state on failure: CONNECTING → FAILED
- [ ] Test race condition guard: multiple timer callbacks don't create duplicate connections
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

**POC Scope**: This is a proof-of-concept for TUI integration - keep it simple
- No screen layer - app composes widgets directly
- No scroll management - use Textual defaults
- No help screen - defer to later version
- No reconnection logic - quit app on connection failure
- No message limit - unbounded list for simplicity

**Event Loop**: Textual and Twisted share asyncio loop via `asyncioreactor`
- Textual's `app.run()` controls the loop
- `reactor.connectTCP()` schedules connection without blocking
- DO NOT call `start_reactor()` or `reactor.run()` in TUI code
- Delay connection slightly (0.5s) to let UI render first

**Service Reuse**: ConbusReceiveService works without modification
- Skip `start_reactor()` method only
- Use existing psygnal signals: `on_telegram_received`, `on_telegram_sent`, `on_timeout`, `on_failed`, `on_connection_made`
- All timeout logic works as-is
- No changes needed to existing service code

**ServiceContainer Scope** (CRITICAL):
- ConbusReceiveService is registered as **singleton** in ServiceContainer
- Multiple `resolve()` calls return the **same instance**
- Only call `resolve()` **once** in widget `on_mount()`
- Store protocol reference (`self.protocol`) to prevent duplicate connections
- Guard connection with `if self.protocol is None` check

**Configuration**: Always use cli.yml configuration
- Resolve `ConbusClientConfig` for connection parameters
- No command-line options for host/port in this POC
- Timeout set to None for continuous monitoring

**Discover Feature**: Send predefined telegram on `d` key press
- Telegram: `<S0000000000F01D00FA>`
- Sent via protocol's telegram queue
- Displayed as `[TX]` in message list

**Data Flow**: `CLI → App → Widget → Signals → Protocol → TCP`
- Widget connects to protocol signals on mount (delayed)
- Connection states: DISCONNECTED → CONNECTING → CONNECTED (or FAILED)
- Signals fire when telegrams arrive
- Reactive attributes (`connection_state`, `messages`) trigger automatic UI updates
- On error: display error, set state to FAILED, exit app after brief delay (no recovery)