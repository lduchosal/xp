"""Pydantic models for Datapoint API endpoints."""

from typing import Optional

from pydantic import BaseModel, Field


class CustomResponse(BaseModel):
    """Response model for successful Datapoint operation."""

    success: bool = Field(default=True, description="Operation success status")
    result: Optional[str] = Field(default=str, description="Datapoint result string")
    description: Optional[str]  = Field(default=str, description="Datapoint description")


class CustomErrorResponse(BaseModel):
    """Response model for failed Datapoint operation."""

    success: bool = Field(default=False, description="Operation success status")
    error: str = Field(..., description="Error message")
