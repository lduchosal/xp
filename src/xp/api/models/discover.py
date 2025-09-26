"""Pydantic models for discover API endpoints."""

from typing import List
from pydantic import BaseModel, Field


class DiscoverResponse(BaseModel):
    """Response model for successful discover operation."""

    success: bool = Field(default=True, description="Operation success status")
    devices: List[str] = Field(
        default_factory=list, description="Parsed device information"
    )


class DiscoverErrorResponse(BaseModel):
    """Response model for failed discover operation."""

    success: bool = Field(default=False, description="Operation success status")
    error: str = Field(..., description="Error message")
