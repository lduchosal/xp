# Get link number of a module

Use CLI to get the link number for a specific module

## CLI usage

Command:
```
xp conbus linknumber get <serial_number>
```

xp conbus linknumber get <serial_number> <link_number>

Output:
```
{
  "success": true,
  "link_number": "10",
  "serial_number": "0020045057",
  "sent_telegram": "<S0020045057F02D04FG>",
  "received_telegrams": [
    "<R0020045057F02D0400FH>"
  ],
  "error": null,
  "timestamp": "2025-09-26T13:11:25.820383",
}


```
Command:
```
xp conbus linknumber set <serial_number> <link_number>
```

xp conbus linknumber set <serial_number> <link_number>

update set linknumber response to add 
  "link_number": "04",

Output:
```
{
  "success": true,
  "link_number": "04",
  "result": "ACK",
  "serial_number": "0020045057",
  "sent_telegram": "<S0020045057F02D04FG>",
  "received_telegrams": [
    "<R0020045057F02D0400FH>"
  ],
  "error": null,
  "timestamp": "2025-09-26T13:11:25.820383",
}
```
## Service

`ConbusLinknumberService` to handle module link number assignment:

reuse existing implementation : get datapoint LINK_NUMBER

## Tests



## Quality

**Quality assurance checklist:**
- [ ] Run `pdm run typecheck` - Type checking passes
- [ ] Run `pdm run lint` - Linting passes
- [ ] Run `pdm run test-unit` - Unit tests pass
- [ ] Run `pdm run test-integration` - Integration tests pass
- [ ] Run `pdm run test` - Full test suite with coverage
- [ ] Code coverage meets requirements (60%+)
- [ ] Documentation updated
- [ ] Error handling implemented
- [ ] Input validation added

