"""Pydantic models for Input API endpoints."""

from typing import Optional

from pydantic import BaseModel, Field


class ApiResponse(BaseModel):
    """Response model for successful Input operation.

    Attributes:
        success: Operation success status.
        result: Result value.
        description: Description of the result.
    """

    success: bool = Field(default=True, description="Operation success status")
    result: Optional[str] = Field(default=None, description="Result")
    description: Optional[str] = Field(default=None, description="Description")


class ApiErrorResponse(BaseModel):
    """Response model for failed Input operation.

    Attributes:
        success: Operation success status (always False).
        error: Error message describing what went wrong.
    """

    success: bool = Field(default=False, description="Operation success status")
    error: str = Field(..., description="Error message")
