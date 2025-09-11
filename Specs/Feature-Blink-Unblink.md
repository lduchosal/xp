# Function Blink and Unblink

The function of a "Blink" of a conson modules control LED on the front panel:
- Blinks an LED on and off at regular intervals
- Often used as a status indicator (system alive)
- Identify module, see physical LED activity

## Blink function: 05 
Telegram:<S0020044964F05D00FN>
Type: System
Serial: 0020044964
Function: 05
DataPoint: 00

Telegram:<R0020044964F18DFA>
Type: Response
Serial: 0020044964
Function: 18 (ACK)
DataPoint:  


## Unblink function: 06

Telegram:<S0020030837F06D00FJ>
Type: System
Serial: 0020030837
Function: 05
DataPoint: 00

Telegram:<R0020030837F18DFA>
Type: Response
Serial: 0020030837
Function: 18 (ACK)
DataPoint:  

## Cli commands

xp blink <serial>
xp unblink <serial>

xp/cli/commands/blink_commands.py

## models

xp/models/blink_telegram.py (inherits telegram)

## services

xp/services/blink_service.py
