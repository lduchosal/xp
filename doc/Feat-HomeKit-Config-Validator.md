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
- [ ] Required fields present: name, serial_number, module_type, module_type_code
- [ ] Valid module_type_code ranges
- [ ] IP/port format validation

**Implementation:**
- Model: `src/xp/models/homekit_conson_config.py` (Pydantic v2)
- Service: `src/xp/services/homekit_conson_service.py`

**File:** `conson.yml`

```yaml
- name: A1
  serial_number: 0020041013
  module_type: XP130
  module_type_code: 13
  link_number: 12
  module_number: 0001
  conbus_ip: 10.0.3.26
  conbus_port: 10001
  sw_version: XP130_V0.10.04
  hw_version: XP130_HW_Rev B

- name: A2
  serial_number: 0020037487
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
- [ ] Required fields: name, id, serial_number, output, service
- [ ] Valid service types (lightbulb, outlet, etc.)

**Cross-Reference Checks:**
- [ ] Serial numbers match conson.yml entries
- [ ] Output numbers within module capabilities

**File:** `homekit.yml`

```yaml
accessories:
  - name: lumiere_salon
    id: A4R2
    serial_number: 0020044991
    output: 01
    description: Salon
    service: lightbulb

  - name: lumiere_salle_a_manger
    id: A4R3
    serial_number: 0020044991
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

    - name: "Nathan"
      accessories:
      - lumiere_nathan
      - prise_nathan
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
- [ ] Exit codes for CI/CD integration