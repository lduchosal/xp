# Feature Specification: Parse VERSION

## Overview
Add support for parsing VERSION information from Conbus system and reply telegrams.

## Message Examples
- System telegram: `<S0012345011F02D02FM>`
- Reply telegrams:
  - `<R0012345011F02D02XP230_V1.00.04FI>`
  - `<R0012345002F02D02XP20_V0.01.05GK>`
  - `<R0012345003F02D02XP33LR_V0.04.02HF>`
  - `<R0012345004F02D02XP24_V0.34.03GA>`
  - `<R0012345008F02D02XP24_V0.34.03GK>`
  - `<R0012345009F02D02XP24_V0.34.03GG>`
  - `<R0012345007F02D02XP24_V0.34.03GJ>`
  - `<R0012345010F02D02XP20_V0.01.05GO>`
  - `<R0012345006F02D02XP24_V0.34.03GI>`
  - `<R0012345005F02D02XP24_V0.34.03GL>`

## Requirements

### 1. System Telegram Parsing
- Parse system telegram requesting version information
- Extract module address and command type
- Validate telegram format and checksum

### 2. Reply Telegram Parsing
- Parse reply telegram containing version information
- Extract version string (format: `XP230_V1.00.04`)
- Support version format: `{PRODUCT}_{VERSION}`
- Validate telegram format and checksum

### 3. Version Information Structure
- Product identifier (e.g., "XP230", "XP20", "XP33LR", "XP24")
- Version number (e.g., "1.00.04", "0.01.05", "0.04.02", "0.34.03")
- Full version string for display

### 4. CLI Commands
Add support for version-related commands:
- `xp telegram parse <version_telegram>` - Parse version telegrams

### 5. Data Models
Add feature to existing data models for:
- request telegram : Version
- reply telegram : Version

### 6. Validation
- Validate telegram format
- Verify checksums
- Handle malformed version strings
- Error handling for invalid telegrams

## Implementation Notes
- Follow existing patterns for telegram parsing
- Ensure compatibility with current telegram structure
- Add comprehensive test coverage
- Update CLI help documentation

## Files to Add/Modify

### New Files to Create:
- `src/xp/services/version_service.py` - Version parsing service
- `tests/unit/test_models/test_version_telegram.py` - Unit tests for version telegram models
- `tests/unit/test_services/test_version_service.py` - Unit tests for version service
- `tests/integration/test_version_integration.py` - Integration tests for version parsing

### Files to Modify:
- `src/xp/models/system_telegram.py` - Add Version to system telegram model
- `src/xp/models/reply_telegram.py` - Add Version to reply telegram model
- `src/xp/cli/main.py` - Add version CLI commands
- `src/xp/services/telegram_service.py` - Add version telegram support
- `src/xp/services/__init__.py` - Export new version models
