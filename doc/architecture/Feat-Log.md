# Logging

## Overview

The application uses Python's standard logging framework with structured configuration and custom formatting for protocol event tracking.

## Level Config

Logging levels are configured through the CLI with a `--log-level` flag supporting standard Python levels (DEBUG, INFO, WARNING, ERROR, CRITICAL). The configuration cascades from the root logger through to all module-level loggers, with specific loggers able to override the default level.

## Log Init

Logging is initialized at application startup through a centralized setup function. The initialization configures handlers, formatters, and log levels based on CLI arguments. Protocol-specific loggers are created for different communication layers (ConBus, Telegram, HomeKit) to enable granular filtering and routing.

## Console logging

Currently, all log output is directed to the console only. This approach works for development and real-time monitoring but lacks persistence for debugging and analysis.

### File logging
Add file-based logging alongside console output. File logs should support rotation, configurable paths, and persistent storage for post-mortem analysis and long-running deployments.
