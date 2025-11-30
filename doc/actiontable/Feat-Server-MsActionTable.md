# Server MsActionTable Implementation Spec

## Overview
Add MsActionTable (F13 command) response capability to XP server emulators for XP20, XP24, and XP33 modules.

## Scope
Enable server emulators to respond to DOWNLOAD_MSACTIONTABLE (F13) requests with configurable or default MsActionTable data.

## Supported Modules
- **XP20**: 8 input channels with flags and AND functions
- **XP24**: 4 input actions with mutex/curtain settings
- **XP33**: 3 outputs with scenes and dimming levels

## Protocol

MsActionTable download follows a multi-telegram handshake protocol:

```
1. [TX] <S{serial}F13D00{checksum}>         # Client: DOWNLOAD_MSACTIONTABLE
2. [RX] <R{serial}F18D{checksum}>           # Server: ACK
3. [TX] <S{serial}F18D00{checksum}>         # Client: CONTINUE
4. [RX] <R{serial}F17D{data}{checksum}>     # Server: MSACTIONTABLE
5. [TX] <S{serial}F18D00{checksum}>         # Client: CONTINUE
6. [RX] <R{serial}F16D{checksum}>           # Server: EOF
```

### System Functions
- **F13D**: DOWNLOAD_MSACTIONTABLE (SystemFunction.DOWNLOAD_MSACTIONTABLE = "13")
- **F18D**: ACK/CONTINUE (SystemFunction.ACK = "18")
- **F17D**: MSACTIONTABLE data (SystemFunction.MSACTIONTABLE = "17")
- **F16D**: EOF (SystemFunction.EOF = "16")

### Data Format
`{data}` is A-P nibble-encoded MsActionTable specific to module type:
- XP20: 64 chars (32 bytes)
- XP24: 68 chars (34 bytes)
- XP33: Variable length (32+ bytes)

### Example Protocol Exchange (XP20)

```
[TX] <S0012345001F13D00FI>                                              # DOWNLOAD_MSACTIONTABLE
[RX] <R0012345001F18DFA>                                                # ACK
[TX] <S0012345001F18D00FB>                                              # CONTINUE
[RX] <R0012345001F17DAAAAAAAAAAABACAEAIBACAEAIAAAAAAAAAAAAAAAAAAA...GH> # MSACTIONTABLE (64 chars)
[TX] <S0012345001F18D00FB>                                              # CONTINUE
[RX] <R0012345001F16DFO>                                                # EOF
```

## Implementation

### 1. Add MsActionTable State to Module Services

**Files to modify:**
- `src/xp/services/server/xp20_server_service.py`
- `src/xp/services/server/xp24_server_service.py`
- `src/xp/services/server/xp33_server_service.py`

Add to each service's `__init__`:
```python
from xp.services.actiontable.msactiontable_xp20_serializer import Xp20MsActionTableSerializer
from xp.models.actiontable.msactiontable_xp20 import Xp20MsActionTable

self.msactiontable_serializer = Xp20MsActionTableSerializer()
self.msactiontable = self._get_default_msactiontable()
```

### 2. Add Download State Tracking

Add to each service's `__init__`:
```python
self.msactiontable_download_state: Optional[str] = None  # Track: "ack_sent", "data_sent", None
```

### 3. Implement Default MsActionTable Generator

Add private method to each service:
```python
def _get_default_msactiontable(self) -> Xp20MsActionTable:
    """Generate default MsActionTable configuration."""
    # Return sensible defaults for testing
```

### 4. Handle Multi-Telegram Protocol

Override `process_system_telegram` in each service to handle the download sequence:

```python
def process_system_telegram(self, request: SystemTelegram) -> Optional[str]:
    """Process system telegrams including MsActionTable download."""

    # Handle F13D - DOWNLOAD_MSACTIONTABLE request
    if request.system_function == SystemFunction.DOWNLOAD_MSACTIONTABLE:
        self.msactiontable_download_state = "ack_sent"
        # Send ACK and queue data telegram
        ack_telegram = self._build_response_telegram(f"R{self.serial_number}F18D")
        self.add_telegram_buffer(ack_telegram)
        return None  # ACK sent via buffer

    # Handle F18D - CONTINUE (after ACK or data)
    if (request.system_function == SystemFunction.ACK and
            self.msactiontable_download_state):

        if self.msactiontable_download_state == "ack_sent":
            # Send MsActionTable data
            encoded_data = self.msactiontable_serializer.to_encoded_string(self.msactiontable)
            data_telegram = self._build_response_telegram(
                f"R{self.serial_number}F17D{encoded_data}"
            )
            self.add_telegram_buffer(data_telegram)
            self.msactiontable_download_state = "data_sent"
            return None

        elif self.msactiontable_download_state == "data_sent":
            # Send EOF
            eof_telegram = self._build_response_telegram(f"R{self.serial_number}F16D")
            self.add_telegram_buffer(eof_telegram)
            self.msactiontable_download_state = None
            return None

    # Delegate to base class for other requests
    return super().process_system_telegram(request)
```

### 5. Reuse Existing Serializers

**Serializers (already implemented):**
- `Xp20MsActionTableSerializer` - `src/xp/services/actiontable/msactiontable_xp20_serializer.py`
- `Xp24MsActionTableSerializer` - `src/xp/services/actiontable/msactiontable_xp24_serializer.py`
- `Xp33MsActionTableSerializer` - `src/xp/services/actiontable/msactiontable_xp33_serializer.py`

**Models (already implemented):**
- `Xp20MsActionTable` - `src/xp/models/actiontable/msactiontable_xp20.py`
- `Xp24MsActionTable` - `src/xp/models/actiontable/msactiontable_xp24.py`
- `Xp33MsActionTable` - `src/xp/models/actiontable/msactiontable_xp33.py`

## Default Configurations

### XP20 Default
All inputs unconfigured (all flags False, AND functions empty).

### XP24 Default
```python
Xp24MsActionTable(
    input1=InputAction(type=InputActionType.NOTHING, param=TimeParam.MS0),
    input2=InputAction(type=InputActionType.NOTHING, param=TimeParam.MS0),
    input3=InputAction(type=InputActionType.NOTHING, param=TimeParam.MS0),
    input4=InputAction(type=InputActionType.NOTHING, param=TimeParam.MS0),
    mutex12=False,
    mutex34=False,
    curtain12=False,
    curtain34=False,
    mutual_deadtime=12  # MS300
)
```

### XP33 Default
All outputs at 0-100% range, no scenes configured.

## Testing

### Manual Test Commands
```bash
# Start server with XP20 device
xp conbus server start --config server.yml

# Download MsActionTable from emulated device
xp conbus msactiontable download 0012345001 xp20
```

### Expected Response
Valid JSON with module-specific MsActionTable structure matching serializer output.

## Implementation Notes

### Telegram Buffer Mechanism
The server uses `add_telegram_buffer()` to queue telegrams for sequential delivery:
- Inherited from `BaseServerService` (see base_server_service.py:265-273)
- Thread-safe buffering for multi-telegram responses
- `collect_telegram_buffer()` retrieves queued telegrams

### State Management
- Download state tracks protocol progression: `None → "ack_sent" → "data_sent" → None`
- State must be per-device (instance variable) to handle multiple concurrent downloads
- Reset state to `None` after EOF to allow repeated downloads

### Key Points
- Use `SystemFunction.DOWNLOAD_MSACTIONTABLE` (value "13") for initial request detection
- Use `SystemFunction.ACK` (value "18") for CONTINUE request detection
- Serializers handle all encoding/decoding - no custom nibble logic needed
- MsActionTable state can be made configurable via server.yml in future enhancement
