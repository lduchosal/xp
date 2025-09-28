# XP24 MS Action Table Download Feature - Python Pseudo Code

## Overview
Python implementation for downloading and managing XP24 module action tables with MS (millisecond) timing parameters.

## Core Class Structure

```python
from typing import List, Optional, Dict
from dataclasses import dataclass, field
from enum import Enum

class InputActionType(Enum):
    """Input action types for XP24 module (based on Feature-Action-Table.md)"""
    VOID = 0
    TURNON = 1
    TURNOFF = 2
    TOGGLE = 3
    BLOCK = 4
    AUXRELAY = 5
    MUTUALEX = 6
    LEVELUP = 7
    LEVELDOWN = 8
    LEVELINC = 9
    LEVELDEC = 10
    LEVELSET = 11
    FADETIME = 12
    SCENESET = 13
    SCENENEXT = 14
    SCENEPREV = 15
    CTRLMETHOD = 16
    RETURNDATA = 17
    DELAYEDON = 18
    EVENTTIMER1 = 19
    EVENTTIMER2 = 20
    EVENTTIMER3 = 21
    EVENTTIMER4 = 22
    STEPCTRL = 23
    STEPCTRLUP = 24
    STEPCTRLDOWN = 25
    LEVELSETINTERN = 29
    FADE = 30
    LEARN = 31

@dataclass
class InputAction:
    """Represents an input action with type and parameter"""
    type: InputActionType
    param: Optional[str]

@dataclass
class Xp24ActionTable:
    """
    XP24 Action Table for managing input actions and settings.

    Each input has an action type (TOGGLE, SWITCH_ON_TIME, HELP)
    with an associated parameter string.
    """

    # MS timing constants
    MS300 = 12
    MS500 = 20

    # Input actions for each input (default to TOGGLE with None parameter)
    input1_action: InputAction = field(default_factory=lambda: InputAction(InputActionType.TOGGLE, None))
    input2_action: InputAction = field(default_factory=lambda: InputAction(InputActionType.TOGGLE, None))
    input3_action: InputAction = field(default_factory=lambda: InputAction(InputActionType.TOGGLE, None))
    input4_action: InputAction = field(default_factory=lambda: InputAction(InputActionType.TOGGLE, None))

    # Boolean settings
    mutex12: bool = False    # Mutual exclusion between inputs 1-2
    mutex34: bool = False    # Mutual exclusion between inputs 3-4
    curtain12: bool = False  # curtain setting for inputs 1-2
    curtain34: bool = False  # curtain setting for inputs 3-4
    ms: int = MS300          # Master timing (MS300=12 or MS500=20)


class Xp24MsActionTableSerializer:
    """Handles serialization/deserialization of XP24 action tables to/from telegrams."""

    # Action types use their enum values directly as function IDs
    # (no mapping needed since the enum values are the actual codes)

    @staticmethod
    def to_telegrams(action_table: Xp24ActionTable, serial: str) -> List[str]:
        """Serialize action table to telegram format."""
        data_parts = [f"S{serial}F17DAAAA"]

        # Encode all 4 input actions
        input_actions = [
            action_table.input1_action,
            action_table.input2_action,
            action_table.input3_action,
            action_table.input4_action
        ]

        for action in input_actions:
            # Use enum value directly as function ID
            function_id = action.type.value
            # Convert parameter to int (None becomes 0)
            if action.param is None:
                param_value = 0
            elif action.param.isdigit():
                param_value = int(action.param)
            else:
                param_value = 0
            data_parts.append(f"{function_id:02X}{param_value:02X}")

        # Add settings as hex values
        data_parts.extend([
            "AB" if action_table.mutex12 else "AA",
            "AB" if action_table.mutex34 else "AA",
            f"{action_table.ms:02X}",
            "AB" if action_table.curtain12 else "AA",
            "AB" if action_table.curtain34 else "AA",
            "A" * 38  # padding
        ])

        data = "".join(data_parts)
        checksum = Xp24MsActionTableSerializer._calculate_checksum(data)
        return [f"<{data}{checksum}>"]

    @staticmethod
    def from_telegrams(ms_telegrams: List[str]) -> Xp24ActionTable:
        """Deserialize action table from telegram format."""
        # Extract and concatenate payload data
        concat = "".join(telegram[20:84] for telegram in ms_telegrams)
        raw_bytes = bytes.from_hex(concat[:64])

        # Decode input actions
        input_actions = []
        for i in range(4):
            function_id = raw_bytes[2 * i]
            param_value = raw_bytes[2 * i + 1]

            # Find action type by enum value
            action_type = InputActionType.VOID  # Default fallback
            for action in InputActionType:
                if action.value == function_id:
                    action_type = action
                    break

            # Convert parameter (0 becomes None for cleaner representation)
            param_str = None if param_value == 0 else str(param_value)
            input_actions.append(InputAction(action_type, param_str))

        action_table = Xp24ActionTable(
            input1_action=input_actions[0],
            input2_action=input_actions[1],
            input3_action=input_actions[2],
            input4_action=input_actions[3],
            mutex12=bool(raw_bytes[8]),
            mutex34=bool(raw_bytes[9]),
            ms=raw_bytes[10],
            curtain12=bool(raw_bytes[11]),
            curtain34=bool(raw_bytes[12])
        )

        return action_table

    @staticmethod
    def _calculate_checksum(data: str) -> str:
        """Calculate checksum for telegram data"""
        from xp.utils.checksum import calculate_checksum
        return calculate_checksum(data)

```

