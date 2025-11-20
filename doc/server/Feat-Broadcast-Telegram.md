# Feature: Broadcast Telegram to Connected Clients

## Context
Enable ConbusServerService to broadcast telegrams from device services to all connected clients, excluding the originating client.

## Current State
- Server maintains collector thread polling device telegram buffers (server_service.py:416-428)
- Telegrams stored in `collector_buffer` (server_service.py:71)
- Buffer sent to clients in `_handle_client` loop (server_service.py:205-209)
- No tracking of telegram origination client

## Target Behavior
When client sends telegram triggering device response:
1. Server notes originating client identity
2. Broadcasts resulting telegrams to all other connected clients
3. Excludes originating client from receiving own triggered responses

## Implementation Checklist

### Phase 1: Client Tracking Infrastructure
- [ ] Add `active_clients: Set[socket.socket]` to ServerService state
- [ ] Update `_handle_client` to register socket in `active_clients` on connection
- [ ] Update `_handle_client` to unregister socket in `active_clients` on disconnect
- [ ] Ensure thread-safe access to `active_clients` using existing `socket_list_lock`

### Phase 2: Request Tracking
- [ ] When client sends telegram in `_handle_client`, tag resulting device telegrams with originating socket

### Phase 3: Selective Broadcast
- [ ] Modify buffer send logic in `_handle_client` to filter telegrams by origination
- [ ] Skip telegrams where `client_socket == current_socket`
- [ ] Send all other telegrams (device-originated or from different clients)

### Phase 4: Thread Safety
- [ ] Verify `socket_list_lock` covers new socket set operations
- [ ] Test concurrent client connections and disconnections
- [ ] Validate no race conditions in telegram routing

### Phase 5: Quality Assurance
Reference: `doc/quality.md`, `doc/coding.md`, `doc/architecture.md`

- [ ] Type hints for all new/modified functions (mypy strict)
- [ ] Docstrings for modified public methods (Args, Returns)
- [ ] Unit tests for client tracking logic (mock sockets)
- [ ] Integration tests for multi-client broadcast scenarios
- [ ] Thread safety tests (concurrent operations)
- [ ] `pdm run typecheck` - Mypy validation
- [ ] `pdm run flake8` - Code quality
- [ ] `pdm lint` - Ruff linting
- [ ] `pdm format` - Black formatting
- [ ] `pdm test-quick` - Test validation
- [ ] Minimum 75% test coverage maintained

## Technical Constraints
- Multi-threaded: One thread per client (server_service.py:179-183)
- Collector thread independent of request processing (server_service.py:416-428)
- Shared telegram buffer across device services
- Must use existing `telegram_buffer_lock` for thread safety
- Pydantic models for any new data structures
- Absolute imports only
- Line length: 88 characters

## Architecture Alignment
- Layer: Services (src/xp/services/server/)
- Pattern: Event-driven with thread-safe state management
- Logging: Use `self.logger` for connection/broadcast events
- Error handling: Specific exceptions with context logging
- No business logic leakage to protocol layer
