# Set link number to a module

## cli

xp conbus linknumber <serial_number> <link_number>

result:
```
{
  "success": true,
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

## service

reuse telegram_linknumber for telegram generation

## tests

## validation

