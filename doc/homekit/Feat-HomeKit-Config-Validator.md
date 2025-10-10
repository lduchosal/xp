# HomeKit Config Validator

Validates coherence between configuration sections across homekit.yml and conson.yml files.

## Overview

The validator ensures consistency and integrity across:
- Conson module configurations
- HomeKit accessory definitions
- Room-accessory mappings

## Conson Configuration

Validates conson module definitions in `conson.yml`.

**Validation Rules:**
- [ ] Module names must be unique
- [ ] Serial numbers must be unique
- [ ] Pydantic v2 automatic validation for required fields

**Implementation:**
- Model: `src/xp/models/homekit_conson_config.py` (Pydantic v2)
- Service: `src/xp/services/homekit_conson_service.py`

**File:** `conson.yml`

```yaml
- name: A1
  serial_number: 0012345001
  module_type: XP130
  module_type_code: 13
  link_number: 12
  module_number: 0001
  conbus_ip: 127.0.0.1
  conbus_port: 10001
  sw_version: XP130_V0.10.04
  hw_version: XP130_HW_Rev B

- name: A2
  serial_number: 0012345002
  module_type: XP20
  module_type_code: 33
  link_number: 11
  module_number: 0011
```


---

## HomeKit Accessories Configuration

Validates accessory definitions in `homekit.yml`.

**Validation Rules:**
- [ ] Accessory names must be unique
- [ ] Serial numbers must exist in conson.yml
- [ ] Valid output numbers for module type
- [ ] Pydantic v2 automatic validation for required fields
- [ ] Valid service types (lightbulb, outlet)

**Cross-Reference Checks:**
- [ ] Serial numbers match conson.yml entries
- [ ] Output numbers within module capabilities

**File:** `homekit.yml`

```yaml
accessories:
  - name: lumiere_salon
    id: A4R2
    serial_number: 0012345004
    output: 01
    description: Salon
    service: lightbulb

  - name: lumiere_salle_a_manger
    id: A4R3
    serial_number: 0012345004
    output: 02
    description: Salle à manger
    service: lightbulb
```

---

## HomeKit Rooms Configuration

Validates room-accessory mappings in `homekit.yml`.

**Validation Rules:**
- [ ] Room names must be unique
- [ ] All referenced accessories must exist in accessories section
- [ ] No orphaned accessories (accessories not assigned to any room)
- [ ] No duplicate accessory assignments across rooms
- [ ] Pydantic v2 automatic validation for required fields

**Cross-Reference Checks:**
- [ ] All room.accessories[] exist in accessories section
- [ ] All accessories are assigned to at least one room

**File:** `homekit.yml` (rooms section)

```yaml
bridge:
  name: "Maison"

  rooms:
    - name: "Salon"
      accessories:
      - lumiere_salon
      - lumiere_salle_a_manger
      - lumiere_cuisine
      - prise_salon

    - name: "Chambre1"
      accessories:
      - lumiere_chambre1
      - prise_chambre1
```

---

## CLI Implementation

**Commands:**
- `xp homekit config validate` - Validate configuration files
- `xp homekit config print` - Display parsed configuration

**Implementation Details:**
- Add `config` subgroup to existing `homekit` command group
- Follow project patterns: `src/xp/cli/commands/homekit.py`
- Use Click decorators and HelpColorsGroup
- Leverage existing service decorators: `@service_command()`
- Register in `cli.main.py` (already imports homekit)

**Command Structure:**
```python
@homekit.group()
def config():
    """HomeKit configuration management"""

@config.command()
@service_command()
def validate():
    """Validate homekit.yml and conson.yml coherence"""

@config.command()
@service_command()
def print():
    """Print parsed configuration"""
```


---

## Implementation Checklist

**Core Components:**
- [ ] Conson config validator service
- [ ] HomeKit config validator service
- [ ] Cross-reference validation service
- [ ] CLI command for validation
- [ ] Unit tests for all validators
- [ ] Integration tests for cross-validation

**Error Handling:**
- [ ] Clear error messages with file/line references
- [ ] Validation summary report
