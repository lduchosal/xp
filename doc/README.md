# XP Documentation

This directory contains all technical documentation for the XP project, organized by feature area to match the codebase structure.

## Directory Structure

```
doc/
├── conbus/         Conbus protocol, communication, and data point management
├── homekit/        HomeKit integration and configuration
├── actiontable/    Action table downloads and management for different XP models
├── telegram/       Telegram protocol, parsing, and event handling
├── cli/            Command-line interface features and utilities
├── modules/        Module types, versioning, and queries
├── output/         Output formats and serialization (JSON, XP formats)
├── architecture/   Architecture decisions, refactoring, and system design
├── maintenance/    Bug fixes, cleanup, technical debt, and maintenance tasks
└── specs/          Project specifications (Architecture, Coding, Quality)
```

## Feature Areas

### Conbus
Protocol-level communication, connection management, data points, scanning, emulation, and caching:
- Client/server communication
- Data point codes and management
- Link number operations
- Background state synchronization
- Auto-reporting and event handling
- Connection pooling

### HomeKit
Apple HomeKit integration:
- Configuration validation
- Bridge setup and management

### Action Table
Downloading and managing action tables from XP devices:
- Generic action table operations
- XP20, XP24, XP33 specific implementations
- Pseudocode and algorithm documentation

### Telegram
Low-level telegram (message) protocol handling:
- Telegram types and parsing
- System telegrams and replies
- Event telegrams
- File decoding utilities
- TelegramService refactoring

### CLI
Command-line interface features:
- CLI refactoring and structure
- Blink/unblink operations
- Click color management

### Modules
XP module information and queries:
- Module type detection
- Version parsing
- Serial number handling
- Click type identification

### Output
Data serialization and output formatting:
- JSON output
- XP-specific output formats

### Architecture
System architecture and major refactorings:
- Dependency injection (IoC)
- Service responsibilities
- Cache management
- Emulator specifications

### Maintenance
Bug fixes, code cleanup, and technical debt:
- Test fixes
- Encoding issues
- Unused code cleanup
- Cache removal
- Technical debt tracking

### Specs
High-level project specifications and guidelines:
- Architecture principles
- Coding standards
- Quality requirements

## Navigation

Each subdirectory contains feature-specific documentation. File names follow the convention:
- `Feat-*.md` - Feature implementation documentation
- `Fix-*.md` - Bug fix documentation
- `Chore-*.md` - Maintenance task documentation
- `Refactor-*.md` - Refactoring documentation

## Contributing

When adding new documentation:
1. Place it in the appropriate feature directory
2. Follow the naming convention above
3. Update this README if adding a new category
