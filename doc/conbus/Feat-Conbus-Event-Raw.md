# Conbus events

conbus cli send event telegrams.

## cli usage
```
xp conbus event raw
xp conbus event raw module_type link_number input_number time_ms 
```

doc:
```
module_type: ModuleTypeCode.MODULE
link_number: 0-99
input_number: 0-9
time_ms: time between MAKE and BREAK. default 1000ms
```

event:
```
<E{module_type_code}L{link_number}I{input_number}{make_code:M}{checksum}}>
wait 1000 ms
<E{module_type_code}L{link_number}I{input_number}{break_code:B}{checksum}}>
```

### Samples

xp conbus event raw CP20 00 00 
```
<E02L00I00MAK>
wait 1000 ms
<E02L00I00BAK>
```

xp conbus event raw XP20 00 00 
```
<E33L00I00MAK>
wait 1000 ms
<E33L00I00BAK>
```