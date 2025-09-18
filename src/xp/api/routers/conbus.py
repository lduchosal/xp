"""FastAPI router for Conbus operations."""
from typing import Union

from fastapi import APIRouter

router = APIRouter(prefix="/api/xp/conbus", tags=["conbus"])
