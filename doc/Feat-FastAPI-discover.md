# FastAPI Conbus Discover Endpoint Specification

## Overview

This specification defines a REST API endpoint for performing Conbus device discover operations using FastAPI, building on the existing CLI discover functionality.

## Endpoint Specification

### POST /api/xp/conbus/discover

Initiates a Conbus discover operation to find devices on the network.

#### Request

```http
POST /api/xp/conbus/discover
{
}
```

#### Response

**Success (200 OK)**
```json
{
  "success": true,
  "request": {
    "telegram_type": "DISCOVERY",
    "serial_number": null
  },
  "sent_telegram": "<S0000000000F01D00FA>",
  "received_telegrams": [
    "<R0020030837F01DFM>",
    "<R0020044966F01DFK>",
    "<R0020042796F01DFN>"
  ],
  "discovered_devices": [
    {
      "serial": "0020030837",
      "telegram": "<R0020030837F01DFM>"
    },
    {
      "serial": "0020044966",
      "telegram": "<R0020044966F01DFK>"
    }
  ],
  "timestamp": "2024-01-15T10:30:45.123Z"
}
```

**Error (400 Bad Request)**
```json
{
  "success": false,
  "error": "Connection timeout: Unable to connect to 192.168.1.100:2113",
  "timestamp": "2024-01-15T10:30:45.123Z"
}
```

**Error (500 Internal Server Error)**
```json
{
  "success": false,
  "error": "Internal server error: Socket connection failed",
  "timestamp": "2024-01-15T10:30:45.123Z"
}
```

## Implementation Requirements

### Dependencies
- Add `fastapi>=0.104.0` to pyproject.toml dependencies
- Add `uvicorn>=0.24.0` for ASGI server
- Add `pydantic>=2.0.0` for request/response models

### Core Components

1. **API Models** (`src/xp/api/models/`)
   - `DiscoverRequest`: Pydantic model for request validation
   - `DiscoverResponse`: Pydantic model for response formatting
   - `DeviceInfo`: Model for discovered device information

2. **API Router** (`src/xp/api/routers/conbus.py`)
   - FastAPI router with `/discover` endpoint
   - Request validation and error handling
   - Integration with existing `ConbusDatapointService`

3. **FastAPI Application** (`src/xp/api/main.py`)
   - FastAPI app initialization
   - Router registration
   - CORS and middleware configuration

### Service Integration

The endpoint leverages existing functionality:
- `ConbusDatapointService` for TCP communication
- `TelegramService` for telegram parsing
- `DiscoverService` for response processing
- Existing error handling patterns from CLI commands

### Error Handling

- **Connection Errors**: Map to 400 Bad Request with descriptive messages
- **Timeout Errors**: Return 408 Request Timeout
- **Service Errors**: Return 500 Internal Server Error
- **Validation Errors**: Return 422 Unprocessable Entity (handled by FastAPI)

### Configuration

- Default configuration loaded from `api.yml`
- Environment variable support for production deployment

### Security Considerations

- Input validation via Pydantic models
- Rate limiting for discover operations
- Network access controls (firewall rules)
- No authentication required for internal network usage

### Testing Strategy

- Unit tests for API models and validation
- Integration tests with mock Conbus server
- End-to-end tests with real hardware (if available)
- Performance tests for concurrent discover operations

## Future Enhancements

1. **Device Caching**: Cache discovered devices with TTL
2. **Authentication**: Add API key or token-based auth
