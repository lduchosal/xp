# Conbus events

conbus cli send event telegrams.

The list action, reads conson.yml with existing DI injected ConsonModuleListConfig.
Parse action table from module list, and generate a list of configured event on the bus.
The list regroups th

## cli usage
```
xp conbus event list
```

conson.yml
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

Outputs
```
{
    "events": [
        "E33L10I00": ["A3", "A4"],
        "E33L10I08": ["A3", "A4"],
        ...
    ]
}
```
