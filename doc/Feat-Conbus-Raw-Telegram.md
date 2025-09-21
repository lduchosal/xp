# Conbus raw telegrams

use cli to send raw and multiple telegrams to the conbus

## Cli usage

Command:
xp conbus raw '\<S2113010000F02D12>\<S2113010001F02D12>\<S2113010002F02D12>'

output:
```
<R2113010000F02D12>
<R2113010001F02D12>
<S2113010002F02D12>
```

**CLI checklist:**
- [ ] Add `raw` subcommand to conbus group
- [ ] Accept raw telegram string as argument
- [ ] use conbus_raw_service to send telegrams
- [ ] Add CLI command in `src/xp/cli/commands/conbus_raw_commands.py`
- [ ] Register command in `src/xp/cli/commands/conbus.py`
- [ ] As few as possible logic in cli, prefer put logic in service

## Service

`ConbusRawService` to handle raw telegram sequences:

- Send raw parameter telegram via TCP connection
- no prior validation
- no received validation

Key methods:
- `send_raw_telegrams(raw_input: str) -> ConbusRawResponse`
- `parse_telegram_sequence(input: str) -> List[str]`

**Implementation checklist:**
- [ ] Create `ConbusRawService` class in `src/xp/services/conbus_raw_service.py`
- [ ] Define `ConbusRawResponse` model in `src/xp/models/conbus_raw.py`
- [ ] Reuse `ConbusService` to send raw telegrams

## Tests

CLI integration tests in `tests/integration/test_conbus_raw_integration.py`:

- `test_conbus_raw_single_telegram()` - Send single raw telegram
- `test_conbus_raw_multiple_telegrams()` - Send telegram sequence
- `test_conbus_raw_connection_error()` - Handle network failures

**Test checklist:**
- [ ] Test CLI command parsing and execution


#
```
Sent custom telegram: <S0020042796F02D12FM><S0020044991F02D12FD><S0020044974F02D12FI><S0020044966F02D12FL><S0020044989F02D12FK><S0020044964F02D12FJ><S0020044986F02D12FF>
Received telegram: <R0020044991F02D12xxxx1000FD>
Received telegram: <R0020044974F02D12xxxx0100FI>
Received telegram: <R0020044966F02D12xxxx0001FL>
Received telegram: <R0020044964F02D12xxxx1111FI>
Received telegram: <R0020042796F02D12xxxxx000BF>
Received telegram: <R0020044986F02D12xxxx0010FF>
Received telegram: <R0020044989F02D12xxxx0000FL>

[TX1] <S0020042796F02D12FM> - [RX1] <R0020044991F02D12xxxx1000FD> 2
[TX2] <S0020044991F02D12FD> - [RX2] <R0020044974F02D12xxxx0100FI> 3
[TX3] <S0020044974F02D12FI> - [RX3] <R0020044966F02D12xxxx0001FL> 4
[TX4] <S0020044966F02D12FL> - [RX4] <R0020044964F02D12xxxx1111FI> 6
[TX5] <S0020044989F02D12FK> - [RX5] <R0020042796F02D12xxxxx000BF> 1
[TX6] <S0020044964F02D12FJ> - [RX6] <R0020044986F02D12xxxx0010FF> 7
[TX7] <S0020044986F02D12FF> - [RX7] <R0020044989F02D12xxxx0000FL> 5

```

