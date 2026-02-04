# Feature: Graceful Shutdown for Term Commands

## Overview

The `xp term` commands (protocol, state, homekit) need proper signal handling and PID file management to ensure clean shutdown when terminated via SIGINT (Ctrl+C) or SIGTERM (kill).

## Problem Statement

Currently:
- `ProtocolMonitorApp` has no `on_unmount()` method - TCP connections leak on exit
- No OS-level signal handlers at CLI command level
- Hard termination (SIGTERM) bypasses Textual's cleanup entirely
- Twisted reactor and queue manager threads may be left running
- No PID file support - FreeBSD rc.d script cannot reliably track/stop the Python process

## Goals

1. Graceful cleanup on SIGINT (Ctrl+C) and SIGTERM
2. Close TCP connections properly
3. Stop Twisted reactor
4. Disconnect blinker signals
5. Stop HomeKit accessory driver (for homekit command)
6. PID file management (write on start, remove on exit)

## Reference Implementation

See `src/xp/cli/commands/reverse_proxy_commands.py` lines 82-98 for the existing signal handling pattern used in the reverse proxy command.

## Scope

### Files to Modify

| File | Change |
|------|--------|
| `src/xp/term/protocol.py` | Add `on_unmount()` method |
| `src/xp/cli/main.py` | Add `--pid-file` option to root `cli` group, store in `ctx.obj` |
| `src/xp/cli/utils/pid_file.py` | New file: `write_pid_file()` and `remove_pid_file()` helpers |
| `src/xp/cli/commands/term/term_commands.py` | Add signal handlers, read `pid_file` from `ctx.obj` |

### Out of Scope

- Changes to service layer (cleanup methods already exist)
- Changes to ConbusEventProtocol (stop_reactor already exists)
- Widget-level changes (already have on_unmount)

## Implementation

### 1. Add `on_unmount()` to ProtocolMonitorApp

Location: `src/xp/term/protocol.py`

Add method to `ProtocolMonitorApp` class:
- Call `self.protocol_service.cleanup()`
- Follow same pattern as `StateMonitorApp.on_unmount()` in `state.py:100-102`

### 2. Add Signal Handlers to Term Commands

Location: `src/xp/cli/commands/term/term_commands.py`

For each command (protocol_monitor, state_monitor, homekit_monitor):

1. Store app instance in a variable accessible to signal handler
2. Register `signal.SIGINT` and `signal.SIGTERM` handlers before calling `app.run()`
3. In signal handler:
   - Call `app.exit()` to trigger Textual's graceful shutdown
   - This will invoke `on_unmount()` which calls service cleanup

### Signal Handler Pattern

```
def create_signal_handler(app_instance):
    def handler(signum, frame):
        app_instance.exit()
    return handler

signal.signal(signal.SIGINT, create_signal_handler(app))
signal.signal(signal.SIGTERM, create_signal_handler(app))
app.run()
```

### 3. Add `--pid-file` Option to Root CLI

Location: `src/xp/cli/main.py`

Add Click option to the root `cli` group (alongside `--cli-config` and `--log-config`):

```
@click.option(
    "--pid-file",
    "-p",
    default=None,
    help="Path to PID file (written on start, removed on exit)",
    type=click.Path(),
)
```

Store in context:
```
ctx.obj["pid_file"] = pid_file
```

#### Usage

```sh
xp --pid-file=/var/run/consonxp.pid term protocol
```

#### PID File Lifecycle

1. **On start** (before `app.run()` in term commands):
   - If `ctx.obj["pid_file"]` set, write current PID to file
   - Use `os.getpid()` to get current process ID
   - Create parent directories if needed

2. **On exit** (in finally block after `app.run()` returns):
   - If PID file was written, remove it
   - Use try/except to handle file already deleted

#### PID File Helper

Create utility in `src/xp/cli/utils/pid_file.py`:

```
from pathlib import Path
import os

def write_pid_file(path: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(str(os.getpid()))

def remove_pid_file(path: str) -> None:
    try:
        Path(path).unlink()
    except FileNotFoundError:
        pass
```

#### Updated Term Command Pattern

Location: `src/xp/cli/commands/term/term_commands.py`

```
@term.command("protocol")
@click.pass_context
def protocol_monitor(ctx: Context) -> None:
    from xp.cli.utils.pid_file import write_pid_file, remove_pid_file

    app = ctx.obj.get("container").get_container().resolve(ProtocolMonitorApp)
    pid_file = ctx.obj.get("pid_file")

    if pid_file:
        write_pid_file(pid_file)

    def signal_handler(signum, frame):
        app.exit()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        app.run()
    finally:
        if pid_file:
            remove_pid_file(pid_file)
```

## Cleanup Chain

When signal received:
```
SIGINT/SIGTERM
  → signal handler calls app.exit()
    → Textual triggers on_unmount()
      → service.cleanup()
        → disconnect blinker signals
        → close transport (TCP)
        → stop reactor (if running)
    → app.run() returns
      → finally block removes PID file
```

## Testing

### Manual Test - Signal Handling

1. Start: `xp term protocol`
2. Verify connection established
3. Send SIGTERM: `kill -TERM <pid>`
4. Verify clean exit (no error messages, no zombie processes)

### Manual Test - PID File

1. Start: `xp --pid-file=/tmp/consonxp/protocol.pid term protocol`
2. Verify PID file created: `cat /tmp/consonxp/protocol.pid`
3. Verify PID matches: `ps -p $(cat /tmp/consonxp/protocol.pid)`
4. Send SIGTERM: `kill -TERM $(cat /tmp/consonxp/protocol.pid)`
5. Verify PID file removed: `ls /tmp/consonxp/protocol.pid` (should not exist)

### Verify No Leaks

After termination, check:
- No orphan Python processes
- No open TCP connections to Conbus gateway
- tmux session properly handles app exit
- PID file removed

## Acceptance Criteria

### Signal Handling
- [ ] `xp term protocol` exits cleanly on Ctrl+C
- [ ] `xp term protocol` exits cleanly on SIGTERM
- [ ] `xp term state` exits cleanly on Ctrl+C and SIGTERM
- [ ] `xp term homekit` exits cleanly on Ctrl+C and SIGTERM
- [ ] No error messages or stack traces on clean shutdown
- [ ] TCP connection closed before process exits

### PID File
- [ ] `--pid-file` option available on all three commands
- [ ] PID file created on start when option provided
- [ ] PID file contains correct process ID
- [ ] PID file removed on clean exit (Ctrl+C, SIGTERM)
- [ ] PID file removed even if app crashes (via finally block)
- [ ] Works without `--pid-file` (option is optional)

## FreeBSD Integration

Update `scripts/FreeBSD/bin/start` to use PID files:

```sh
xp --pid-file=/var/run/consonxp/protocol.pid term protocol
xp --pid-file=/var/run/consonxp/homekit.pid term homekit
```

Note: `/var/run/consonxp/` must be writable by the `consonxp` user. Create directory in rc.d script if needed:

```sh
mkdir -p /var/run/consonxp
chown consonxp:consonxp /var/run/consonxp
```

Update `scripts/FreeBSD/rc.d/consonxp` stop command to kill both PIDs.
