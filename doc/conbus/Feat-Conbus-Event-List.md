# Conbus events

conbus cli send event telegrams.

The list action, reads conson.yml with existing DI injected ConsonModuleListConfig.
Parse action table from module list, and generate a list of configured event on the bus.

## cli usage
```
xp conbus event list
```

### ConsonModuleListConfig
given conson.yml, read the action table, convert to event telegram and regroup common actions
```
- name: A3
  action_table:
    - XP20 10 0 > 0 OFF
    - XP20 10 0 > 1 OFF
    - XP20 10 0 > 2 OFF
    - XP20 10 8 > 0 ON
    - XP20 10 8 > 1 ON
    - XP20 10 8 > 2 ON
- name: A4
  action_table:
    - XP20 10 0 > 0 OFF
    - XP20 10 0 > 1 OFF
    - XP20 10 0 > 2 OFF
    - XP20 10 8 > 0 ON
    - XP20 10 8 > 1 ON
    - XP20 10 8 > 2 ON
```

### Conversion

Action table is formatted:
```
XP20 10 0 > 0 OFF

{module_type} {link_number} {input_number} > {make_or_break:~}{output_number} {action}
```

Converted to 

### Outputs
```
{
    "events": [
        "E33L10I00": ["A3", "A4"],
        "E33L10I08": ["A3", "A4"],
        ...
    ]
}
```
