# Feature Specification: ConsonConnectionPool

## Overview

This specification introduces a connection pooling mechanism for the XP project using the `generic-connection-pool` Python library. The `ConsonConnectionPool` will replace direct socket management in `ConbusService` to provide reliable, reusable TCP connections with automatic lifecycle management.

## Background

Currently, the `ConbusService` (src/xp/services/conbus_service.py:31) manages socket connections directly with basic connect/disconnect operations. This approach has limitations:

- No connection reuse between requests
- Manual connection state management
- No automatic reconnection after timeouts
- Potential socket leaks on errors
- No connection lifecycle management

## Proposed Solution

### 1. Introduction of generic-connection-pool Library

Add `generic-connection-pool` as a project dependency to provide robust connection pooling capabilities.

```bash
pip install generic-connection-pool
```

### 2. ConsonConnectionPool Implementation

Create a new `ConsonConnectionPool` class that:

- Manages a single reusable TCP connection to Conbus servers
- Automatically reconnects after connection expiry (6 hours)
- Provides connection health checking
- Handles connection lifecycle and cleanup

### 3. Socket Connection Manager

Implement a custom connection manager for TCP sockets:

```python
class ConbusSocketConnectionManager:
    """Connection manager for TCP socket connections to Conbus servers"""

    def __init__(self, host: str, port: int, timeout: float):
        self.host = host
        self.port = port
        self.timeout = timeout

    def create(self) -> socket.socket:
        """Create and configure a new TCP socket connection"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(self.timeout)
        sock.connect((self.host, self.port))
        return sock

    def dispose(self, connection: socket.socket) -> None:
        """Close and cleanup socket connection"""
        try:
            connection.close()
        except Exception:
            pass

    def check_aliveness(self, connection: socket.socket) -> bool:
        """Verify if connection is still alive"""
        try:
            # Send empty data to check connection
            connection.send(b'')
            return True
        except (socket.error, OSError):
            return False
```

### 4. Integration with ConbusService

Modify `ConbusService` to use `ConsonConnectionPool`:

- Replace direct socket management (src/xp/services/conbus_service.py:43,90)
- Inject connection pool in constructor
- Use pool.acquire() and pool.release() for connection management
- Remove manual connect/disconnect methods

## Configuration Parameters

### Recommended Values

Based on the Conbus protocol requirements and connection patterns:

```python
ConsonConnectionPool(
    connection_manager=ConbusSocketConnectionManager(host, port, timeout),
    min_idle=1,              # Single connection always available
    max_size=1,              # Single connection maximum
    idle_timeout=21600,      # 6 hours (6 * 60 * 60 seconds)
    max_lifetime=21600,      # 6 hours maximum connection lifetime
    background_collector=True # Enable automatic cleanup
)
```

### Parameter Justification

**min_idle=1**
- Ensures one connection is always ready for immediate use
- Matches requirement for "single connection"
- Minimizes connection establishment overhead

**max_size=1**
- Enforces single connection constraint
- Prevents connection proliferation
- Aligns with Conbus server expectations

**idle_timeout=21600 (6 hours)**
- Matches specified 6-hour connection expiry requirement
- Allows for extended idle periods typical in Conbus communication
- Prevents stale connections that may be dropped by server

**max_lifetime=21600 (6 hours)**
- Enforces mandatory reconnection every 6 hours
- Ensures fresh connections and prevents long-term socket issues
- Complies with connection refresh requirements

**background_collector=True**
- Enables automatic connection lifecycle management
- Handles cleanup without blocking main operations
- Provides monitoring and maintenance capabilities

## Implementation Plan

### Phase 1: Core Infrastructure
1. Add `generic-connection-pool` dependency
2. Create `ConbusSocketConnectionManager`
3. Implement `ConsonConnectionPool` wrapper class

### Phase 2: Service Integration
1. Modify `ConbusService` constructor to accept connection pool
2. Replace socket management with pool operations
3. Update connection status methods

### Phase 3: Configuration & Testing
1. Add connection pool configuration to `cli.yml`
2. Implement comprehensive testing
3. Add monitoring and logging

## Benefits

1. **Reliability**: Automatic connection health monitoring and recovery
2. **Performance**: Connection reuse reduces establishment overhead
3. **Maintainability**: Centralized connection lifecycle management
4. **Monitoring**: Built-in connection pool metrics and status
5. **Flexibility**: Configurable connection parameters and behavior

## Migration Strategy

The implementation will be backward compatible:
- Existing `ConbusService` interface remains unchanged
- Connection pool is injected as dependency
- Fallback to direct socket management if pool unavailable
- Gradual rollout with feature flags

## Testing Requirements

1. **Unit Tests**: Connection manager lifecycle operations
2. **Integration Tests**: Pool behavior with Conbus protocol
3. **Load Tests**: Connection reuse under multiple requests
4. **Failure Tests**: Connection recovery and error handling
5. **Timeout Tests**: 6-hour expiry and reconnection behavior

## Dependencies

- `generic-connection-pool >= 0.4.1`
- Existing socket and logging infrastructure
- YAML configuration system

## Risk Mitigation

1. **Connection Failures**: Pool handles automatic retry and failover
2. **Memory Leaks**: Background collector prevents resource accumulation
3. **Configuration Errors**: Validation and default fallbacks
4. **Performance Impact**: Minimal overhead with single connection design