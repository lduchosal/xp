# Feature: Broadcast Telegram to Connected Clients

## Overview
Enable ConbusServerService to broadcast telegrams from device services to all connected clients, excluding the originating client.

## Current Behavior
- Server maintains a collector thread that polls device telegram buffers (server_service.py:416-428)
- Collected telegrams are stored in `collector_buffer` (server_service.py:71)
- Buffer is sent to clients during `_handle_client` loop (server_service.py:205-209)
- No tracking of which client sent the original telegram

## Required Change
When a client sends a telegram that triggers a device response:
1. Server should note which client originated the request
2. Broadcast any resulting telegrams to **all other connected clients**
3. Exclude the originating client from receiving its own triggered responses

## Scope
- **Service**: `ServerService` (server_service.py)
- **Method**: `_handle_client` (processes client requests and sends buffers)
- **Requirement**: Track client identity per telegram to enable selective broadcast

## Constraints
- Multi-threaded client handling (server_service.py:179-183: one thread per client)
- Collector thread operates independently from request processing (server_service.py:416-428)
- Telegram buffer is shared across all device services
- Must maintain thread safety with existing `telegram_buffer_lock`
- No current socket set tracking for active clients

## Notes
Server accepts multiple concurrent connections via threading. Broadcast implementation requires:
- Socket set management to track all active client connections
- Client identifier tracking per telegram source
- Broadcast mechanism that excludes originating client socket