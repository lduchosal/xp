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

Modify `ConbusService` to use singleton `ConbusConnectionPool`:

- Replace direct socket management (src/xp/services/conbus_service.py:43,90)
- Initialize singleton connection pool in constructor
- Use context manager pattern for automatic connection management
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

### Phase 1: Singleton Implementation (Recommended First Approach)

**Thread-Safe Singleton Connection Pool**

```python
# src/xp/services/conbus_connection_pool.py
import threading
import socket
from typing import Optional
from generic_connection_pool import ConnectionPool
from ..models import ConbusClientConfig

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

class ConbusConnectionPool:
    """Singleton connection pool for Conbus TCP connections"""

    _instance: Optional['ConbusConnectionPool'] = None
    _lock = threading.Lock()

    def __new__(cls) -> 'ConbusConnectionPool':
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized'):
            return

        self._initialized = True
        self._pool: Optional[ConnectionPool] = None
        self._config: Optional[ConbusClientConfig] = None

    def initialize(self, config: ConbusClientConfig):
        """Initialize the connection pool with configuration"""
        if self._pool is not None:
            return

        self._config = config
        connection_manager = ConbusSocketConnectionManager(
            config.ip, config.port, config.timeout
        )

        self._pool = ConnectionPool(
            connection_manager,
            min_idle=1,
            max_size=1,
            idle_timeout=21600,  # 6 hours
            max_lifetime=21600,  # 6 hours
            background_collector=True
        )

    def acquire_connection(self) -> socket.socket:
        """Acquire a connection from the pool"""
        if self._pool is None:
            raise RuntimeError("Connection pool not initialized")
        return self._pool.acquire()

    def release_connection(self, connection: socket.socket) -> None:
        """Release a connection back to the pool"""
        if self._pool is not None:
            self._pool.release(connection)

    def __enter__(self):
        """Context manager entry - acquire connection"""
        self._current_connection = self.acquire_connection()
        return self._current_connection

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - release connection"""
        if hasattr(self, '_current_connection') and self._current_connection:
            self.release_connection(self._current_connection)
            self._current_connection = None

    @classmethod
    def get_instance(cls) -> 'ConbusConnectionPool':
        """Get the singleton instance"""
        return cls()

    @classmethod
    def reset_instance(cls):
        """Reset singleton for testing"""
        with cls._lock:
            cls._instance = None
```

**Usage with Context Manager Pattern**

```python
# In ConbusService methods
def send_raw_telegram(self, telegram: Optional[str] = None) -> ConbusResponse:
    """Send telegram using connection pool with automatic acquire/release"""
    request = ConbusRequest(telegram=telegram)

    try:
        # Use context manager for automatic connection management
        with self._connection_pool as connection:
            # Send telegram
            if telegram is not None:
                connection.send(telegram.encode("latin-1"))
                self.logger.info(f"Sent telegram: {telegram}")

            self.last_activity = datetime.now()

            # Receive responses
            responses = self._receive_responses_with_connection(connection)

            return ConbusResponse(
                success=True,
                request=request,
                sent_telegram=telegram,
                received_telegrams=responses,
            )
            # Connection automatically released here

    except Exception as e:
        error_msg = f"Failed to send telegram: {e}"
        self.logger.error(error_msg)
        return ConbusResponse(
            success=False,
            request=request,
            error=error_msg,
        )
```

**Alternative: Connection Pool Context Manager**

```python
class ConnectionPoolContext:
    """Context manager for automatic connection acquire/release"""

    def __init__(self, pool: ConbusConnectionPool):
        self.pool = pool
        self.connection = None

    def __enter__(self) -> socket.socket:
        self.connection = self.pool.acquire_connection()
        return self.connection

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.connection:
            self.pool.release_connection(self.connection)

# Usage in ConbusService
def get_connection(self) -> ConnectionPoolContext:
    """Get connection with automatic management"""
    return ConnectionPoolContext(self._connection_pool)

def send_raw_telegram(self, telegram: Optional[str] = None) -> ConbusResponse:
    """Send telegram with context manager"""
    request = ConbusRequest(telegram=telegram)

    try:
        with self.get_connection() as connection:
            if telegram is not None:
                connection.send(telegram.encode("latin-1"))
                self.logger.info(f"Sent telegram: {telegram}")

            self.last_activity = datetime.now()
            responses = self._receive_responses_with_connection(connection)

            return ConbusResponse(
                success=True,
                request=request,
                sent_telegram=telegram,
                received_telegrams=responses,
            )
    except Exception as e:
        return ConbusResponse(
            success=False,
            request=request,
            error=f"Failed to send telegram: {e}",
        )
```

### Phase 2: Service Integration
1. Modify `ConbusService` constructor to initialize singleton pool
2. Replace direct socket management with context manager pattern
3. Update connection status methods
4. Implement automatic acquire/release using `with` statements

### Phase 3: Configuration & Testing
1. Add connection pool configuration to `cli.yml`
2. Implement comprehensive testing with pool reset
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
- Singleton connection pool is automatically initialized
- No changes required to existing service usage
- Zero configuration needed for basic functionality

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