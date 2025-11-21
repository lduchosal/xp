# Feature: Broadcast Telegram to All Connected Clients

## Context
Enable ConbusServerService to broadcast telegrams from device services to all connected clients simultaneously.

## Current State
- Server maintains collector thread polling device telegram buffers (server_service.py:417-428)
- Telegrams (strings) stored in single shared `collector_buffer: queue.Queue[str]` (server_service.py:72)
- Buffer sent to clients in `_handle_client` loop (server_service.py:207-213)
- Current architecture: single queue consumed by multiple client threads causes telegrams to go to only one client

## Target Behavior
All telegrams from device services broadcast to all connected clients:
1. Multiple device services contribute telegrams to collection system
2. Collector thread gathers telegrams from all device services
3. All collected telegrams broadcast to every connected client
4. No exclusions - every client receives every telegram

## Implementation Checklist

### Phase 1: Refactor Buffer Architecture
- [ ] Replace `collector_buffer: queue.Queue[str]` with per-client queue structure
- [ ] Create `client_buffers: Dict[socket.socket, queue.Queue[str]]` to store individual client queues
- [ ] Add `client_buffers_lock: threading.Lock` for thread-safe dictionary operations

### Phase 2: Client Queue Management
- [ ] Update `_handle_client` to create new queue in `client_buffers` on connection
- [ ] Update `_handle_client` to remove queue from `client_buffers` on disconnect
- [ ] Ensure thread-safe access to `client_buffers` dictionary during add/remove operations

### Phase 3: Broadcast Logic in Collector Thread
- [ ] Modify `_device_collector_thread` to iterate through all `client_buffers`
- [ ] For each collected telegram, put it into every client's individual queue
- [ ] Use thread-safe operations when accessing `client_buffers` dictionary

### Phase 4: Client Thread Consumption
- [ ] Modify `_handle_client` loop to read from its own dedicated queue
- [ ] Replace `self.collector_buffer.get_nowait()` with per-client queue access
- [ ] Maintain existing send logic (encode to latin-1 and socket.send)

### Phase 5: Thread Safety
- [ ] Verify `client_buffers_lock` protects all dictionary operations
- [ ] Test concurrent client connections and disconnections
- [ ] Validate no race conditions in telegram routing
- [ ] Ensure collector thread safely iterates client buffers during modifications

### Phase 6: Quality Assurance
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
