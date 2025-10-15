# Feature: Bus Error Management - XP33LR Dead Loop Prevention

## Problem Statement

### Critical Issue: XP33LR Crazy Dead Loop

XP33LR modules can enter a **"crazy dead loop"** state when receiving too many query datapoint telegrams. Despite implementing telegram debounce (see `Feat-Bus-Debounce.md`), the module can still become stuck in a pathological state.

#### Symptoms

When an XP33LR module enters the dead loop state:

1. **Telegram Storm**: Module sends **thousands of identical datapoint reply telegrams** on the bus
2. **Bus Saturation**: Conbus protocol becomes overwhelmed with duplicate responses
3. **Bridge Lockup**: XP130 and XP230 bridge modules **freeze or lock** due to telegram overflow
4. **System Unresponsiveness**: Entire Conbus system becomes unresponsive
5. **Cascading Failures**: Other modules may timeout or fail to respond

#### Root Cause Analysis

**Pre-conditions:**
- Multiple HomeKit accessories share the same XP33LR module
- Rapid state changes trigger multiple query telegrams (even with debounce)
- Module firmware enters error state under load

**Trigger:**
```
[Physical button press or rapid state changes]
         ↓
[Multiple query telegrams to XP33LR module]
         ↓
[Module firmware enters error state]
         ↓
[Module repeatedly sends same response telegram]
         ↓
[Bus saturates with thousands of duplicate telegrams]
         ↓
[Bridge modules (XP130/XP230) overwhelmed and freeze]
```

#### Why Debounce Alone Doesn't Solve This

The existing telegram debounce service (implemented in `src/xp/services/protocol/telegram_debounce_service.py`) successfully:

- ✅ Reduces duplicate query telegrams sent TO modules
- ✅ Batches requests within 50ms window
- ✅ Deduplicates identical requests before transmission

However, it **cannot prevent** the XP33LR dead loop because:

- ❌ Debounce doesn't detect when a module has entered an error state
- ❌ Debounce doesn't handle **response telegram storms** FROM modules
- ❌ Debounce operates at request layer, not error detection layer
- ❌ Module firmware bug causes it to loop internally (independent of incoming requests)

### Discovery: MODULE_ERROR_CODE as Circuit Breaker

**Critical Finding:** Sending a read datapoint telegram for `MODULE_ERROR_CODE` (datapoint type `10`) **stops the dead loop**.

**Example:**
```
Request:  S0012345003F02D10FO
Response: R0012345003F02D1000FP  (00 = normal)
Response: R0012345003F02D10XXFP  (XX = error code)
```

This suggests the MODULE_ERROR_CODE query acts as a **reset/recovery mechanism** for the module's internal state machine.

## Proposed Solution: Proactive Error State Monitoring

Implement **proactive error state checking** after operations that may stress the module:

1. **After Action Telegrams** (SendActionEvent): Query MODULE_ERROR_CODE
2. **After Query Telegrams** (ReadDatapointFromProtocolEvent): Query MODULE_ERROR_CODE
3. **Periodic Health Checks**: Query MODULE_ERROR_CODE at intervals
4. **Telegram Storm Detection**: Monitor response rates and trigger error query

### Architecture

```
[Action or Query Telegram Sent]
         ↓
[Wait for Response (with timeout)]
         ↓
[Automatically Query MODULE_ERROR_CODE]
         ↓
    ┌───┴───┐
    │       │
   [00]   [XX]
Normal   Error
    │       │
    │       └─> [Log Error State]
    │           [Trigger Error Recovery Event]
    │           [Notify monitoring system]
    │
[Continue Normal Operation]
```

### Implementation Strategy

#### Phase 1: Error State Querying Service

Create `BusErrorManagementService` to handle error state monitoring:

