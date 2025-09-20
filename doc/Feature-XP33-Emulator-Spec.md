# XP33 Module Emulator Specification

## Overview
XP33 3-channel light dimmer module emulator for Conbus system testing. Responds to discovery requests and all standard Conbus data point queries.

## Module Identity
- **Module Type**: XP33 (Code 11)
- **Serial Number**: Configurable (default: 0020042796)
- **Product ID**: XP33LR or XP33LED
- **Firmware**: V0.04.02

## Module Variants

### XP33LR - 3-Channel Resistive/Inductive Dimmer
- **EAN**: 5703513058982
- **Power**: Total 640VA, max 500VA per channel
- **Load Types**: Resistive and inductive loads
- **Dimming**: Leading edge, logarithmic control
- **Channels**: 3 independent channels

### XP33LED - 3-Channel LED Dimmer  
- **EAN**: 5703513058999
- **Power**: 3 x 100VA (100VA per channel)
- **Load Types**: LED lamps, resistive and capacitive
- **Dimming**: Leading/Trailing edge configurable per channel
- **Channels**: 3 independent channels, short-circuit proof

## Discovery Response
**Request**: `<S0000000000F01D00FA>`  
**Response**: `<R0020042796F01DFN>`

## Data Point Responses

### 02 - Version Information
**Request**: `<S0020042796F02D02FN>`  
**Response**: `<R0020042796F02D02XP33LR_V0.04.02HF>`

### 07 - Module Type
**Request**: `<S0020042796F02D07FI>`  
**Response**: `<R0020042796F02D0730FK>` (30 hex = 48 decimal = XP33 code 11 + offset)

### 10 - Status Query
**Request**: `<S0020042796F02D10FO>`  
**Response**: `<R0020042796F02D1000FP>` (00 = normal status)

### 12 - Channel States  
**Request**: `<S0020042796F02D12FM>`  
**Response**: `<R0020042796F02D12xxxxx000BF>` (3 channels at 0% dimming)

### 04 - LINK_NUMBER
**Request**: `<S0020042796F02D04FL>`  
**Response**: `<R0020042796F02D0404FO>` (links 4 configured)

## Channel Control Data Points

### 13-15 - Individual Channel Dimming (0-100%)
- **Channel 1**: Data point 13
- **Channel 2**: Data point 14  
- **Channel 3**: Data point 15

**Format**: `xxxxx` = 5-digit hex value representing 3 channels
- Bytes 0-1: Channel 1 level (00-64 hex = 0-100%)
- Bytes 2-3: Channel 2 level (00-64 hex = 0-100%)
- Byte 4: Channel 3 level (00-64 hex = 0-100%)

## Implementation

```yaml
# config.yml
devices:
  0020042796: XP33
```

### Response Generation
1. Parse incoming data point request
2. Extract data point number from F02D{XX}
3. Generate appropriate response based on data point
4. Calculate checksum and format as `<R{serial}F02D{point}{data}{checksum}>`

### Error Handling
- Invalid data points: No response
- Malformed requests: Log error, no response
- Out-of-range values: Clamp to valid ranges

## Technical Specifications

### Common Features (Both Variants)
- **Direct Inputs**: 5 impulse inputs (3 individual + all channels + scene select)
- **LED Outputs**: 3 channels for feedback (terminals H, I, K)
- **Scene Control**: 4 pre-programmable scenes with fade times
- **Soft-start**: 500ms rise time, 750ms off time
- **Protection**: Thermal protection, neutral break detection
- **Control**: Logarithmic regulation, minimum/maximum levels
- **Programming**: Up to 99 functions via data bus
- **Mounting**: DIN-rail DIN46277, 85x70x72mm

### Power Specifications
**XP33LR:**
- Supply: 110/230 VAC 50/60Hz  
- Load: 640VA total, 500VA max per channel
- Consumption: 0.3W idle

**XP33LED:**
- Supply: 110/230 VAC 50/60Hz
- Load: 3 x 100VA (100VA per channel)
- Consumption: 0.6W idle
- Edge Mode: Configurable LE/TE per channel (jumpers)

### Scene Programming
- **Scene 1-4**: Programmable light levels per channel
- **Fade Time**: Configurable 0.5 sec to 120 min
- **Scene Selection**: Via data point or direct input
- **Channel Isolation**: Individual channels can be excluded from scenes

## Configuration Options
- **serial_number**: 10-digit device serial
- **firmware_version**: Product ID and version string  
- **module_variant**: XP33LR or XP33LED
- **channel_count**: Number of dimmer channels (default: 3)
- **max_dimming_level**: Maximum brightness (default: 100%)
- **scene_config**: 4 pre-programmed scenes with fade times
- **edge_mode**: LE/TE configuration (XP33LED only)