"""Pydantic models for discovery API endpoints."""

from typing import List
from pydantic import BaseModel, Field

class DiscoveryRequest(BaseModel):
    """Request model for discovery endpoint."""
    pass  # Empty body as per specification

class DiscoveryResponse(BaseModel):
    """Response model for successful discovery operation."""

    success: bool = Field(default=True, description="Operation success status")
    devices: List[str] = Field(default_factory=list, description="Parsed device information")

class DiscoveryErrorResponse(BaseModel):
    """Response model for failed discovery operation."""

    success: bool = Field(default=False, description="Operation success status")
    error: str = Field(..., description="Error message")