```python
class BusErrorManagementService:
    """
    Monitors and manages XP33LR module error states.

    Automatically queries MODULE_ERROR_CODE after operations
    to detect and recover from dead loop states.
    """

    def __init__(
        self,
        event_bus: EventBus,
        telegram_protocol: TelegramProtocol,
        enable_proactive_checks: bool = True,
        error_check_delay_ms: int = 100,
    ):
        self.event_bus = event_bus
        self.telegram_protocol = telegram_protocol
        self.enable_proactive_checks = enable_proactive_checks
        self.error_check_delay_ms = error_check_delay_ms
        self.logger = logging.getLogger(__name__)

        # Track modules that need error checking
        self.pending_error_checks: Set[str] = set()
        self.error_check_timer: Optional[asyncio.TimerHandle] = None

        # Statistics
        self.error_checks_sent = 0
        self.errors_detected = 0
        self.dead_loops_recovered = 0

        # Subscribe to telegram events
        if enable_proactive_checks:
            self.event_bus.on(
                TelegramReceivedEvent,
                self.handle_telegram_received
            )

    def handle_telegram_received(self, event: TelegramReceivedEvent) -> None:
        """
        After receiving response telegram, schedule error check.

        This ensures we query MODULE_ERROR_CODE after operations
        that may stress the module.
        """
        # Only check for system telegrams (S prefix) to XP33 modules
        if not event.telegram.startswith('S'):
            return

        serial_number = event.serial_number
        if not serial_number:
            return

        # Schedule error check for this module
        self.schedule_error_check(serial_number)

    def schedule_error_check(self, serial_number: str) -> None:
        """
        Schedule MODULE_ERROR_CODE query for given module.

        Uses debounce timer to avoid excessive queries.
        """
        self.pending_error_checks.add(serial_number)

        # Reset timer
        if self.error_check_timer:
            self.error_check_timer.cancel()

        loop = asyncio.get_event_loop()
        self.error_check_timer = loop.call_later(
            self.error_check_delay_ms / 1000.0,
            lambda: asyncio.create_task(self._process_error_checks())
        )

    async def _process_error_checks(self) -> None:
        """
        Send MODULE_ERROR_CODE queries for all pending modules.
        """
        if not self.pending_error_checks:
            return

        modules_to_check = list(self.pending_error_checks)
        self.pending_error_checks.clear()

        self.logger.debug(
            f"Checking error state for {len(modules_to_check)} modules"
        )

        for serial_number in modules_to_check:
            await self._send_error_check(serial_number)

    async def _send_error_check(self, serial_number: str) -> None:
        """
        Send MODULE_ERROR_CODE query to specific module.
        """
        system_function = SystemFunction.READ_DATAPOINT.value
        datapoint_type = DataPointType.MODULE_ERROR_CODE.value
        telegram = f"S{serial_number}F{system_function}D{datapoint_type}"

        self.logger.debug(f"Sending error check to {serial_number}: {telegram}")
        self.telegram_protocol.sendFrame(telegram.encode())
        self.error_checks_sent += 1

        # Subscribe to response
        self.event_bus.once(
            TelegramReceivedEvent,
            lambda event: self._handle_error_response(event, serial_number)
        )

    def _handle_error_response(
        self,
        event: TelegramReceivedEvent,
        expected_serial: str
    ) -> None:
        """
        Parse MODULE_ERROR_CODE response and take action if needed.
        """
        if event.serial_number != expected_serial:
            return

        # Parse error code from response
        # Response format: R{serial}F02D10{XX}FN
        # where XX is the error code (00 = normal)
        try:
            # Extract data value from payload
            payload = event.payload
            if "D10" in payload:
                error_code_start = payload.index("D10") + 3
                error_code = payload[error_code_start:error_code_start+2]

                if error_code != "00":
                    self.errors_detected += 1
                    self.logger.warning(
                        f"Module {expected_serial} reports error code: {error_code}"
                    )

                    # Dispatch error event
                    self.event_bus.dispatch(ModuleErrorDetectedEvent(
                        serial_number=expected_serial,
                        error_code=error_code,
                        timestamp=asyncio.get_event_loop().time()
                    ))

                    # Log potential dead loop recovery
                    if error_code in ["FF", "FE", "FD"]:  # Critical error codes
                        self.dead_loops_recovered += 1
                        self.logger.critical(
                            f"Potential dead loop detected and recovered for {expected_serial}"
                        )
                else:
                    self.logger.debug(f"Module {expected_serial} reports normal status")

        except Exception as e:
            self.logger.error(f"Failed to parse error response: {e}")
```

