# Migration of ConbusReceiveService to the new ConbusEventProtocol

Old protocol: ConbusProtocol 
- inherit
- base class
- override methods
- reuse difficult

New procotol: ConbusEventProtocol
- composition
- attach events
- reuse possible

## ConbusDiscoverService

ConbusDiscoverService has been migrated from ConbusProtocol to ConbusEventProtocol
Write a how to migration:
- Analyse difference
- git log
- write spec

Migration of 1 service:
- ConbusReceiveService
- explain what to do
