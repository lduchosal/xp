# ModuleType Query Feature Specification

## Overview
The ModuleType Query feature enables querying XP system modules to retrieve their module type information. This is a fundamental diagnostic capability that allows identification of connected modules in the XP control system.

## Telegram Protocol

### Query Structure
ModuleType queries use the standard XP telegram format with specific function and datatype codes:
- **Function Code**: `02` (Query/Read operation)
- **DataType Code**: `07` (ModuleType data)

### Query Format
```
<S[SERIAL]F02D07[CHECKSUM]>
```

### Response Format  
```
<R[SERIAL]F02D07[MODULE_TYPE][CHECKSUM]>
```

## Protocol Examples

### Example 1: XP230 Module Query
**Query**: `<S0020030837F02D07FJ>`
- Serial: `0020030837` 
- Function: `02` (Query)
- DataType: `07` (ModuleType)
- Checksum: `FJ`

**Response**: `<R0020030837F02D0734FP>`
- Serial: `0020030837` 
- Function: `02` (Query response)
- DataType: `07` (ModuleType)
- ModuleType: `34` (24 decimal = XP230)
- Checksum: `FP`

### Example 2: XP24 Module Query
**Query**: `<S0020044991F02D07FH>`
- Serial: `0020044991`
- Function: `02` (Query)
- DataType: `07` (ModuleType)
- Checksum: `FH`

**Response**: `<R0020044991F02D0707FB>`
- Serial: `0020044991`
- Function: `02` (Query response)
- DataType: `07` (ModuleType)
- ModuleType: `07` (07 decimal = XP24)
- Checksum: `FB`

### Example 3: XP33 Module Query
**Query**: `<S0020037487F02D07FJ>`
- Serial: `0020037487`
- Function: `02` (Query)
- DataType: `07` (ModuleType)
- Checksum: `FJ`

**Response**: `<R0020037487F02D0733FI>`
- Serial: `0020037487`
- Function: `02` (Query response)
- DataType: `07` (ModuleType)
- ModuleType: `33` (33 = XP33LR)
- Checksum: `FI`

## Module Type Codes

The response contains a hexadecimal module type code that maps to specific XP system modules:

| Hex Code | Module Name | Description            |
|----------|-------------|------------------------|
| 07       | XP24        | XP relay module        |
| 24       | XP230       | XP230 module           |
| 30       | XP33LR      | XP light dimmer module |
| 33       | XP20        | XP switch link module  |

For complete module type registry, see `src/xp/models/module_type.py`.

## Implementation Notes

1. **Module Identification**: This query is essential for system discover and configuration
2. **Address Validation**: Ensure destination addresses correspond to valid, connected modules
3. **Error Handling**: Modules that don't respond indicate disconnection or communication issues
4. **Checksum Verification**: All telegrams must include valid checksums for data integrity
5. **Server Response**: The XP server should automatically respond to ModuleType query telegrams with the corresponding response telegram containing the module's type code

## Related Features

- **Telegram Parsing**: The system can parse and decode these telegrams automatically
- **Module Registry**: Complete module type database with descriptions and capabilities
- **CLI Integration**: Use `xp telegram parse` and `xp module info` commands for analysis

## Usage in XP CLI

```bash
# Parse a module type query
xp telegram parse '<S0020030837F02D07FJ>'

# Parse the response to see module information
xp telegram parse '<R0020030837F02D0734FP>'

```

