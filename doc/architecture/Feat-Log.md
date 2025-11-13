# Logging

## Overview

The application uses Python's standard logging framework with structured configuration and custom formatting for protocol event tracking.

### Level Config

Logging levels will be configured through the CLI with a `--log-level` flag supporting standard Python levels (DEBUG, INFO, WARNING, ERROR, CRITICAL). The configuration cascades from the root logger through to all module-level loggers. Same level applies to both console and file handlers.

Reference: src/xp/cli/main.py (flag not yet implemented)

### Log Init

Logging is initialized at application startup in the CLI entry point (src/xp/cli/main.py:34-50). The initialization configures a StreamHandler with custom formatting including thread information and timestamps. Protocol-specific loggers are created via `logging.getLogger(__name__)` in service modules (e.g., src/xp/services/protocol/conbus_event_protocol.py, src/xp/services/conbus/conbus_receive_service.py) to enable granular filtering.

## Log output
### Console logging

Currently, all log output is directed to the console only. This approach works for development and real-time monitoring but lacks persistence for debugging and analysis.

### File logging
Add file-based logging alongside console output. File logs should support rotation, configurable paths, and persistent storage for post-mortem analysis and long-running deployments.

## Implementation Checklist

**Scope**: Add file logging for term app, maintain console logging for all CLI commands.

**References**: doc/Quality.md, doc/Coding.md, doc/Architecture.md

**Configuration**:
- Max file size: 1MB
- Backup count: 365 (1 per day for 365 days)
- Log path: Retrieved from conbus config, default ~/.xp/logs/term.log
- Auto-create log directory with warning on failure
- If file logging fails: warn and start app anyway

**Tasks**:

- [ ] Add `--log-level` flag to CLI main (src/xp/cli/main.py) with default DEBUG
- [ ] Add log_path field to ConbusClientConfig (src/xp/models/conbus/conbus_client_config.py)
- [ ] Create file handler setup function in term command (src/xp/cli/commands/term/term_commands.py)
- [ ] Add RotatingFileHandler (maxBytes=1MB, backupCount=365)
- [ ] Retrieve log path from conbus config, fallback to ~/.xp/logs/term.log
- [ ] Auto-create log directory with Path.mkdir(parents=True, exist_ok=True)
- [ ] Add try/except around file handler creation, warn on failure, continue startup
- [ ] Configure file formatter using same format as console
- [ ] Attach file handler to root logger in term command before app.run()
- [ ] Ensure both console and file handlers use same log level
- [ ] Unit test: file handler configuration with valid path
- [ ] Unit test: file handler failure handling (read-only directory)
- [ ] Integration test: verify log file creation and rotation
