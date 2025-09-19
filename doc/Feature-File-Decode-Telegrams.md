# Feature Specification: File Decode Telegrams

## Overview

This feature enables parsing and analysis of console bus log files containing timestamped telegram transmissions and receptions. The system can decode various telegram types (Event, System, Reply) from log files and provide comprehensive analysis including validation, timing, and communication patterns.

## Current Codebase Integration

### Existing Components
- **TelegramService** (`src/xp/services/telegram_service.py`) - Core telegram parsing
- **EventTelegram** (`src/xp/models/event_telegram.py`) - Event telegram model
- **SystemTelegram** (`src/xp/models/system_telegram.py`) - System telegram model  
- **ReplyTelegram** (`src/xp/models/reply_telegram.py`) - Reply telegram model
- **Checksum Utilities** (`src/xp/utils/checksum.py`) - Checksum validation
- **CLI Interface** (`src/xp/cli/main.py`) - Command-line interface

### Automatic Checksum Validation
All telegram models now include automatic checksum validation during parsing:
- `checksum_validated: Optional[bool]` property in all telegram models
- Visual indicators (/) in human-readable output
- JSON output includes validation status

## Log File Format

Based on the provided console bus log sample:

```
22:44:20,352 [TX] <S0020044964F27D00AAFN>
22:44:20,420 [RX] <R0020044964F18DFA>
22:44:20,467 [TX] <S0020044964F02D12FJ>
22:44:20,467 [RX] <E07L06I80BAL>
22:44:20,529 [RX] <R0020044964F02D12xxxx1110FJ>
22:44:21,766 [TX] <S0020044964F27D01AAFM>
22:44:21,831 [RX] <R0020044964F18DFA>
22:44:21,831 [RX] <E07L06I81BAK>
```

## Sample files
- Specs/ConbusLog.txt
- Specs/ConbusLog-discover.txt

### Format Structure
- **Timestamp**: `HH:MM:SS,mmm` format
- **Direction**: `[TX]` (transmitted) or `[RX]` (received)
- **Telegram**: Standard telegram format `<...>`

## Feature Requirements

### 1. Log File Parsing

#### 1.1 LogEntry Model
Create a new model to represent log entries:

```python
@dataclass
class LogEntry:
    timestamp: datetime
    direction: str  # "TX" or "RX"
    raw_telegram: str
    parsed_telegram: Optional[Union[EventTelegram, SystemTelegram, ReplyTelegram]] = None
    parse_error: Optional[str] = None
    line_number: int = 0
```

#### 1.2 LogFileService
New service for log file operations:

```python
class LogFileService:
    def parse_log_file(self, file_path: str) -> List[LogEntry]:
        pass
    def extract_telegrams(self, file_path: str) -> List[str]:
        pass
```

### 2. CLI Commands

#### 2.1 File Parsing Command
```bash
xp file read <log_file_path> [OPTIONS]
```

**Options:**
- `--json-output, -j` - Output in JSON format
- `--output-file <path>` - Save results to file

### 4. Output Formats

#### 4.1 Human-Readable Output
Regroup System telegram with their matching Reply telegram
If an event is 
```
<S0020044964F27D00AAFN> : <R0020044964F18DFA>
<S0020044964F02D12FJ>   : <R0020044964F02D12xxxx1110FJ>
<S0020044964F27D01AAFM> : <R0020044964F18DFA>
<S0020044974F02D17FN>   : <R0020044974F02D1700:00000[NA],01:00000[NA],02:00000[NA],03:00000[NA]HA>
<S0020044974F04D0425FO> : <R0020044974F18DFB>
<S0020044974F04D0409FA> : <R0020044974F18DFB>

<E07L06I80BAL>
```

### 5. Implementation Plan

#### 5.1 Phase 1: Basic Log Parsing
- [ ] Create LogEntry model
- [ ] Implement LogFileService
- [ ] Add basic CLI command
- [ ] Support timestamp parsing
- [ ] Handle TX/RX direction indicators

#### 5.2 Phase 2: Telegram Integration
- [ ] Integrate with existing TelegramService
- [ ] Apply automatic checksum validation
- [ ] Handle parsing errors gracefully
- [ ] Add filtering capabilities

#### 5.3 Phase 3: Analysis Features
- [ ] Implement communication pattern detection
- [ ] Add timing analysis
- [ ] Create device tracking
- [ ] Generate statistics

#### 5.4 Phase 4: Advanced Features
- [ ] Request-response correlation
- [ ] Anomaly detection
- [ ] Export capabilities
- [ ] Visualization support

### 6. File Structure

```
src/xp/
   models/log_entry.py            # New: LogEntry model
   services/log_file_service.py   # New: Log file parsing service
   cli/main.py                    # Extended: Add file commands
   utils/time_utils.py            # New: Time parsing utilities
   
```

### 7. Error Handling

#### 7.1 File-Level Errors
- File not found or inaccessible
- Invalid file format
- Corrupted or truncated files

#### 7.2 Parsing Errors  
- Invalid timestamp format
- Unknown direction indicators
- Malformed telegram syntax
- Missing or invalid checksums

#### 7.3 Analysis Errors
- Incomplete request-response pairs
- Timing anomalies
- Protocol violations

### 8. Testing Strategy

#### 8.1 Unit Tests
- LogEntry model validation
- LogFileService parsing logic
- Time parsing utilities
- Error handling scenarios

#### 8.2 Integration Tests
- End-to-end file processing
- CLI command functionality
- Output format validation
- Real log file processing

#### 8.3 Test Data
- Sample log files with various scenarios
- Corrupted/malformed log files
- Large log files for performance testing
- Edge cases (empty files, single entries)

### 9. Performance Considerations

#### 9.1 Large File Handling
- Stream processing for large files
- Memory-efficient parsing
- Progress indicators for long operations
- Chunk-based processing

#### 9.2 Optimization
- Regex compilation caching
- Efficient timestamp parsing
- Lazy loading of parsed telegrams
- Parallel processing for analysis

### 10. Usage Examples

```bash
# Decode all telegrams in log file
xp file decode conbus.log
```

## Conclusion

This feature transforms the XP CLI tool into a comprehensive console bus analysis platform, enabling users to decode, validate, and analyze communication logs with detailed insights into system behavior, timing patterns, and protocol compliance.