#### Phase 2: Event Model

Add new event for error state tracking:

```python
# In src/xp/models/protocol/conbus_protocol.py

class ModuleErrorDetectedEvent(BaseEvent):
    """Event dispatched when a module reports an error state"""

    serial_number: str = Field(description="Serial number of the module")
    error_code: str = Field(description="Error code from MODULE_ERROR_CODE datapoint")
    timestamp: float = Field(description="Timestamp when error was detected")
```

#### Phase 3: Integration Points

**1. Register in Dependency Container**

```python
# In src/xp/utils/dependencies.py

def setup_services(container):
    # ... existing services ...

    # Register BusErrorManagementService
    container.register(
        BusErrorManagementService,
        factory=lambda c: BusErrorManagementService(
            event_bus=c.resolve(EventBus),
            telegram_protocol=c.resolve(TelegramProtocol),
            enable_proactive_checks=config.get("bus_error_management.enabled", True),
            error_check_delay_ms=config.get("bus_error_management.delay_ms", 100),
        ),
        singleton=True
    )
```

**2. Configuration**

```yaml
# config.yaml
bus_error_management:
  enabled: true
  delay_ms: 100  # Wait 100ms after telegram before checking error

  # Module-specific settings
  xp33lr:
    enable_error_checks: true
    critical_error_codes: ["FF", "FE", "FD"]

  # Telegram storm detection
  storm_detection:
    enabled: true
    threshold_telegrams_per_second: 100
    window_seconds: 5
```

### Phase 4: Telegram Storm Detection

Add advanced detection for response telegram storms:

```python
class TelegramStormDetector:
    """
    Detects and mitigates telegram storms from modules.

    Monitors response rates and triggers error checks when
    abnormal patterns are detected.
    """

    def __init__(
        self,
        event_bus: EventBus,
        error_management_service: BusErrorManagementService,
        threshold_tps: int = 100,
        window_seconds: int = 5
    ):
        self.event_bus = event_bus
        self.error_management_service = error_management_service
        self.threshold_tps = threshold_tps
        self.window_seconds = window_seconds

        # Track telegram rates per module
        self.telegram_counts: Dict[str, List[float]] = {}

        self.event_bus.on(
            TelegramReceivedEvent,
            self.handle_telegram_received
        )

    def handle_telegram_received(self, event: TelegramReceivedEvent) -> None:
        """Track telegram rate and detect storms"""
        serial_number = event.serial_number
        if not serial_number:
            return

        current_time = asyncio.get_event_loop().time()

        # Initialize tracking for this module
        if serial_number not in self.telegram_counts:
            self.telegram_counts[serial_number] = []

        # Add current timestamp
        self.telegram_counts[serial_number].append(current_time)

        # Remove old timestamps outside window
        cutoff_time = current_time - self.window_seconds
        self.telegram_counts[serial_number] = [
            ts for ts in self.telegram_counts[serial_number]
            if ts > cutoff_time
        ]

        # Check if rate exceeds threshold
        telegram_count = len(self.telegram_counts[serial_number])
        telegrams_per_second = telegram_count / self.window_seconds

        if telegrams_per_second > self.threshold_tps:
            self.logger.critical(
                f"TELEGRAM STORM DETECTED: {serial_number} "
                f"sending {telegrams_per_second:.1f} telegrams/sec "
                f"(threshold: {self.threshold_tps})"
            )

            # Immediately trigger error check to stop dead loop
            self.error_management_service.schedule_error_check(serial_number)

            # Dispatch storm event
            self.event_bus.dispatch(TelegramStormDetectedEvent(
                serial_number=serial_number,
                telegrams_per_second=telegrams_per_second,
                timestamp=current_time
            ))
```

## Implementation Plan

### Phase 1: Core Error Management (Week 1)

1. ✅ Create `BusErrorManagementService` class
2. ✅ Implement MODULE_ERROR_CODE query logic
3. ✅ Add `ModuleErrorDetectedEvent` to protocol models
4. ✅ Register service in dependency container
5. ✅ Add configuration options

### Phase 2: Testing & Validation (Week 1-2)

