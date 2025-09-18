"""Pydantic models for Datapoint API endpoints."""

from typing import List
from pydantic import BaseModel, Field

from xp.models import DatapointTypeName

class DatapointResponse(BaseModel):
    """Response model for successful Datapoint operation."""

    success: bool = Field(default=True, description="Operation success status")
    result: str = Field(default=str, description="Parsed device information")

class DatapointErrorResponse(BaseModel):
    """Response model for failed Datapoint operation."""

    success: bool = Field(default=False, description="Operation success status")
    error: str = Field(..., description="Error message")
