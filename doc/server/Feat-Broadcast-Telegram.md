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
- [ ] Create `ClientBufferManager` class to encapsulate client queue management
  - [ ] Internal `_buffers: Dict[socket.socket, queue.Queue[str]]` attribute
  - [ ] Internal `_lock: threading.Lock` for thread-safe operations
  - [ ] Method `register_client(socket) -> queue.Queue[str]` - create and return new queue
  - [ ] Method `unregister_client(socket) -> None` - remove client queue
  - [ ] Method `broadcast(telegram: str) -> None` - put telegram into all client queues
  - [ ] Method `get_queue(socket) -> Optional[queue.Queue[str]]` - retrieve client's queue
- [ ] Replace `collector_buffer: queue.Queue[str]` with `client_buffers: ClientBufferManager`

### Phase 2: Client Queue Management
- [ ] Update `_handle_client` to call `client_buffers.register_client(socket)` on connection
- [ ] Store returned queue reference for this client thread
- [ ] Update `_handle_client` to call `client_buffers.unregister_client(socket)` on disconnect
- [ ] Thread safety handled internally by `ClientBufferManager`

### Phase 3: Broadcast Logic in Collector Thread
- [ ] Modify `_device_collector_thread` to call `client_buffers.broadcast(telegram)` for each collected telegram
- [ ] Remove direct queue.put operations
- [ ] Thread safety handled internally by `ClientBufferManager.broadcast()`

### Phase 4: Client Thread Consumption
- [ ] Modify `_handle_client` loop to read from client's dedicated queue (obtained from register_client)
- [ ] Replace `self.collector_buffer.get_nowait()` with `client_queue.get_nowait()`
- [ ] Maintain existing send logic (encode to latin-1 and socket.send)

### Phase 5: Thread Safety
- [ ] Verify `ClientBufferManager` uses lock for all dictionary operations
- [ ] Test concurrent client connections and disconnections
- [ ] Validate no race conditions in telegram routing
- [ ] Ensure collector thread's broadcast safely handles concurrent client add/remove

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
- Collector thread independent of request processing (server_service.py:417-430)
- Shared telegram buffer across device services
- `ClientBufferManager` encapsulates thread safety with internal lock
- Type hints for all methods (mypy strict)
- Absolute imports only
- Line length: 88 characters

## Architecture Alignment
- Layer: Services (src/xp/services/server/)
- Pattern: Event-driven with thread-safe state management
- Logging: Use `self.logger` for connection/broadcast events
- Error handling: Specific exceptions with context logging
- No business logic leakage to protocol layer