6. ✅ Unit tests for error detection logic
7. ✅ Integration tests with XP33LR emulator
8. ✅ Simulate dead loop scenario and verify recovery
9. ✅ Test with multiple modules under load
10. ✅ Verify bridge module stability (XP130/XP230)

### Phase 3: Storm Detection (Week 2)

11. ✅ Implement `TelegramStormDetector` class
12. ✅ Add rate limiting and throttling
13. ✅ Test storm detection thresholds
14. ✅ Add metrics and alerting

### Phase 4: Monitoring & Observability (Week 3)

15. ✅ Add metrics dashboard
16. ✅ Expose error statistics via API
17. ✅ Add CLI commands for error monitoring
18. ✅ Implement error log aggregation

## Success Metrics

### Before Implementation

**Failure Mode:**
```
[XP33LR receives 10 query telegrams in 100ms]
         ↓
[Module enters dead loop state]
         ↓
[Sends 1000+ identical response telegrams]
         ↓
[XP130 bridge module freezes]
         ↓
[System unresponsive for 30+ seconds]
         ↓
[Manual intervention required (power cycle)]
```

**Metrics:**
- Dead loop incidents: **1-2 per day**
- System downtime: **30-60 seconds per incident**
- Bridge module crashes: **50% of incidents**
- Recovery method: **Manual power cycle**

### After Implementation

**Recovery Mode:**
```
[XP33LR receives 10 query telegrams in 100ms]
         ↓
[Debounce reduces to 2-3 unique telegrams]
         ↓
[MODULE_ERROR_CODE queried after each response]
         ↓
[Module error state detected (if any)]
         ↓
[Automatic recovery via error query]
         ↓
[System remains stable]
```

**Target Metrics:**
- Dead loop incidents: **0 per day** (or immediate recovery)
- System downtime: **<1 second** (automatic recovery)
- Bridge module crashes: **0%**
- Recovery method: **Automatic**

## Configuration Examples

### Basic Configuration

```yaml
# config.yaml - Recommended for most deployments
bus_error_management:
  enabled: true
  delay_ms: 100
```

### Advanced Configuration

```yaml
# config.yaml - High-traffic deployments
bus_error_management:
  enabled: true
  delay_ms: 50  # Lower delay for faster detection

  xp33lr:
    enable_error_checks: true
    critical_error_codes: ["FF", "FE", "FD", "FC"]
    max_error_checks_per_minute: 60

  storm_detection:
    enabled: true
    threshold_telegrams_per_second: 80
    window_seconds: 5

  recovery:
    auto_recovery_enabled: true
    recovery_delay_ms: 500
    max_recovery_attempts: 3
```

### Debugging Configuration

```yaml
# config.yaml - For troubleshooting
bus_error_management:
  enabled: true
  delay_ms: 200  # Higher delay for observation
  debug_logging: true

  storm_detection:
    enabled: true
    threshold_telegrams_per_second: 50  # Lower threshold for testing
    log_all_telegrams: true
```

## CLI Commands

Add monitoring commands to `xp conbus` CLI:

```bash
# Check error status for all modules
xp conbus error-status

# Check error status for specific module
xp conbus error-status --serial 012345678901

# View error statistics
xp conbus error-stats

# Enable/disable error management
xp conbus error-management --enable
xp conbus error-management --disable

# View telegram storm history
xp conbus telegram-storms --last 24h
```

## Error Code Reference

Based on XP33LR firmware documentation:

| Code | Severity | Description | Action |
|------|----------|-------------|--------|
| `00` | Normal | No error | Continue normal operation |
| `01` | Warning | Temperature warning | Monitor temperature |
| `02` | Warning | Load imbalance | Check channel configuration |
| `10` | Error | Communication timeout | Retry communication |
| `20` | Error | Invalid command | Log and ignore |
| `FC` | Critical | Firmware error | Log, notify admin |
| `FD` | Critical | Hardware fault | Log, notify admin |
| `FE` | Critical | Internal buffer overflow | **Potential dead loop - immediate recovery** |
| `FF` | Critical | Fatal error | **Dead loop state - immediate recovery** |

## Testing Strategy

### Unit Tests

