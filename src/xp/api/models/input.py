"""Pydantic models for Input API endpoints."""

from typing import Optional

from pydantic import BaseModel, Field


class InputResponse(BaseModel):
    """Response model for successful Input operation."""

    success: bool = Field(default=True, description="Operation success status")
    result: Optional[str] = Field(default=str, description="Input result string")
    description: Optional[str]  = Field(default=str, description="Input description")

class InputErrorResponse(BaseModel):
    """Response model for failed Input operation."""

    success: bool = Field(default=False, description="Operation success status")
    error: str = Field(..., description="Error message")