## Integration Points

### Conbus Service Integration
```python
class MsActionTableService:
    """Service for downloading XP24 action tables via Conbus"""

    def __init__(self, config_path: str = "cli.yml"):
        self.conbus_service = ConbusService(config_path)

    def download_action_table(self, serial_number: str) -> Xp24ActionTable:
        """Download action table from XP24 module"""
        query_response = self.conbus_service.send_telegram(
            serial_number,
            SystemFunction.READ_CONFIG,  # F02
            "AAAA"  # MS table query
        )

        if not query_response.success:
            raise Xp24ActionTableError("Failed to query action table")

        return Xp24MsActionTableSerializer.from_telegrams(query_response.received_telegrams)

```

### CLI Integration
```python
@conbus_xp24.command("download-action-table")
@click.argument("serial_number", type=SERIAL)
@connection_command()
@handle_service_errors(Xp24ActionTableError)
def xp24_download_action_table(serial_number: str) -> None:
    """Download MS action table from XP24 module"""
    service = MsActionTableService()

    with service:
        action_table = service.download_action_table(serial_number)

        # Use dataclass built-in conversion for JSON serialization
        from dataclasses import asdict
        output = {
            "serial_number": serial_number,
            "action_table": asdict(action_table)
        }
        click.echo(json.dumps(output, indent=2, default=str))
```

## Python Native Serialization

The design follows Python's native serialization patterns:

### 1. Dataclass with `asdict()`
```python
from dataclasses import asdict
import json

# Convert dataclass to dict for JSON serialization
action_table_dict = asdict(action_table)
json_data = json.dumps(action_table_dict, indent=2, default=str)
```

### 3. Separate Serializer Classes
- **Single Responsibility**: Data model separate from serialization logic
- **Protocol-Specific**: Different serializers for different protocols (telegram, JSON, etc.)
- **Testable**: Easy to unit test serialization logic independently
- **Extensible**: Can add new serialization formats without modifying the data model

## Telegram Format

### MS Action Table Query (F02)
```
<S{serial}F02DAAAA{checksum}>
```

### MS Action Table Response (F17)
```
<S{serial}F17DAAAA{4_rows}{mutex12}{mutex34}{ms}{curtain12}{curtain34}{padding}{checksum}>
```

Where:
- `{in1_action}`: 8 bytes (action_id + parameter_id)
- `{in2_action}`: 8 bytes (action_id + parameter_id)
- `{in3_action}`: 8 bytes (action_id + parameter_id)
- `{in4_action}`: 8 bytes (action_id + parameter_id)
- `{mutex12}`: AA/AB (mutex for outputs 1-2)
- `{mutex34}`: AA/AB (mutex for outputs 3-4)
- `{ms}`: Timing value (MS300=12, MS500=20)
- `{curtain12}`: AA/AB (curtain setting for outputs 1-2)
- `{curtain34}`: AA/AB (curtain setting for outputs 3-4)
- `{padding}`: 19 bytes of "AA" padding

## Usage Examples

### Creating Action Tables
```python
# Create action table with different input types
action_table = Xp24ActionTable(
    input1_action=InputAction(InputActionType.TOGGLE, None),     # Toggle with no parameter
    input2_action=InputAction(InputActionType.TURNON, "5000"),  # Turn on for 5 seconds
    input3_action=InputAction(InputActionType.LEVELSET, "75"),  # Set light level to 75%
    input4_action=InputAction(InputActionType.SCENESET, "3"),   # Set scene 3
    mutex12=True,                      # Inputs 1-2 are mutually exclusive
    curtain34=True,                    # Inputs 3-4 have curtain control
    ms=Xp24ActionTable.MS500           # 500ms timing base
)

# Or use defaults (all inputs will be TOGGLE with None parameter)
default_table = Xp24ActionTable()

# Serialize to telegram format
telegrams = Xp24MsActionTableSerializer.to_telegrams(action_table, "0123456789")

# Deserialize from telegrams
received_action_table = Xp24MsActionTableSerializer.from_telegrams(telegrams)

# JSON serialization using dataclass
from dataclasses import asdict
json_data = json.dumps(asdict(action_table), indent=2, default=str)
```