```python
def test_error_check_scheduled_after_telegram():
    """Verify error check is scheduled after receiving telegram"""

def test_error_code_parsed_correctly():
    """Verify error code extraction from response"""

def test_critical_error_triggers_event():
    """Verify ModuleErrorDetectedEvent dispatched for errors"""

def test_storm_detector_identifies_high_rate():
    """Verify storm detection at threshold"""
```

### Integration Tests

```python
def test_xp33lr_dead_loop_recovery():
    """Simulate dead loop and verify automatic recovery"""

def test_multiple_modules_concurrent_errors():
    """Test error handling with multiple modules"""

def test_bridge_module_stability_under_storm():
    """Verify XP130/XP230 don't freeze during storm"""
```

### Load Tests

```python
def test_100_modules_error_checks():
    """Test error checking at scale"""

def test_sustained_high_telegram_rate():
    """Test storm detection over extended period"""
```

## Rollout Strategy

### Phase 1: Canary Deployment (1 week)
- Enable on 10% of modules
- Monitor error detection rates
- Verify no false positives
- Collect baseline metrics

### Phase 2: Gradual Rollout (2 weeks)
- Increase to 50% of modules
- Monitor system stability
- Tune storm detection thresholds
- Validate automatic recovery

### Phase 3: Full Deployment (1 week)
- Enable for all modules
- Monitor for 7 days
- Document any incidents
- Adjust configuration if needed

## Monitoring & Alerting

### Key Metrics to Monitor

1. **Error Detection Rate**
   - `bus_error_checks_sent_total`: Total error checks sent
   - `bus_errors_detected_total`: Total errors detected
   - `bus_dead_loops_recovered_total`: Total dead loop recoveries

2. **Telegram Storm Metrics**
   - `bus_telegram_storm_detected_total`: Total storms detected
   - `bus_telegrams_per_second`: Current telegram rate per module
   - `bus_storm_recovery_duration_seconds`: Time to recover from storm

3. **System Health**
   - `bus_bridge_module_uptime_seconds`: XP130/XP230 uptime
   - `bus_module_availability_percent`: Module responsiveness
   - `bus_system_downtime_seconds`: Total downtime

### Alert Conditions

```yaml
# Prometheus alert rules
alerts:
  - name: HighErrorRate
    condition: rate(bus_errors_detected_total[5m]) > 10
    severity: warning

  - name: DeadLoopDetected
    condition: bus_dead_loops_recovered_total > 0
    severity: critical

  - name: TelegramStorm
    condition: bus_telegram_storm_detected_total > 0
    severity: critical

  - name: BridgeModuleDown
    condition: bus_bridge_module_uptime_seconds < 300
    severity: critical
```

## References

- **Debounce Implementation**: `doc/architecture/Feat-Bus-Debounce.md`
- **XP33LR Specification**: `doc/architecture/Feat-XP33-Emulator-Spec.md`
- **Cache Management**: `doc/architecture/Feat-Cache-Management.md`
- **Protocol Models**: `src/xp/models/protocol/conbus_protocol.py`
- **Datapoint Types**: `src/xp/models/telegram/datapoint_type.py`

## Open Questions

1. **Should error checking be module-type-specific?**
   - Currently applies to all modules
   - Could optimize for XP33LR only
   - **Recommendation**: Start with all modules, add filtering if needed

2. **What's the optimal error check delay?**
   - Too short: Excessive queries
   - Too long: Delayed detection
   - **Recommendation**: 100ms default, make configurable

3. **Should we implement circuit breaker pattern?**
   - Stop querying module after N consecutive errors
   - **Recommendation**: Yes, in Phase 2

4. **Should error checks be debounced separately?**
   - Avoid overwhelming module with error queries
   - **Recommendation**: Yes, use 100ms debounce window

## Status

- ⏳ **Specification**: Complete
- ⏳ **Implementation**: Pending
- ⏳ **Testing**: Pending
- ⏳ **Deployment**: Pending

## Changelog

- **2025-10-14**: Initial specification created
  - Documented XP33LR dead loop issue
  - Designed BusErrorManagementService
  - Added telegram storm detection
  - Defined success metrics and rollout plan
