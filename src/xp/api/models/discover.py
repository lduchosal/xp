"""Pydantic models for discover API endpoints."""

from typing import List

from pydantic import BaseModel, Field


class DiscoverResponse(BaseModel):
    """Response model for successful discover operation.

    Attributes:
        success: Operation success status.
        devices: List of discovered device information strings.
    """

    success: bool = Field(default=True, description="Operation success status")
    devices: List[str] = Field(
        default_factory=list, description="Parsed device information"
    )


class DiscoverErrorResponse(BaseModel):
    """Response model for failed discover operation.

    Attributes:
        success: Operation success status (always False).
        error: Error message describing what went wrong.
    """

    success: bool = Field(default=False, description="Operation success status")
    error: str = Field(..., description="Error message")
