# Print Action Table

Display action table configurations from conson.yml

## Overview

Provides CLI commands to view action table configurations stored in conson.yml without connecting to hardware modules. Useful for reviewing configurations before uploading or documenting existing setups.

## CLI Commands

### List all modules with action tables

```bash
xp conbus actiontable list
```

**Output:**
```json
{
  "modules": [
    {
      "serial_number": "0020044974",
      "module_type": "CP20"
    },
    {
      "serial_number": "0020044991",
      "module_type": "XP24"
    },
    {
      "serial_number": "0020045123",
      "module_type": "XP24"
    }
  ],
  "total": 3
}
```

### Show action table for specific module

```bash
xp conbus actiontable show <serial_number>
```

**Example:**
```bash
xp conbus actiontable show 0020044974
```

```bash
xp conbus actiontable show <serial_number>
```

**output format:**
```json
{
  "serial_number": "0020044974",
  "name": "A1",
  "module_type": "CP20",
  "module_type_code": 2,
  "link_number": 0,
  "module_number": 0,
  "auto_report_status": "PP",
  "action_table": [
    "CP20 0 0 > 1 OFF",
    "CP20 0 0 > 2 OFF",
    "CP20 0 0 > 3 OFF",
    "CP20 0 0 > 4 OFF",
    "CP20 0 1 > 1 ~ON",
    "CP20 0 1 > 2 ON",
    "CP20 0 1 > 3 ON",
    "CP20 0 1 > 4 ON"
  ]
}
```

## conson.yml Format

The commands read from existing conson.yml configuration:

```yaml
- name: A1
  serial_number: "0020044974"
  module_type: CP20
  module_type_code: 02
  link_number: 0
  action_table:
    - CP20 0 0 > 1 OFF
    - CP20 0 0 > 2 OFF
    - CP20 0 0 > 3 OFF
    - CP20 0 0 > 4 OFF
    - CP20 0 1 > 1 ~ON
    - CP20 0 1 > 2 ON
    - CP20 0 1 > 3 ON
    - CP20 0 1 > 4 ON

- name: A4
  serial_number: "0020044991"
  module_type: XP24
  module_type_code: 07
  link_number: 2
  action_table:
    - CP20 0 0 > 1 OFF
    - CP20 0 0 > 2 OFF
    - CP20 0 1 > 1 ~ON
    - CP20 0 1 > 2 ON
```

## Error Handling

### No conson.yml found
```bash
$ xp conbus actiontable list
Error: conson.yml not found in current directory
```

### Module not found
```bash
$ xp conbus actiontable show 0020099999
Error: Module 0020099999 not found in conson.yml
```

### No action table configured
```bash
$ xp conbus actiontable show 0020044974
Error: No action_table configured for module 0020044974
```

## Implementation Plan

### CLI Layer

**File:** `src/xp/cli/commands/conbus/conbus_actiontable_commands.py` *(existing)*

**New commands:**
1. `conbus_list_actiontable()` - List all modules with action tables
2. `conbus_show_actiontable()` - Show action table for specific module

**Implementation:**

```python
@conbus_actiontable.command("list", short_help="List modules with ActionTable")
def conbus_list_actiontable() -> None:
    """List all modules with action table configurations from conson.yml.

    Raises:
        ActionTableError: If conson.yml not found or cannot be read.
    """
    
    service: ActionTableListService = (
        ctx.obj.get("container").get_container().resolve(ActionTableListService)
    )

    def on_finish(
        list,
    ) -> None:
        """Handle successful completion of action table list.
        """
        click.echo(json.dumps(list, indent=2, default=str))

    def error_callback(error: str) -> None:
        """Handle errors during action table list.

        Args:
            error: Error message string.
        """
        click.echo(error)

    with service:
        service.start(
            finish_callback=on_finish,
            error_callback=error_callback,
        )
    


@conbus_actiontable.command("show", short_help="Show ActionTable configuration")
@click.argument("serial_number", type=SERIAL)
def conbus_show_actiontable(serial_number: str) -> None:
    """Show action table configuration for a specific module from conson.yml.

    Args:
        serial_number: 10-digit module serial number.

    Raises:
        ActionTableError: If conson.yml not found, module not found,
            or no action_table configured.
    """
    
    service: ActionTableShowService = (
        ctx.obj.get("container").get_container().resolve(ActionTableShowService)
    )

    def on_finish(
        module,
    ) -> None:
        """Handle successful completion of action table show.
        """
        click.echo(json.dumps(module, indent=2, default=str))

    def error_callback(error: str) -> None:
        """Handle errors during action table show.

        Args:
            error: Error message string.
        """
        click.echo(error)

    with service:
        service.start(
            serial_number=serial_number,
            finish_callback=on_finish,
            error_callback=error_callback,
        )
    
```

### Testing Layer

#### Unit Tests

**File:** `tests/unit/test_cli/test_conbus_actiontable_commands.py`

**Test methods:**
- `test_conbus_list_actiontable_success()`
- `test_conbus_list_actiontable_no_modules()`
- `test_conbus_list_actiontable_missing_config()`
- `test_conbus_show_actiontable_table_format()`
- `test_conbus_show_actiontable_json_format()`
- `test_conbus_show_actiontable_yaml_format()`
- `test_conbus_show_actiontable_module_not_found()`
- `test_conbus_show_actiontable_no_action_table()`

## Use Cases

### 1. Review Configuration Before Upload
```bash
# Check what action tables are configured
xp conbus actiontable list

# Review specific module configuration
xp conbus actiontable show 0020044974

# Upload if correct
xp conbus actiontable upload 0020044974
```

### 2. Documentation Generation
```bash
# Export all action table configurations to JSON
for serial in $(xp conbus actiontable list | grep -E '[0-9]{10}' | awk '{print $1}'); do
    xp conbus actiontable show $serial --format json > actiontable_$serial.json
done
```

### 3. Configuration Comparison
```bash
# Compare configuration before and after changes
xp conbus actiontable show 0020044974 > before.txt
# Edit conson.yml
xp conbus actiontable show 0020044974 > after.txt
diff before.txt after.txt
```

## Benefits

1. **No Hardware Connection Required** - View configurations without connecting to modules
2. **Quick Configuration Review** - List and inspect action tables efficiently
3. **Documentation** - Export configurations for documentation or backup
4. **Validation** - Check configurations before uploading to hardware
5. **Multiple Output Formats** - Support for table, JSON, and YAML formats

## Notes

- These commands are read-only and do not modify conson.yml
- No hardware connection or network access required
- Commands work offline with local conson.yml file
- Output formats designed for both human reading and machine processing
