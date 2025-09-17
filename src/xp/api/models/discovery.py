"""Pydantic models for discovery API endpoints."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class DiscoveryRequest(BaseModel):
    """Request model for discovery endpoint."""
    pass  # Empty body as per specification


class DeviceInfo(BaseModel):
    """Information about a discovered device."""

    serial: str = Field(..., description="Device serial number")
    telegram: str = Field(..., description="Raw telegram response from device")


class DiscoveryRequestInfo(BaseModel):
    """Information about the discovery request."""

    telegram_type: str = Field(default="DISCOVERY", description="Type of telegram sent")
    target_serial: Optional[str] = Field(default=None, description="Target serial (null for broadcast)")


class DiscoveryResponse(BaseModel):
    """Response model for successful discovery operation."""

    success: bool = Field(default=True, description="Operation success status")
    request: DiscoveryRequestInfo = Field(..., description="Request information")
    sent_telegram: str = Field(..., description="Telegram sent to initiate discovery")
    received_telegrams: List[str] = Field(default_factory=list, description="All received telegram responses")
    discovered_devices: List[DeviceInfo] = Field(default_factory=list, description="Parsed device information")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="Response timestamp")


class DiscoveryErrorResponse(BaseModel):
    """Response model for failed discovery operation."""

    success: bool = Field(default=False, description="Operation success status")
    error: str = Field(..., description="Error message")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="Response timestamp")